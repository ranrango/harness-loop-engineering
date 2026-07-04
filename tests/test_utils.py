"""测试 src/utils.py 中的工具函数。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import VISDRONE_CLASSES, build_run_name, resolve_model


def test_类别表长度为10():
    assert len(VISDRONE_CLASSES) == 10


def test_类别表包含轿车():
    assert VISDRONE_CLASSES[3] == "轿车"


def test_模型路径存在时正常返回(tmp_path):
    model = tmp_path / "best.pt"
    model.write_text("fake weights")
    result = resolve_model(str(model))
    assert result == model


def test_模型路径不存在时抛出异常(tmp_path):
    with pytest.raises(FileNotFoundError, match="不存在"):
        resolve_model(str(tmp_path / "no_such.pt"))


def test_run名称格式正确():
    name = build_run_name("train", "yolov8n")
    parts = name.split("_")
    assert parts[0] == "train"
    assert len(parts[1]) == 8  # YYYYMMDD
    assert parts[1].isdigit()
    assert parts[2] == "yolov8n"
    assert parts[3] == "visdrone"


def test_run名称自定义后缀():
    name = build_run_name("val", "yolov8s", suffix="mydata")
    assert name.endswith("_mydata")
