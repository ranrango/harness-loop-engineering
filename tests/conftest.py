"""公共测试夹具（pytest fixtures）。"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from tests.image_helpers import make_jpeg


@pytest.fixture()
def tmp_visdrone_split(tmp_path: Path):
    """创建一个最小化的 VisDrone 切分目录结构，供测试使用。"""
    split = "train"
    img_dir = tmp_path / f"VisDrone2019-DET-{split}" / "images"
    ann_dir = tmp_path / f"VisDrone2019-DET-{split}" / "annotations"
    img_dir.mkdir(parents=True)
    ann_dir.mkdir(parents=True)

    # 图片1：1000×750 JPEG，2个有效框 + 1个忽略区域（category=0）
    (img_dir / "img1.jpg").write_bytes(make_jpeg(1000, 750))
    (ann_dir / "img1.txt").write_text(
        textwrap.dedent("""\
            100,50,200,100,1,4,0,0
            300,200,80,60,1,1,0,0
            0,0,50,50,1,0,0,0
        """),
        encoding="utf-8",
    )

    # 图片2：640×480 JPEG，2个有效框
    (img_dir / "img2.jpg").write_bytes(make_jpeg(640, 480))
    (ann_dir / "img2.txt").write_text(
        textwrap.dedent("""\
            10,10,100,80,1,10,0,0
            200,150,50,40,1,8,0,0
        """),
        encoding="utf-8",
    )

    return tmp_path, split
