"""Self-contained Harness/Loop demo generation."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml

from src.harness.audit_data import audit_dataset, audit_to_dict
from src.harness.config import load_experiment_config
from src.harness.metrics import check_metric_gates
from src.harness.report import (
    LoopReportInput,
    load_commands_file,
    render_loop_report,
    resolve_report_paths,
)


@dataclass(frozen=True)
class DemoLoopResult:
    run_dir: Path
    report_path: Path


DEMO_METRICS = {
    "precision": 0.39,
    "recall": 0.31,
    "map50": 0.29,
    "map": 0.16,
}


def create_demo_loop(
    output_root: str | Path = "runs/harness-demo",
    timestamp: str | None = None,
) -> DemoLoopResult:
    stamp = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(output_root) / "harness_loop_demo" / stamp
    run_dir.mkdir(parents=True, exist_ok=False)

    data_root = run_dir / "demo_data"
    _write_demo_dataset(data_root)
    _write_demo_dataset_yaml(run_dir / "data.yaml", data_root)
    config_path = run_dir / "resolved_config.yaml"
    _write_demo_config(config_path, data_root, run_dir / "data.yaml")

    config = load_experiment_config(config_path)
    audit = audit_dataset(config)
    (run_dir / "audit.json").write_text(
        json.dumps(audit_to_dict(audit), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (run_dir / "metrics.json").write_text(
        json.dumps(DEMO_METRICS, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _write_commands_file(run_dir)

    artifacts = [
        str(run_dir / artifact_name)
        for artifact_name in (
            "resolved_config.yaml",
            "demo_data",
            "audit.json",
            "metrics.json",
            "commands.txt",
            "loop_report.md",
        )
    ]
    paths = resolve_report_paths(run_dir=run_dir, artifacts=artifacts)
    gate_report = check_metric_gates(config, DEMO_METRICS)
    report = render_loop_report(
        LoopReportInput(
            experiment_name=config.experiment.name,
            timestamp=paths.timestamp,
            audit=audit,
            metrics=DEMO_METRICS,
            gate_report=gate_report,
            commands=load_commands_file(paths.commands_file),
            artifacts=paths.artifacts,
        )
    )
    paths.output.write_text(report, encoding="utf-8")
    return DemoLoopResult(run_dir=run_dir, report_path=paths.output)


def _write_demo_dataset(root: Path) -> None:
    for split in ("train", "val"):
        image_dir = root / f"VisDrone2019-DET-{split}" / "images"
        label_dir = root / f"VisDrone2019-DET-{split}" / "labels"
        image_dir.mkdir(parents=True)
        label_dir.mkdir(parents=True)
        (image_dir / f"demo_{split}.jpg").write_bytes(b"\xff\xd8\xff\xd9")
        (label_dir / f"demo_{split}.txt").write_text(
            "3 0.5000 0.5000 0.2500 0.2000\n",
            encoding="utf-8",
        )


def _write_demo_dataset_yaml(path: Path, data_root: Path) -> None:
    raw = {
        "path": str(data_root),
        "train": "VisDrone2019-DET-train/images",
        "val": "VisDrone2019-DET-val/images",
        "names": {3: "car"},
    }
    path.write_text(yaml.safe_dump(raw, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _write_demo_config(path: Path, data_root: Path, dataset_yaml: Path) -> None:
    raw = {
        "experiment": {
            "name": "harness_loop_demo",
            "description": "Self-contained demo loop with synthetic audit and metrics artifacts",
        },
        "data": {
            "root": str(data_root),
            "dataset_yaml": str(dataset_yaml),
            "splits": ["train", "val"],
            "image_ext": "jpg",
            "require_labels": True,
        },
        "model": {"weights": "demo-no-training.pt"},
        "train": {
            "enabled": False,
            "epochs": 0,
            "batch": 1,
            "imgsz": 64,
            "device": "cpu",
            "workers": 0,
            "patience": 0,
        },
        "val": {
            "enabled": False,
            "batch": 1,
            "imgsz": 64,
            "device": "cpu",
            "conf": 0.001,
            "iou": 0.6,
        },
        "gates": {
            "map50_min": 0.258,
            "map_min": 0.147,
            "precision_min": 0.354,
            "recall_min": 0.274,
            "allowed_drop": 0.02,
        },
        "outputs": {"root": str(path.parent)},
    }
    path.write_text(yaml.safe_dump(raw, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _write_commands_file(run_dir: Path) -> None:
    commands = [
        "drone-audit-data --config resolved_config.yaml --format json --output audit.json",
        "drone-check-metrics --config resolved_config.yaml --metrics metrics.json",
        "drone-loop-report --config resolved_config.yaml --run-dir .",
    ]
    (run_dir / "commands.txt").write_text("\n".join(commands) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a self-contained Harness/Loop demo run.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--output-root", default="runs/harness-demo")
    parser.add_argument("--timestamp", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = create_demo_loop(output_root=args.output_root, timestamp=args.timestamp)
    print(f"Demo harness loop directory: {result.run_dir}")
    print(f"Demo loop report: {result.report_path}")


if __name__ == "__main__":
    main()
