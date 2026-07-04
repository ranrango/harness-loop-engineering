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
