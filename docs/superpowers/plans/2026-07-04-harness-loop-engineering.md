# Harness Loop Engineering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a configuration-driven experiment harness and improvement loop for the YOLOv8 VisDrone project without requiring real data, weights, GPU, or network access in CI.

**Architecture:** Add a focused `src/harness/` package with separate modules for config parsing, data auditing, metric gates, report rendering, and run orchestration. Keep existing `drone-convert`, `drone-train`, `drone-val`, and `drone-detect` intact; the harness wraps them instead of replacing them.

**Tech Stack:** Python 3.9+, dataclasses, argparse, pathlib, json, subprocess, PyYAML, pytest, existing Makefile and setuptools console scripts.

**Chinese companion:** `docs/superpowers/plans/2026-07-04-harness-loop-engineering.zh.md`

**Documentation language convention:** User-facing project documents created after this plan should be Chinese-first. Add an English companion only when explicitly useful for publication or external review.

---

## File Map

- Create `configs/experiments/baseline_yolov8n.yaml`: baseline experiment contract.
- Create `src/harness/__init__.py`: harness package metadata.
- Create `src/harness/config.py`: typed config loader and validation errors.
- Create `src/harness/audit_data.py`: dataset audit logic, JSON/Markdown renderers, CLI.
- Create `src/harness/metrics.py`: metric gate logic, JSON loading, CLI.
- Create `src/harness/report.py`: loop report rendering and rule-based suggestions, CLI.
- Create `src/harness/runner.py`: dry-run and real runner orchestration, CLI.
- Create `tests/test_harness_config.py`: config parser tests.
- Create `tests/test_harness_audit.py`: synthetic dataset audit tests.
- Create `tests/test_harness_metrics.py`: metric gate tests.
- Create `tests/test_harness_report.py`: report rendering tests.
- Create `tests/test_harness_runner.py`: dry-run runner tests.
- Modify `pyproject.toml`: add `PyYAML>=6.0` and four console scripts.
- Modify `Makefile`: add harness convenience targets.
- Modify `README.md`: add short harness loop section.
- Create `docs/harness_loop.md`: user-facing Chinese guide.

## Task 1: Experiment Config And Loader

**Files:**
- Create: `configs/experiments/baseline_yolov8n.yaml`
- Create: `src/harness/__init__.py`
- Create: `src/harness/config.py`
- Create: `tests/test_harness_config.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Write config loader tests**

Create `tests/test_harness_config.py`:

```python
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from src.harness.config import ConfigError, load_experiment_config


def write_config(path: Path, content: str) -> Path:
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


def test_loads_baseline_config():
    config = load_experiment_config("configs/experiments/baseline_yolov8n.yaml")

    assert config.experiment.name == "baseline_yolov8n"
    assert config.data.root == Path("data")
    assert config.data.splits == ["train", "val"]
    assert config.model.weights == "yolov8n.pt"
    assert config.train.epochs == 10
    assert config.val.conf == 0.001
    assert config.gates.map50_min == pytest.approx(0.258)
    assert config.outputs.root == Path("runs/harness")


def test_rejects_missing_required_section(tmp_path):
    path = write_config(
        tmp_path / "bad.yaml",
        """
        experiment:
          name: missing_data
        model:
          weights: yolov8n.pt
        """,
    )

    with pytest.raises(ConfigError, match="data"):
        load_experiment_config(path)


def test_rejects_wrong_field_type(tmp_path):
    path = write_config(
        tmp_path / "bad.yaml",
        """
        experiment:
          name: bad_type
          description: bad
        data:
          root: data
          dataset_yaml: data.yaml
          splits: train
          image_ext: jpg
          require_labels: true
        model:
          weights: yolov8n.pt
        train:
          enabled: true
          epochs: 10
          batch: 8
          imgsz: 640
          device: cpu
          workers: 4
          patience: 50
        val:
          enabled: true
          batch: 8
          imgsz: 640
          device: cpu
          conf: 0.001
          iou: 0.6
        gates:
          map50_min: 0.258
          map_min: 0.147
          precision_min: 0.354
          recall_min: 0.274
          allowed_drop: 0.02
        outputs:
          root: runs/harness
        """,
    )

    with pytest.raises(ConfigError, match="data.splits"):
        load_experiment_config(path)
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
python3 -m pytest tests/test_harness_config.py -q
```

Expected: FAIL because `src.harness.config` and baseline config do not exist yet.

- [ ] **Step 3: Add baseline experiment YAML**

Create `configs/experiments/baseline_yolov8n.yaml`:

```yaml
experiment:
  name: baseline_yolov8n
  description: YOLOv8n VisDrone baseline loop

data:
  root: data
  dataset_yaml: data.yaml
  splits: [train, val]
  image_ext: jpg
  require_labels: true

model:
  weights: yolov8n.pt

train:
  enabled: true
  epochs: 10
  batch: 8
  imgsz: 640
  device: cpu
  workers: 4
  patience: 50

val:
  enabled: true
  batch: 8
  imgsz: 640
  device: cpu
  conf: 0.001
  iou: 0.6

gates:
  map50_min: 0.258
  map_min: 0.147
  precision_min: 0.354
  recall_min: 0.274
  allowed_drop: 0.02

outputs:
  root: runs/harness
```

- [ ] **Step 4: Add harness package init**

Create `src/harness/__init__.py`:

```python
"""Experiment harness and iteration loop utilities for drone object detection."""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "0.1.0"
```

- [ ] **Step 5: Add typed config loader**

Create `src/harness/config.py`:

```python
"""Experiment configuration loading and validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """Raised when an experiment config is missing required fields or has invalid types."""


@dataclass(frozen=True)
class ExperimentSection:
    name: str
    description: str = ""


@dataclass(frozen=True)
class DataSection:
    root: Path
    dataset_yaml: Path
    splits: list[str]
    image_ext: str
    require_labels: bool


@dataclass(frozen=True)
class ModelSection:
    weights: str


@dataclass(frozen=True)
class TrainSection:
    enabled: bool
    epochs: int
    batch: int
    imgsz: int
    device: str
    workers: int
    patience: int


@dataclass(frozen=True)
class ValSection:
    enabled: bool
    batch: int
    imgsz: int
    device: str
    conf: float
    iou: float


@dataclass(frozen=True)
class GatesSection:
    map50_min: float
    map_min: float
    precision_min: float
    recall_min: float
    allowed_drop: float

    def thresholds(self) -> dict[str, float]:
        return {
            "precision": self.precision_min,
            "recall": self.recall_min,
            "map50": self.map50_min,
            "map": self.map_min,
        }


@dataclass(frozen=True)
class OutputsSection:
    root: Path


@dataclass(frozen=True)
class ExperimentConfig:
    path: Path
    experiment: ExperimentSection
    data: DataSection
    model: ModelSection
    train: TrainSection
    val: ValSection
    gates: GatesSection
    outputs: OutputsSection


def load_experiment_config(path: str | Path) -> ExperimentConfig:
    config_path = Path(path)
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(f"无法读取实验配置：{config_path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"YAML 解析失败：{config_path}") from exc

    root = _mapping(raw, "config")
    experiment = _mapping(root.get("experiment"), "experiment")
    data = _mapping(root.get("data"), "data")
    model = _mapping(root.get("model"), "model")
    train = _mapping(root.get("train"), "train")
    val = _mapping(root.get("val"), "val")
    gates = _mapping(root.get("gates"), "gates")
    outputs = _mapping(root.get("outputs"), "outputs")

    return ExperimentConfig(
        path=config_path,
        experiment=ExperimentSection(
            name=_string(experiment.get("name"), "experiment.name"),
            description=_optional_string(experiment.get("description"), "experiment.description"),
        ),
        data=DataSection(
            root=Path(_string(data.get("root"), "data.root")),
            dataset_yaml=Path(_string(data.get("dataset_yaml"), "data.dataset_yaml")),
            splits=_string_list(data.get("splits"), "data.splits"),
            image_ext=_string(data.get("image_ext"), "data.image_ext").lstrip("."),
            require_labels=_bool(data.get("require_labels"), "data.require_labels"),
        ),
        model=ModelSection(weights=_string(model.get("weights"), "model.weights")),
        train=TrainSection(
            enabled=_bool(train.get("enabled"), "train.enabled"),
            epochs=_int(train.get("epochs"), "train.epochs"),
            batch=_int(train.get("batch"), "train.batch"),
            imgsz=_int(train.get("imgsz"), "train.imgsz"),
            device=_string(train.get("device"), "train.device"),
            workers=_int(train.get("workers"), "train.workers"),
            patience=_int(train.get("patience"), "train.patience"),
        ),
        val=ValSection(
            enabled=_bool(val.get("enabled"), "val.enabled"),
            batch=_int(val.get("batch"), "val.batch"),
            imgsz=_int(val.get("imgsz"), "val.imgsz"),
            device=_string(val.get("device"), "val.device"),
            conf=_float(val.get("conf"), "val.conf"),
            iou=_float(val.get("iou"), "val.iou"),
        ),
        gates=GatesSection(
            map50_min=_float(gates.get("map50_min"), "gates.map50_min"),
            map_min=_float(gates.get("map_min"), "gates.map_min"),
            precision_min=_float(gates.get("precision_min"), "gates.precision_min"),
            recall_min=_float(gates.get("recall_min"), "gates.recall_min"),
            allowed_drop=_float(gates.get("allowed_drop"), "gates.allowed_drop"),
        ),
        outputs=OutputsSection(root=Path(_string(outputs.get("root"), "outputs.root"))),
    )


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"{field} 必须是 mapping")
    return value


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{field} 必须是非空字符串")
    return value


def _optional_string(value: Any, field: str) -> str:
    if value is None:
        return ""
    return _string(value, field)


def _string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ConfigError(f"{field} 必须是非空字符串列表")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise ConfigError(f"{field} 必须只包含非空字符串")
    return list(value)


def _bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise ConfigError(f"{field} 必须是布尔值")
    return value


def _int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"{field} 必须是整数")
    return value


def _float(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"{field} 必须是数字")
    return float(value)
```

- [ ] **Step 6: Add PyYAML dependency**

Modify `pyproject.toml` dependencies:

```toml
dependencies = [
    "ultralytics>=8.2.0",
    "opencv-python>=4.8.0",
    "numpy>=1.24.0",
    "matplotlib>=3.7.0",
    "torch>=2.0.0",
    "torchvision>=0.15.0",
    "PyYAML>=6.0",
]
```

- [ ] **Step 7: Run config tests**

Run:

```bash
python3 -m pytest tests/test_harness_config.py -q
```

Expected: PASS with 3 tests.

- [ ] **Step 8: Commit config task**

Run:

```bash
git add configs/experiments/baseline_yolov8n.yaml src/harness/__init__.py src/harness/config.py tests/test_harness_config.py pyproject.toml
git commit -m "feat: add harness experiment config"
```

## Task 2: Data Audit

**Files:**
- Create: `src/harness/audit_data.py`
- Create: `tests/test_harness_audit.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Write data audit tests**

Create `tests/test_harness_audit.py`:

```python
from __future__ import annotations

from pathlib import Path

from src.harness.audit_data import audit_dataset, render_audit_markdown
from src.harness.config import load_experiment_config
from tests.image_helpers import make_jpeg


def make_split(root: Path, split: str) -> tuple[Path, Path]:
    img_dir = root / f"VisDrone2019-DET-{split}" / "images"
    label_dir = root / f"VisDrone2019-DET-{split}" / "labels"
    img_dir.mkdir(parents=True)
    label_dir.mkdir(parents=True)
    return img_dir, label_dir


def test_audit_valid_synthetic_dataset(tmp_path):
    img_dir, label_dir = make_split(tmp_path, "train")
    (img_dir / "img1.jpg").write_bytes(make_jpeg(32, 24))
    (label_dir / "img1.txt").write_text("3 0.5 0.5 0.2 0.3\n", encoding="utf-8")

    config = load_experiment_config("configs/experiments/baseline_yolov8n.yaml")
    audit = audit_dataset(config, data_root=tmp_path, splits=["train"])

    assert audit.ok is True
    assert audit.splits[0].image_count == 1
    assert audit.splits[0].label_count == 1
    assert audit.splits[0].class_distribution == {3: 1}
    assert audit.error_count == 0


def test_audit_reports_missing_label(tmp_path):
    img_dir, _label_dir = make_split(tmp_path, "train")
    (img_dir / "orphan.jpg").write_bytes(make_jpeg(32, 24))

    config = load_experiment_config("configs/experiments/baseline_yolov8n.yaml")
    audit = audit_dataset(config, data_root=tmp_path, splits=["train"])

    assert audit.ok is False
    assert audit.splits[0].missing_labels == ["orphan.txt"]
    assert audit.error_count == 1


def test_audit_reports_invalid_yolo_row(tmp_path):
    img_dir, label_dir = make_split(tmp_path, "train")
    (img_dir / "bad.jpg").write_bytes(make_jpeg(32, 24))
    (label_dir / "bad.txt").write_text("12 1.2 0.5 0.0 0.3\n", encoding="utf-8")

    config = load_experiment_config("configs/experiments/baseline_yolov8n.yaml")
    audit = audit_dataset(config, data_root=tmp_path, splits=["train"])

    assert audit.ok is False
    assert len(audit.splits[0].invalid_labels) == 1
    assert "class id" in audit.splits[0].invalid_labels[0]["message"]


def test_markdown_summary_contains_split_status(tmp_path):
    img_dir, label_dir = make_split(tmp_path, "train")
    (img_dir / "img1.jpg").write_bytes(make_jpeg(32, 24))
    (label_dir / "img1.txt").write_text("3 0.5 0.5 0.2 0.3\n", encoding="utf-8")

    config = load_experiment_config("configs/experiments/baseline_yolov8n.yaml")
    audit = audit_dataset(config, data_root=tmp_path, splits=["train"])
    markdown = render_audit_markdown(audit)

    assert "# Data Audit" in markdown
    assert "train" in markdown
    assert "PASS" in markdown
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
python3 -m pytest tests/test_harness_audit.py -q
```

Expected: FAIL because `src.harness.audit_data` does not exist.

- [ ] **Step 3: Implement data audit module and CLI**

Create `src/harness/audit_data.py`:

```python
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
    split_audits = [_audit_split(root, split, config.data.image_ext, config.data.require_labels) for split in selected_splits]
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
            distribution = ", ".join(f"{cls}:{count}" for cls, count in sorted(split.class_distribution.items()))
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
    text = json.dumps(audit_to_dict(audit), ensure_ascii=False, indent=2) if args.format == "json" else render_audit_markdown(audit)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    raise SystemExit(0 if audit.ok else 1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Add audit CLI script entry**

Modify `[project.scripts]` in `pyproject.toml`:

```toml
[project.scripts]
drone-detect  = "src.detect:main"
drone-train   = "src.train:main"
drone-val     = "src.val:main"
drone-convert = "scripts.convert_visdrone_to_yolo:main"
drone-audit-data = "src.harness.audit_data:main"
```

- [ ] **Step 5: Run audit tests**

Run:

```bash
python3 -m pytest tests/test_harness_audit.py -q
```

Expected: PASS with 4 tests.

- [ ] **Step 6: Commit data audit task**

Run:

```bash
git add src/harness/audit_data.py tests/test_harness_audit.py pyproject.toml
git commit -m "feat: add dataset audit harness"
```

## Task 3: Metric Gates

**Files:**
- Create: `src/harness/metrics.py`
- Create: `tests/test_harness_metrics.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Write metric gate tests**

Create `tests/test_harness_metrics.py`:

```python
from __future__ import annotations

import json

from src.harness.config import load_experiment_config
from src.harness.metrics import check_metric_gates, load_metrics, render_gate_table


def test_metric_gates_pass_with_baseline_values():
    config = load_experiment_config("configs/experiments/baseline_yolov8n.yaml")
    report = check_metric_gates(
        config,
        {"precision": 0.354, "recall": 0.274, "map50": 0.258, "map": 0.147},
    )

    assert report.ok is True
    assert all(result.passed for result in report.results)


def test_metric_gates_allow_configured_drop():
    config = load_experiment_config("configs/experiments/baseline_yolov8n.yaml")
    report = check_metric_gates(
        config,
        {"precision": 0.334, "recall": 0.254, "map50": 0.238, "map": 0.127},
    )

    assert report.ok is True


def test_metric_gates_fail_below_allowed_drop():
    config = load_experiment_config("configs/experiments/baseline_yolov8n.yaml")
    report = check_metric_gates(
        config,
        {"precision": 0.20, "recall": 0.274, "map50": 0.258, "map": 0.147},
    )

    assert report.ok is False
    failed = [result for result in report.results if not result.passed]
    assert failed[0].name == "precision"


def test_load_metrics_from_json(tmp_path):
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(
        json.dumps({"precision": 0.4, "recall": 0.3, "map50": 0.27, "map": 0.15}),
        encoding="utf-8",
    )

    metrics = load_metrics(metrics_path)

    assert metrics["map50"] == 0.27


def test_render_gate_table_contains_failure_status():
    config = load_experiment_config("configs/experiments/baseline_yolov8n.yaml")
    report = check_metric_gates(
        config,
        {"precision": 0.20, "recall": 0.274, "map50": 0.258, "map": 0.147},
    )
    table = render_gate_table(report)

    assert "precision" in table
    assert "FAIL" in table
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
python3 -m pytest tests/test_harness_metrics.py -q
```

Expected: FAIL because `src.harness.metrics` does not exist.

- [ ] **Step 3: Implement metric gate module and CLI**

Create `src/harness/metrics.py`:

```python
"""Metric gate checking for experiment loops."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from src.harness.config import ExperimentConfig, load_experiment_config


@dataclass(frozen=True)
class MetricGateResult:
    name: str
    observed: float
    minimum: float
    allowed_drop: float
    required: float
    delta: float
    passed: bool


@dataclass(frozen=True)
class MetricGateReport:
    ok: bool
    results: list[MetricGateResult]


def load_metrics(path: str | Path) -> dict[str, float]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("metrics JSON must be an object")
    metrics: dict[str, float] = {}
    for key in ("precision", "recall", "map50", "map"):
        if key in raw:
            value = raw[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{key} must be numeric")
            metrics[key] = float(value)
    return metrics


def check_metric_gates(config: ExperimentConfig, metrics: dict[str, float]) -> MetricGateReport:
    results: list[MetricGateResult] = []
    for name, minimum in config.gates.thresholds().items():
        if name not in metrics:
            raise ValueError(f"missing metric: {name}")
        observed = float(metrics[name])
        required = minimum - config.gates.allowed_drop
        delta = observed - required
        results.append(
            MetricGateResult(
                name=name,
                observed=observed,
                minimum=minimum,
                allowed_drop=config.gates.allowed_drop,
                required=required,
                delta=delta,
                passed=observed >= required,
            )
        )
    return MetricGateReport(ok=all(result.passed for result in results), results=results)


def gate_report_to_dict(report: MetricGateReport) -> dict[str, Any]:
    return asdict(report)


def render_gate_table(report: MetricGateReport) -> str:
    lines = [
        "| metric | observed | minimum | allowed_drop | required | delta | status |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for result in report.results:
        lines.append(
            f"| {result.name} | {result.observed:.4f} | {result.minimum:.4f} | "
            f"{result.allowed_drop:.4f} | {result.required:.4f} | {result.delta:.4f} | "
            f"{'PASS' if result.passed else 'FAIL'} |"
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check validation metrics against experiment gates.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--config", default="configs/experiments/baseline_yolov8n.yaml")
    parser.add_argument("--metrics", default=None)
    parser.add_argument("--map50", type=float, default=None)
    parser.add_argument("--map", type=float, default=None)
    parser.add_argument("--precision", type=float, default=None)
    parser.add_argument("--recall", type=float, default=None)
    parser.add_argument("--json", action="store_true", help="Print machine-readable gate report.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_experiment_config(args.config)
    metrics = load_metrics(args.metrics) if args.metrics else {}
    direct = {
        "precision": args.precision,
        "recall": args.recall,
        "map50": args.map50,
        "map": args.map,
    }
    metrics.update({key: value for key, value in direct.items() if value is not None})
    report = check_metric_gates(config, metrics)
    if args.json:
        print(json.dumps(gate_report_to_dict(report), ensure_ascii=False, indent=2))
    else:
        print(render_gate_table(report))
    raise SystemExit(0 if report.ok else 1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Add metric CLI script entry**

Modify `[project.scripts]` in `pyproject.toml`:

```toml
drone-check-metrics = "src.harness.metrics:main"
```

- [ ] **Step 5: Run metric tests**

Run:

```bash
python3 -m pytest tests/test_harness_metrics.py -q
```

Expected: PASS with 5 tests.

- [ ] **Step 6: Commit metric gate task**

Run:

```bash
git add src/harness/metrics.py tests/test_harness_metrics.py pyproject.toml
git commit -m "feat: add metric gate checks"
```

## Task 4: Loop Report

**Files:**
- Create: `src/harness/report.py`
- Create: `tests/test_harness_report.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Write report tests**

Create `tests/test_harness_report.py`:

```python
from __future__ import annotations

from src.harness.audit_data import DatasetAudit, SplitAudit
from src.harness.config import load_experiment_config
from src.harness.metrics import check_metric_gates
from src.harness.report import LoopReportInput, render_loop_report, suggest_next_experiments


def sample_audit(ok: bool = True) -> DatasetAudit:
    return DatasetAudit(
        data_root="data",
        ok=ok,
        error_count=0 if ok else 1,
        warning_count=0,
        splits=[
            SplitAudit(
                split="train",
                path="data/VisDrone2019-DET-train",
                ok=ok,
                image_count=2,
                label_count=2,
                missing_dirs=[],
                missing_labels=[] if ok else ["img2.txt"],
                empty_labels=[],
                invalid_labels=[],
                class_distribution={3: 2},
            )
        ],
    )


def test_suggestions_for_low_recall():
    suggestions = suggest_next_experiments(
        metrics={"precision": 0.4, "recall": 0.1, "map50": 0.25, "map": 0.14},
        audit_ok=True,
    )

    assert any("召回率" in item for item in suggestions)


def test_suggestions_prioritize_data_quality_when_audit_fails():
    suggestions = suggest_next_experiments(
        metrics={"precision": 0.4, "recall": 0.3, "map50": 0.27, "map": 0.15},
        audit_ok=False,
    )

    assert suggestions[0].startswith("先修复数据质量")


def test_render_loop_report_contains_required_sections():
    config = load_experiment_config("configs/experiments/baseline_yolov8n.yaml")
    metrics = {"precision": 0.354, "recall": 0.274, "map50": 0.258, "map": 0.147}
    gate_report = check_metric_gates(config, metrics)
    report = render_loop_report(
        LoopReportInput(
            experiment_name=config.experiment.name,
            timestamp="20260704_120000",
            audit=sample_audit(),
            metrics=metrics,
            gate_report=gate_report,
            commands=["python3 -m src.train --epochs 10"],
            artifacts=["runs/harness/baseline_yolov8n/20260704_120000"],
        )
    )

    assert "# Harness Loop Report" in report
    assert "## Data Audit" in report
    assert "## Metric Gates" in report
    assert "## Next Experiments" in report
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
python3 -m pytest tests/test_harness_report.py -q
```

Expected: FAIL because `src.harness.report` does not exist.

- [ ] **Step 3: Implement report module and CLI**

Create `src/harness/report.py`:

```python
"""Loop report rendering and rule-based next experiment suggestions."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from src.harness.audit_data import DatasetAudit, SplitAudit, render_audit_markdown
from src.harness.config import load_experiment_config
from src.harness.metrics import MetricGateReport, check_metric_gates, load_metrics, render_gate_table


@dataclass(frozen=True)
class LoopReportInput:
    experiment_name: str
    timestamp: str
    audit: DatasetAudit
    metrics: dict[str, float]
    gate_report: MetricGateReport
    commands: list[str]
    artifacts: list[str]


def suggest_next_experiments(metrics: dict[str, float], audit_ok: bool) -> list[str]:
    if not audit_ok:
        return ["先修复数据质量：补齐缺失标签、清理无效 YOLO 行，然后再训练。"]
    suggestions: list[str] = []
    if metrics.get("recall", 1.0) < 0.28:
        suggestions.append("召回率偏低：尝试降低置信度阈值、增加 epoch、增大 imgsz 或检查类别不平衡。")
    if metrics.get("precision", 1.0) < 0.35:
        suggestions.append("精确率偏低：抽查误检样本，并尝试提高 conf 或加强负样本覆盖。")
    if metrics.get("map50", 1.0) < 0.26 or metrics.get("map", 1.0) < 0.15:
        suggestions.append("mAP 偏低：优先复核小目标类别，尝试 imgsz=960 或更强数据增强。")
    if not suggestions:
        suggestions.append("指标达到当前门槛：可以尝试 yolov8s、更多 epoch 或验证集错误样本分析。")
    return suggestions


def render_loop_report(data: LoopReportInput) -> str:
    lines = [
        "# Harness Loop Report",
        "",
        f"- Experiment: `{data.experiment_name}`",
        f"- Timestamp: `{data.timestamp}`",
        "",
        "## Data Audit",
        "",
        render_audit_markdown(data.audit).strip(),
        "",
        "## Commands",
        "",
    ]
    if data.commands:
        lines.extend(f"- `{command}`" for command in data.commands)
    else:
        lines.append("- No commands recorded.")
    lines.extend(
        [
            "",
            "## Metrics",
            "",
            "| metric | value |",
            "| --- | ---: |",
        ]
    )
    for name in ("precision", "recall", "map50", "map"):
        if name in data.metrics:
            lines.append(f"| {name} | {data.metrics[name]:.4f} |")
    lines.extend(["", "## Metric Gates", "", render_gate_table(data.gate_report), "", "## Artifacts", ""])
    if data.artifacts:
        lines.extend(f"- `{artifact}`" for artifact in data.artifacts)
    else:
        lines.append("- No artifacts recorded.")
    lines.extend(["", "## Risks And Missing Resources", ""])
    if data.audit.ok:
        lines.append("- No blocking data quality issue detected by the audit.")
    else:
        lines.append("- Data audit failed. Fix data quality before trusting training or validation metrics.")
    if not data.gate_report.ok:
        lines.append("- One or more metrics failed configured gates.")
    lines.extend(["", "## Next Experiments", ""])
    lines.extend(f"- {item}" for item in suggest_next_experiments(data.metrics, data.audit.ok))
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a Markdown loop report from audit and metric artifacts.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--config", default="configs/experiments/baseline_yolov8n.yaml")
    parser.add_argument("--audit-json", required=True)
    parser.add_argument("--metrics", required=True)
    parser.add_argument("--timestamp", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_experiment_config(args.config)
    audit_raw = json.loads(Path(args.audit_json).read_text(encoding="utf-8"))
    audit = _audit_from_dict(audit_raw)
    metrics = load_metrics(args.metrics)
    gate_report = check_metric_gates(config, metrics)
    report = render_loop_report(
        LoopReportInput(
            experiment_name=config.experiment.name,
            timestamp=args.timestamp,
            audit=audit,
            metrics=metrics,
            gate_report=gate_report,
            commands=[],
            artifacts=[],
        )
    )
    Path(args.output).write_text(report, encoding="utf-8")


def _audit_from_dict(raw: dict) -> DatasetAudit:
    return DatasetAudit(
        data_root=raw["data_root"],
        ok=raw["ok"],
        error_count=raw["error_count"],
        warning_count=raw["warning_count"],
        splits=[SplitAudit(**split) for split in raw["splits"]],
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Add report CLI script entry**

Modify `[project.scripts]` in `pyproject.toml`:

```toml
drone-loop-report = "src.harness.report:main"
```

- [ ] **Step 5: Run report tests**

Run:

```bash
python3 -m pytest tests/test_harness_report.py -q
```

Expected: PASS with 3 tests.

- [ ] **Step 6: Commit report task**

Run:

```bash
git add src/harness/report.py tests/test_harness_report.py pyproject.toml
git commit -m "feat: add loop report generation"
```

## Task 5: Harness Runner

**Files:**
- Create: `src/harness/runner.py`
- Create: `tests/test_harness_runner.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Write runner dry-run tests**

Create `tests/test_harness_runner.py`:

```python
from __future__ import annotations

from pathlib import Path

from src.harness.config import load_experiment_config
from src.harness.runner import build_stage_commands, create_run_dir


def test_build_all_stage_commands_with_skip_train(tmp_path):
    config = load_experiment_config("configs/experiments/baseline_yolov8n.yaml")
    commands = build_stage_commands(
        config=config,
        stage="all",
        run_dir=tmp_path / "run",
        skip_train=True,
        model_path="runs/detect/train/weights/best.pt",
    )

    command_text = [" ".join(command) for command in commands]
    assert any("convert_visdrone_to_yolo.py" in item for item in command_text)
    assert not any("src.train" in item for item in command_text)
    assert any("src.val" in item for item in command_text)


def test_build_audit_only_commands(tmp_path):
    config = load_experiment_config("configs/experiments/baseline_yolov8n.yaml")
    commands = build_stage_commands(
        config=config,
        stage="audit",
        run_dir=tmp_path / "run",
        skip_train=False,
        model_path=None,
    )

    assert len(commands) == 1
    assert commands[0][1:] == [
        "-m",
        "src.harness.audit_data",
        "--config",
        str(config.path),
        "--format",
        "json",
        "--output",
        str(tmp_path / "run" / "audit.json"),
    ]


def test_create_run_dir_uses_experiment_name(tmp_path):
    config = load_experiment_config("configs/experiments/baseline_yolov8n.yaml")
    run_dir = create_run_dir(config, outputs_root=tmp_path, timestamp="20260704_120000")

    assert run_dir == tmp_path / "baseline_yolov8n" / "20260704_120000"
    assert run_dir.is_dir()
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
python3 -m pytest tests/test_harness_runner.py -q
```

Expected: FAIL because `src.harness.runner` does not exist.

- [ ] **Step 3: Implement runner module and CLI**

Create `src/harness/runner.py`:

```python
"""Experiment harness runner orchestration."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from src.harness.config import ExperimentConfig, load_experiment_config


VALID_STAGES = {"audit", "convert", "train", "val", "report", "all"}


def create_run_dir(
    config: ExperimentConfig,
    outputs_root: str | Path | None = None,
    timestamp: str | None = None,
) -> Path:
    root = Path(outputs_root) if outputs_root is not None else config.outputs.root
    stamp = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = root / config.experiment.name / stamp
    run_dir.mkdir(parents=True, exist_ok=False)
    shutil.copy2(config.path, run_dir / "resolved_config.yaml")
    return run_dir


def build_stage_commands(
    config: ExperimentConfig,
    stage: str,
    run_dir: Path,
    skip_train: bool,
    model_path: str | None,
) -> list[list[str]]:
    if stage not in VALID_STAGES:
        raise ValueError(f"invalid stage: {stage}")
    commands: list[list[str]] = []
    if stage in {"audit", "all"}:
        commands.append(
            [
                sys.executable,
                "-m",
                "src.harness.audit_data",
                "--config",
                str(config.path),
                "--format",
                "json",
                "--output",
                str(run_dir / "audit.json"),
            ]
        )
    if stage in {"convert", "all"}:
        commands.append(
            [
                sys.executable,
                "scripts/convert_visdrone_to_yolo.py",
                "--data-root",
                str(config.data.root),
                "--splits",
                *config.data.splits,
                "--img-ext",
                config.data.image_ext,
            ]
        )
    if stage in {"train", "all"} and config.train.enabled and not skip_train:
        commands.append(
            [
                sys.executable,
                "-m",
                "src.train",
                "--model",
                config.model.weights,
                "--data",
                str(config.data.dataset_yaml),
                "--epochs",
                str(config.train.epochs),
                "--batch",
                str(config.train.batch),
                "--imgsz",
                str(config.train.imgsz),
                "--device",
                config.train.device,
                "--project",
                str(run_dir / "detect"),
                "--workers",
                str(config.train.workers),
                "--patience",
                str(config.train.patience),
            ]
        )
    resolved_model = model_path
    if resolved_model is None and not skip_train:
        resolved_model = str(run_dir / "detect" / "train" / "weights" / "best.pt")
    if stage in {"val", "all"} and config.val.enabled:
        if resolved_model is None:
            raise ValueError("validation requires --model when --skip-train is used")
        commands.append(
            [
                sys.executable,
                "-m",
                "src.val",
                "--model",
                resolved_model,
                "--data",
                str(config.data.dataset_yaml),
                "--imgsz",
                str(config.val.imgsz),
                "--batch",
                str(config.val.batch),
                "--device",
                config.val.device,
                "--conf",
                str(config.val.conf),
                "--iou",
                str(config.val.iou),
                "--project",
                str(run_dir / "detect"),
            ]
        )
    if stage in {"report", "all"}:
        commands.append(
            [
                sys.executable,
                "-m",
                "src.harness.report",
                "--config",
                str(config.path),
                "--audit-json",
                str(run_dir / "audit.json"),
                "--metrics",
                str(run_dir / "metrics.json"),
                "--timestamp",
                run_dir.name,
                "--output",
                str(run_dir / "loop_report.md"),
            ]
        )
    return commands


def run_harness(
    config_path: str | Path,
    stage: str,
    dry_run: bool,
    skip_train: bool,
    model_path: str | None,
) -> Path:
    config = load_experiment_config(config_path)
    run_dir = create_run_dir(config)
    commands = build_stage_commands(config, stage, run_dir, skip_train, model_path)
    (run_dir / "commands.txt").write_text(
        "\n".join(" ".join(command) for command in commands) + "\n",
        encoding="utf-8",
    )
    if dry_run:
        for command in commands:
            print(" ".join(command))
        return run_dir
    for command in commands:
        subprocess.run(command, check=True)
    return run_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the configured experiment harness loop.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--config", default="configs/experiments/baseline_yolov8n.yaml")
    parser.add_argument("--stage", choices=sorted(VALID_STAGES), default="all")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-train", action="store_true")
    parser.add_argument("--model", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_dir = run_harness(
        config_path=args.config,
        stage=args.stage,
        dry_run=args.dry_run,
        skip_train=args.skip_train,
        model_path=args.model,
    )
    print(f"Harness run directory: {run_dir}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Add runner CLI script entry**

Modify `[project.scripts]` in `pyproject.toml`:

```toml
drone-run-harness = "src.harness.runner:main"
```

- [ ] **Step 5: Run runner tests**

Run:

```bash
python3 -m pytest tests/test_harness_runner.py -q
```

Expected: PASS with 3 tests.

- [ ] **Step 6: Commit runner task**

Run:

```bash
git add src/harness/runner.py tests/test_harness_runner.py pyproject.toml
git commit -m "feat: add harness runner"
```

## Task 6: Makefile And User Documentation

**Files:**
- Create: `docs/harness_loop.md`
- Modify: `README.md`
- Modify: `Makefile`

- [ ] **Step 1: Add Makefile targets**

Modify the top of `Makefile`:

```make
PYTHON ?= python3
DATA_ROOT ?= data
HARNESS_CONFIG ?= configs/experiments/baseline_yolov8n.yaml

.PHONY: help install install-dev test lint format convert train val audit harness-dry-run metrics-check
```

Add help lines:

```make
	@echo "  audit        运行 harness 数据审计"
	@echo "  harness-dry-run  打印完整 harness 闭环命令但不训练"
	@echo "  metrics-check     使用命令行指标检查 baseline gate"
```

Add targets:

```make
audit:
	$(PYTHON) -m src.harness.audit_data --config $(HARNESS_CONFIG) --data-root $(DATA_ROOT)

harness-dry-run:
	$(PYTHON) -m src.harness.runner --config $(HARNESS_CONFIG) --stage all --dry-run --skip-train --model runs/detect/train/weights/best.pt

metrics-check:
	$(PYTHON) -m src.harness.metrics --config $(HARNESS_CONFIG) --precision 0.354 --recall 0.274 --map50 0.258 --map 0.147
```

- [ ] **Step 2: Add user guide**

Create `docs/harness_loop.md`:

````markdown
# Harness 与 Loop 工程化

本文说明本项目新增的实验线束和迭代闭环。

## 核心概念

Harness engineering 指把数据检查、训练、验证、指标门槛和报告产物统一到一份实验合约中。

Loop engineering 指把一次实验变成可重复闭环：数据审计 → 转换 → 训练 → 验证 → 指标门槛 → 报告 → 下一轮建议。

## 默认配置

默认实验配置位于：

```bash
configs/experiments/baseline_yolov8n.yaml
```

默认保持 CPU 安全，不要求 GPU。真实训练仍然需要本地准备 VisDrone2019-DET 数据集和依赖环境。

## 快速命令

数据审计：

```bash
make audit
```

打印完整闭环命令但不执行训练：

```bash
make harness-dry-run
```

检查 baseline 指标门槛：

```bash
make metrics-check
```

仅用已有权重验证：

```bash
python3 -m src.harness.runner \
  --config configs/experiments/baseline_yolov8n.yaml \
  --stage val \
  --skip-train \
  --model runs/detect/train/weights/best.pt
```

完整本地闭环：

```bash
python3 -m src.harness.runner \
  --config configs/experiments/baseline_yolov8n.yaml \
  --stage all
```

## 输出目录

Harness 输出位于：

```text
runs/harness/<experiment>/<timestamp>/
```

典型产物包括：

- `resolved_config.yaml`
- `audit.json`
- `commands.txt`
- `loop_report.md`
- `detect/`

这些产物属于运行输出，不提交进 Git。

## 指标门槛

默认 gate 使用当前 README 中的 baseline 指标：

- precision: 0.354
- recall: 0.274
- mAP@0.5: 0.258
- mAP@0.5:0.95: 0.147

`allowed_drop: 0.02` 表示允许小幅波动。低于 `minimum - allowed_drop` 时，命令返回非零退出码。

## 需要用户提供的资源

实现和 CI 测试不需要额外资源。

真实训练或验证需要：

- VisDrone2019-DET 数据集，放在 README 约定的 `data/` 结构中。
- 已安装依赖的 Python 环境。
- 验证用 `best.pt`，或足够 CPU/GPU 时间重新训练。
````

- [ ] **Step 3: Add README section**

Insert this section after the Makefile quick command block in `README.md`:

````markdown
## Harness 与 Loop 工程化

本项目提供一套轻量实验线束，用于把数据审计、训练、验证、指标门槛和报告产物串成可重复闭环。

```bash
make audit            # 检查本地 VisDrone/YOLO 数据结构和标签质量
make harness-dry-run  # 打印完整闭环命令，不执行训练
make metrics-check    # 用 baseline 指标检查 gate
```

默认实验配置位于 `configs/experiments/baseline_yolov8n.yaml`。完整说明见
[`docs/harness_loop.md`](docs/harness_loop.md)。
````

- [ ] **Step 4: Run documentation-adjacent commands**

Run:

```bash
make metrics-check
```

Expected: PASS and print a Markdown metric gate table.

Run:

```bash
python3 -m pytest tests/test_harness_config.py tests/test_harness_metrics.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit docs and Makefile task**

Run:

```bash
git add Makefile README.md docs/harness_loop.md
git commit -m "docs: document harness loop workflow"
```

## Task 7: Full Verification And Cleanup

**Files:**
- Modify only files required by verification failures.

- [ ] **Step 1: Run the focused harness test suite**

Run:

```bash
python3 -m pytest tests/test_harness_config.py tests/test_harness_audit.py tests/test_harness_metrics.py tests/test_harness_report.py tests/test_harness_runner.py -q
```

Expected: PASS with all harness tests.

- [ ] **Step 2: Run all tests**

Run:

```bash
python3 -m pytest tests/ --tb=short -q
```

Expected: PASS, including the original 25 tests and all new harness tests.

- [ ] **Step 3: Run lint**

Run:

```bash
ruff check src/ scripts/ tests/
```

Expected: PASS with no reported issues.

- [ ] **Step 4: Run formatting check**

Run:

```bash
black --check src/ scripts/ tests/
```

Expected: PASS with all checked files unchanged.

- [ ] **Step 5: Run dry-run smoke command**

Run:

```bash
python3 -m src.harness.runner --config configs/experiments/baseline_yolov8n.yaml --stage audit --dry-run
```

Expected: PASS, create one ignored directory under `runs/harness/`, print the audit command, and avoid training.

- [ ] **Step 6: Inspect git status**

Run:

```bash
git status --short
```

Expected: only intentional source, test, docs, config, and pyproject changes. `runs/` must remain ignored.

- [ ] **Step 7: Commit final verification adjustments if any files changed**

If Step 1 through Step 6 required edits, commit them:

```bash
git add configs/experiments/baseline_yolov8n.yaml src/harness tests Makefile README.md docs/harness_loop.md pyproject.toml
git commit -m "chore: verify harness loop workflow"
```

If no files changed after the previous task commits, do not create an empty commit.

## Self-Review Against Spec

- Spec requires experiment YAML configuration: Task 1 creates `configs/experiments/baseline_yolov8n.yaml`.
- Spec requires data audit with JSON/Markdown output: Task 2 implements `src/harness/audit_data.py`.
- Spec requires runner stages and dry-run support: Task 5 implements `src/harness/runner.py`.
- Spec requires metric gate checking: Task 3 implements `src/harness/metrics.py`.
- Spec requires loop report and next-step suggestions: Task 4 implements `src/harness/report.py`.
- Spec requires docs and Makefile shortcuts: Task 6 updates README, Makefile, and adds `docs/harness_loop.md`.
- Spec requires lightweight tests without real data, weights, GPU, or network: Tasks 1 through 5 use synthetic data and direct unit tests only.
- Spec requires existing tests to keep passing: Task 7 runs the full test suite.
