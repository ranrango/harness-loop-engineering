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
