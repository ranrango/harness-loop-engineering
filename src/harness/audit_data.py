"""Dataset auditing for VisDrone-style YOLO training data."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from src.harness.config import ExperimentConfig, load_experiment_config

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}


@dataclass
class SplitAudit:
    split: str
    path: str
    ok: bool
    image_count: int
    label_count: int
    missing_dirs: list[str]
    missing_labels: list[str]
    empty_labels: list[str]
    invalid_labels: list[dict[str, Any]]
    class_distribution: dict[int, int]


@dataclass
class DatasetAudit:
    data_root: str
    ok: bool
    splits: list[SplitAudit]
    error_count: int
    warning_count: int


def audit_dataset(
    config: ExperimentConfig,
    data_root: str | Path | None = None,
    splits: list[str] | None = None,
) -> DatasetAudit:
    root = Path(data_root) if data_root is not None else config.data.root
    selected_splits = splits or config.data.splits
    split_audits = [
        _audit_split(root, split, config.data.image_ext, config.data.require_labels)
        for split in selected_splits
    ]
    error_count = sum(
        len(item.missing_dirs) + len(item.missing_labels) + len(item.invalid_labels)
        for item in split_audits
    )
    warning_count = sum(len(item.empty_labels) for item in split_audits)
    return DatasetAudit(
        data_root=str(root),
        ok=error_count == 0,
        splits=split_audits,
        error_count=error_count,
        warning_count=warning_count,
    )


def audit_to_dict(audit: DatasetAudit) -> dict[str, Any]:
    return asdict(audit)


def render_audit_markdown(audit: DatasetAudit) -> str:
    lines = [
        "# Data Audit",
        "",
        f"- Data root: `{audit.data_root}`",
        f"- Status: {'PASS' if audit.ok else 'FAIL'}",
        f"- Errors: {audit.error_count}",
        f"- Warnings: {audit.warning_count}",
        "",
        "| split | status | images | labels | missing labels | empty labels | invalid rows |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for split in audit.splits:
        lines.append(
            f"| {split.split} | {'PASS' if split.ok else 'FAIL'} | {split.image_count} | "
            f"{split.label_count} | {len(split.missing_labels)} | {len(split.empty_labels)} | "
            f"{len(split.invalid_labels)} |"
        )
    lines.append("")
    for split in audit.splits:
        lines.append(f"## {split.split}")
        if split.missing_dirs:
            lines.append(f"- Missing dirs: {', '.join(split.missing_dirs)}")
        if split.missing_labels:
            lines.append(f"- Missing labels: {', '.join(split.missing_labels[:20])}")
        if split.empty_labels:
            lines.append(f"- Empty labels: {', '.join(split.empty_labels[:20])}")
        if split.invalid_labels:
            lines.append("- Invalid labels:")
            for issue in split.invalid_labels[:20]:
                lines.append(f"  - `{issue['file']}` line {issue['line']}: {issue['message']}")
        if split.class_distribution:
            distribution = ", ".join(
                f"{cls}:{count}" for cls, count in sorted(split.class_distribution.items())
            )
            lines.append(f"- Class distribution: {distribution}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _audit_split(root: Path, split: str, image_ext: str, require_labels: bool) -> SplitAudit:
    split_dir = root / f"VisDrone2019-DET-{split}"
    image_dir = split_dir / "images"
    label_dir = split_dir / "labels"
    missing_dirs: list[str] = []
    if not image_dir.is_dir():
        missing_dirs.append(str(image_dir))
    if require_labels and not label_dir.is_dir():
        missing_dirs.append(str(label_dir))

    images = _collect_images(image_dir, image_ext) if image_dir.is_dir() else []
    labels = sorted(label_dir.glob("*.txt")) if label_dir.is_dir() else []
    missing_labels: list[str] = []
    empty_labels: list[str] = []
    invalid_labels: list[dict[str, Any]] = []
    class_distribution: dict[int, int] = {}

    if require_labels and label_dir.is_dir():
        label_names = {path.name for path in labels}
        for image_path in images:
            expected = image_path.with_suffix(".txt").name
            if expected not in label_names:
                missing_labels.append(expected)

        for label_path in labels:
            text = label_path.read_text(encoding="utf-8").strip()
            if not text:
                empty_labels.append(label_path.name)
                continue
            for line_no, line in enumerate(text.splitlines(), 1):
                issue = _validate_yolo_row(label_path.name, line_no, line)
                if issue is not None:
                    invalid_labels.append(issue)
                    continue
                cls_id = int(line.split()[0])
                class_distribution[cls_id] = class_distribution.get(cls_id, 0) + 1

    ok = not missing_dirs and not missing_labels and not invalid_labels
    return SplitAudit(
        split=split,
        path=str(split_dir),
        ok=ok,
        image_count=len(images),
        label_count=len(labels),
        missing_dirs=missing_dirs,
        missing_labels=missing_labels,
        empty_labels=empty_labels,
        invalid_labels=invalid_labels,
        class_distribution=class_distribution,
    )


def _collect_images(image_dir: Path, image_ext: str) -> list[Path]:
    ext = "." + image_ext.lower().lstrip(".")
    if ext in IMAGE_EXTENSIONS:
        return sorted(path for path in image_dir.iterdir() if path.suffix.lower() == ext)
    return sorted(path for path in image_dir.iterdir() if path.suffix.lower() in IMAGE_EXTENSIONS)


def _validate_yolo_row(file_name: str, line_no: int, line: str) -> dict[str, Any] | None:
    parts = line.split()
    if len(parts) != 5:
        return _issue(file_name, line_no, "expected 5 columns")
    try:
        cls_id = int(parts[0])
        values = [float(part) for part in parts[1:]]
    except ValueError:
        return _issue(file_name, line_no, "non-numeric value")
    if cls_id < 0 or cls_id > 9:
        return _issue(file_name, line_no, "class id outside 0-9")
    xc, yc, width, height = values
    if not all(0.0 <= value <= 1.0 for value in (xc, yc, width, height)):
        return _issue(file_name, line_no, "normalized value outside 0-1")
    if width <= 0.0 or height <= 0.0:
        return _issue(file_name, line_no, "width and height must be positive")
    return None


def _issue(file_name: str, line_no: int, message: str) -> dict[str, Any]:
    return {"file": file_name, "line": line_no, "message": message}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit VisDrone-style YOLO dataset folders.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--config", default="configs/experiments/baseline_yolov8n.yaml")
    parser.add_argument("--data-root", default=None)
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_experiment_config(args.config)
    audit = audit_dataset(config, data_root=args.data_root)
    if args.format == "json":
        text = json.dumps(audit_to_dict(audit), ensure_ascii=False, indent=2)
    else:
        text = render_audit_markdown(audit)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    raise SystemExit(0 if audit.ok else 1)


if __name__ == "__main__":
    main()
