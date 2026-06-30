"""将 VisDrone2019-DET 标注文件转换为 YOLO 格式。

用法
----
    python scripts/convert_visdrone_to_yolo.py
    python scripts/convert_visdrone_to_yolo.py --data-root data --splits train val
    python scripts/convert_visdrone_to_yolo.py --data-root data --splits train val --img-ext jpg
"""

from __future__ import annotations

import argparse
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path


# VisDrone 类别 ID 为 1-based（1–10），0 表示忽略区域。
# 转换为 YOLO 的 0-based ID 时减 1。
NUM_CLASSES = 10


@dataclass
class ConvertStats:
    """单次转换的统计信息。"""
    images_processed: int = 0
    boxes_written: int = 0
    boxes_skipped_ignored: int = 0   # category=0（忽略区域）
    boxes_skipped_invalid: int = 0   # 尺寸为零或字段非法
    files_missing_image: int = 0     # 找不到对应图片

    def merge(self, other: ConvertStats) -> None:
        self.images_processed += other.images_processed
        self.boxes_written += other.boxes_written
        self.boxes_skipped_ignored += other.boxes_skipped_ignored
        self.boxes_skipped_invalid += other.boxes_skipped_invalid
        self.files_missing_image += other.files_missing_image


def _read_image_dimensions(img_path: Path) -> tuple[int, int] | None:
    """只读取图片文件头来获取宽高，无需加载完整图片，支持 JPEG 和 PNG。

    返回 (width, height)；文件不存在或格式不支持时返回 None。
    """
    try:
        with img_path.open("rb") as fh:
            header = fh.read(24)
    except OSError:
        return None

    # PNG：签名（8字节）+ IHDR chunk 长度（4）+ 'IHDR'（4）+ 宽（4）+ 高（4）
    if header[:8] == b"\x89PNG\r\n\x1a\n" and len(header) >= 24:
        w = struct.unpack(">I", header[16:20])[0]
        h = struct.unpack(">I", header[20:24])[0]
        return w, h

    # JPEG：扫描 SOF0/SOF2 等标记，其中包含图片尺寸
    if header[:2] == b"\xff\xd8":
        try:
            with img_path.open("rb") as fh:
                fh.read(2)  # 跳过 SOI
                while True:
                    marker = fh.read(2)
                    if len(marker) < 2:
                        break
                    if marker[0] != 0xFF:
                        break
                    length = struct.unpack(">H", fh.read(2))[0]
                    if marker[1] in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                                     0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                        fh.read(1)  # 精度字段
                        h = struct.unpack(">H", fh.read(2))[0]
                        w = struct.unpack(">H", fh.read(2))[0]
                        return w, h
                    fh.seek(length - 2, 1)
        except (struct.error, OSError):
            return None

    return None


def convert_one(
    ann_path: Path,
    img_dir: Path,
    out_label_dir: Path,
    img_ext: str,
) -> ConvertStats:
    """将单个 VisDrone 标注文件转换为 YOLO 格式标注文件。"""
    stats = ConvertStats()
    img_path = img_dir / ann_path.with_suffix(f".{img_ext}").name

    dims = _read_image_dimensions(img_path)
    if dims is None:
        stats.files_missing_image += 1
        return stats

    w, h = dims
    yolo_lines: list[str] = []

    for raw_line in ann_path.read_text(encoding="utf-8").splitlines():
        parts = raw_line.strip().split(",")
        if len(parts) < 6:
            continue

        try:
            x1, y1, box_w, box_h = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
            category = int(parts[5])
        except ValueError:
            stats.boxes_skipped_invalid += 1
            continue

        cls_id = category - 1  # 转换为 0-based

        if cls_id < 0 or cls_id >= NUM_CLASSES:
            stats.boxes_skipped_ignored += 1
            continue

        if box_w <= 0 or box_h <= 0:
            stats.boxes_skipped_invalid += 1
            continue

        xc = (x1 + box_w / 2) / w
        yc = (y1 + box_h / 2) / h
        bw = box_w / w
        bh = box_h / h

        # 对超出图片边界的标注框进行截断
        xc = max(0.0, min(1.0, xc))
        yc = max(0.0, min(1.0, yc))
        bw = max(0.0, min(1.0, bw))
        bh = max(0.0, min(1.0, bh))

        yolo_lines.append(f"{cls_id} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}")
        stats.boxes_written += 1

    out_path = out_label_dir / ann_path.name
    out_path.write_text("\n".join(yolo_lines), encoding="utf-8")
    stats.images_processed += 1
    return stats


def convert_split(data_root: Path, split: str, img_ext: str) -> ConvertStats:
    """转换一个数据集切分（train / val / test）的所有标注文件。"""
    ann_dir = data_root / f"VisDrone2019-DET-{split}" / "annotations"
    img_dir = data_root / f"VisDrone2019-DET-{split}" / "images"
    out_label_dir = data_root / f"VisDrone2019-DET-{split}" / "labels"

    if not ann_dir.is_dir():
        print(f"  [跳过] 标注目录不存在：{ann_dir}")
        return ConvertStats()

    out_label_dir.mkdir(exist_ok=True)

    ann_files = sorted(ann_dir.glob("*.txt"))
    total = len(ann_files)
    stats = ConvertStats()

    for i, ann_path in enumerate(ann_files, 1):
        file_stats = convert_one(ann_path, img_dir, out_label_dir, img_ext)
        stats.merge(file_stats)
        if i % 500 == 0 or i == total:
            print(f"  [{split}] {i}/{total} 已处理 …", end="\r")

    print()
    return stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="将 VisDrone2019-DET 标注转换为 YOLO 格式。",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--data-root",
        default="data",
        help="包含 VisDrone2019-DET-train/、-val/ 等子目录的根路径。",
    )
    parser.add_argument(
        "--splits",
        nargs="+",
        default=["train", "val"],
        metavar="切分名",
        help="要转换的数据集切分。",
    )
    parser.add_argument(
        "--img-ext",
        default="jpg",
        metavar="扩展名",
        help="图片文件扩展名（不含点号）。",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_root = Path(args.data_root)

    total = ConvertStats()
    for split in args.splits:
        print(f"正在转换 '{split}' 切分 …")
        stats = convert_split(data_root, split, args.img_ext)
        total.merge(stats)
        print(
            f"  完成 — {stats.images_processed} 张图片，"
            f"{stats.boxes_written} 个框已写入，"
            f"{stats.boxes_skipped_ignored} 个忽略区域跳过，"
            f"{stats.boxes_skipped_invalid} 个无效框跳过，"
            f"{stats.files_missing_image} 张图片缺失。"
        )

    if len(args.splits) > 1:
        print(
            f"\n合计 — {total.images_processed} 张图片，"
            f"{total.boxes_written} 个框，"
            f"{total.boxes_skipped_ignored + total.boxes_skipped_invalid} 个跳过。"
        )


if __name__ == "__main__":
    main()
