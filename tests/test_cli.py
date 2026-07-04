"""测试 src/detect.py、src/train.py、src/val.py 的命令行参数解析。

这些测试只验证 argparse 逻辑，不会导入 torch 或 ultralytics。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


# ── detect.py ────────────────────────────────────────────────────────────────


def test_推理必选参数及默认值(tmp_path, monkeypatch):
    model = tmp_path / "best.pt"
    model.write_text("fake")
    monkeypatch.setattr(
        "sys.argv",
        [
            "detect.py",
            "--model",
            str(model),
            "--source",
            "image.jpg",
        ],
    )
    from src.detect import parse_args

    args = parse_args()
    assert args.conf == 0.25
    assert args.iou == 0.45
    assert args.classes is None
    assert args.save_txt is False


def test_推理指定类别过滤(tmp_path, monkeypatch):
    model = tmp_path / "best.pt"
    model.write_text("fake")
    monkeypatch.setattr(
        "sys.argv",
        [
            "detect.py",
            "--model",
            str(model),
            "--source",
            "img.jpg",
            "--classes",
            "3",
            "4",
            "8",
        ],
    )
    from src.detect import parse_args

    args = parse_args()
    assert args.classes == [3, 4, 8]


# ── train.py ─────────────────────────────────────────────────────────────────


def test_训练默认参数(monkeypatch):
    monkeypatch.setattr("sys.argv", ["train.py"])
    from src.train import parse_args

    args = parse_args()
    assert args.epochs == 10
    assert args.batch == 8
    assert args.model == "yolov8n.pt"
    assert args.device == "cpu"


def test_训练自定义参数(monkeypatch):
    monkeypatch.setattr("sys.argv", ["train.py", "--epochs", "50", "--device", "mps"])
    from src.train import parse_args

    args = parse_args()
    assert args.epochs == 50
    assert args.device == "mps"


# ── val.py ───────────────────────────────────────────────────────────────────


def test_验证缺少模型参数时报错(monkeypatch):
    monkeypatch.setattr("sys.argv", ["val.py"])
    from src.val import parse_args

    with pytest.raises(SystemExit):
        parse_args()


def test_验证默认参数(tmp_path, monkeypatch):
    model = tmp_path / "best.pt"
    model.write_text("fake")
    monkeypatch.setattr("sys.argv", ["val.py", "--model", str(model)])
    from src.val import parse_args

    args = parse_args()
    assert args.conf == 0.001
    assert args.iou == 0.6
    assert args.batch == 8
