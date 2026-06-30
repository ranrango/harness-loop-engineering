"""测试 scripts/convert_visdrone_to_yolo.py 的转换逻辑。"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.convert_visdrone_to_yolo import (
    ConvertStats,
    convert_one,
    convert_split,
    _read_image_dimensions,
)
from tests.image_helpers import make_jpeg as _make_jpeg, make_png as _make_png


# ── _read_image_dimensions ───────────────────────────────────────────────────

def test_读取JPEG尺寸(tmp_path):
    p = tmp_path / "img.jpg"
    p.write_bytes(_make_jpeg(1024, 768))
    assert _read_image_dimensions(p) == (1024, 768)


def test_读取PNG尺寸(tmp_path):
    p = tmp_path / "img.png"
    p.write_bytes(_make_png(320, 240))
    assert _read_image_dimensions(p) == (320, 240)


def test_文件不存在返回None(tmp_path):
    assert _read_image_dimensions(tmp_path / "不存在.jpg") is None


def test_损坏文件返回None(tmp_path):
    p = tmp_path / "bad.jpg"
    p.write_bytes(b"\x00\x01\x02\x03garbage")
    assert _read_image_dimensions(p) is None


# ── convert_one ──────────────────────────────────────────────────────────────

def test_基本转换(tmp_path):
    img_dir = tmp_path / "images"
    img_dir.mkdir()
    out_dir = tmp_path / "labels"
    out_dir.mkdir()

    (img_dir / "img1.jpg").write_bytes(_make_jpeg(1000, 500))
    ann = tmp_path / "img1.txt"
    # 轿车（category=4 → cls_id=3），框为 (100, 50, 200, 100)
    ann.write_text("100,50,200,100,1,4,0,0\n", encoding="utf-8")

    stats = convert_one(ann, img_dir, out_dir, "jpg")

    assert stats.images_processed == 1
    assert stats.boxes_written == 1
    assert stats.files_missing_image == 0

    lines = (out_dir / "img1.txt").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    parts = lines[0].split()
    assert parts[0] == "3"  # 轿车 → cls_id 3
    xc, yc, bw, bh = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
    assert abs(xc - 0.2) < 1e-4   # (100 + 100) / 1000
    assert abs(yc - 0.2) < 1e-4   # (50 + 50) / 500
    assert abs(bw - 0.2) < 1e-4   # 200 / 1000
    assert abs(bh - 0.2) < 1e-4   # 100 / 500


def test_忽略区域被过滤(tmp_path):
    img_dir = tmp_path / "images"
    img_dir.mkdir()
    out_dir = tmp_path / "labels"
    out_dir.mkdir()

    (img_dir / "img.jpg").write_bytes(_make_jpeg(640, 480))
    ann = tmp_path / "img.txt"
    ann.write_text("0,0,50,50,1,0,0,0\n", encoding="utf-8")  # category=0 忽略区域

    stats = convert_one(ann, img_dir, out_dir, "jpg")
    assert stats.boxes_skipped_ignored == 1
    assert stats.boxes_written == 0
    assert (out_dir / "img.txt").read_text().strip() == ""


def test_超出边界的框被截断(tmp_path):
    img_dir = tmp_path / "images"
    img_dir.mkdir()
    out_dir = tmp_path / "labels"
    out_dir.mkdir()

    (img_dir / "img.jpg").write_bytes(_make_jpeg(100, 100))
    ann = tmp_path / "img.txt"
    # 框略微超出图片右下角边界
    ann.write_text("90,90,20,20,1,3,0,0\n", encoding="utf-8")

    stats = convert_one(ann, img_dir, out_dir, "jpg")
    assert stats.boxes_written == 1
    parts = (out_dir / "img.txt").read_text().strip().split()
    xc, yc, bw, bh = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
    assert 0.0 <= xc <= 1.0
    assert 0.0 <= yc <= 1.0
    assert 0.0 <= bw <= 1.0
    assert 0.0 <= bh <= 1.0


def test_图片缺失时跳过(tmp_path):
    img_dir = tmp_path / "images"
    img_dir.mkdir()
    out_dir = tmp_path / "labels"
    out_dir.mkdir()

    ann = tmp_path / "img.txt"
    ann.write_text("100,50,200,100,1,4,0,0\n", encoding="utf-8")

    stats = convert_one(ann, img_dir, out_dir, "jpg")
    assert stats.files_missing_image == 1
    assert stats.images_processed == 0


def test_零尺寸框被跳过(tmp_path):
    img_dir = tmp_path / "images"
    img_dir.mkdir()
    out_dir = tmp_path / "labels"
    out_dir.mkdir()

    (img_dir / "img.jpg").write_bytes(_make_jpeg(640, 480))
    ann = tmp_path / "img.txt"
    ann.write_text("100,50,0,0,1,4,0,0\n", encoding="utf-8")  # 宽高为0

    stats = convert_one(ann, img_dir, out_dir, "jpg")
    assert stats.boxes_skipped_invalid == 1


# ── convert_split ────────────────────────────────────────────────────────────

def test_整体转换流程(tmp_visdrone_split):
    data_root, split = tmp_visdrone_split
    stats = convert_split(data_root, split, "jpg")

    label_dir = data_root / f"VisDrone2019-DET-{split}" / "labels"
    assert label_dir.is_dir()
    assert len(list(label_dir.glob("*.txt"))) == 2
    assert stats.images_processed == 2
    assert stats.boxes_written >= 3


def test_标注目录不存在时跳过(tmp_path):
    stats = convert_split(tmp_path, "test", "jpg")
    assert stats.images_processed == 0


# ── CLI 参数 ─────────────────────────────────────────────────────────────────

def test_默认参数(monkeypatch):
    monkeypatch.setattr("sys.argv", ["convert_visdrone_to_yolo.py"])
    from scripts.convert_visdrone_to_yolo import parse_args
    args = parse_args()
    assert args.data_root == "data"
    assert args.splits == ["train", "val"]
    assert args.img_ext == "jpg"


def test_自定义参数(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        ["convert_visdrone_to_yolo.py", "--data-root", "/tmp/data", "--splits", "val", "--img-ext", "png"],
    )
    from scripts.convert_visdrone_to_yolo import parse_args
    args = parse_args()
    assert args.data_root == "/tmp/data"
    assert args.splits == ["val"]
    assert args.img_ext == "png"
