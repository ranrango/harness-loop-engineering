"""YOLOv8 推理命令行入口。"""

from __future__ import annotations

import argparse
from pathlib import Path

from src.utils import build_run_name, resolve_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="对图片、目录或视频运行 YOLOv8 目标检测。",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--model", required=True, help="训练好的模型权重路径（.pt）。")
    parser.add_argument("--source", required=True, help="图片路径、目录、视频或 URL。")
    parser.add_argument("--project", default="runs/detect", help="输出根目录。")
    parser.add_argument("--name", default=None, help="本次 run 的名称（默认自动生成）。")
    parser.add_argument("--imgsz", type=int, default=640, help="推理图片尺寸。")
    parser.add_argument("--conf", type=float, default=0.25, help="置信度阈值（0–1）。")
    parser.add_argument("--iou", type=float, default=0.45, help="NMS IoU 阈值（0–1）。")
    parser.add_argument("--device", default="cpu", help="推理设备：cpu、0、mps 等。")
    parser.add_argument(
        "--classes",
        nargs="+",
        type=int,
        metavar="类别ID",
        help="只检测指定类别，例如 --classes 3 4 8 表示只检测轿车/面包车/公交车。",
    )
    parser.add_argument("--save-txt", action="store_true", help="保存每张图片的 YOLO 格式标注文件。")
    parser.add_argument("--no-save", action="store_true", help="不保存带标注框的结果图片。")
    parser.add_argument(
        "--exist-ok",
        action="store_true",
        help="允许向已存在的 run 目录写入（否则报错）。",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model_path = resolve_model(args.model)
    run_name = args.name or build_run_name("predict", model_path.stem)

    from ultralytics import YOLO  # 延迟导入，使测试无需安装 torch

    model = YOLO(str(model_path))
    results = model.predict(
        source=args.source,
        project=args.project,
        name=run_name,
        imgsz=args.imgsz,
        conf=args.conf,
        iou=args.iou,
        device=args.device,
        classes=args.classes,
        save=not args.no_save,
        save_txt=args.save_txt,
        exist_ok=args.exist_ok,
    )

    if not results:
        print("未返回任何结果。")
        return

    total = sum(len(r.boxes) for r in results)
    print(f"\n共处理 {len(results)} 张图片，检测到 {total} 个目标。")

    if results[0].boxes is not None and len(results[0].boxes):
        from collections import Counter
        from src.utils import VISDRONE_CLASSES

        counts: Counter[str] = Counter()
        for r in results:
            for cls_id in r.boxes.cls.tolist():
                counts[VISDRONE_CLASSES.get(int(cls_id), str(int(cls_id)))] += 1
        print("  各类别数量：")
        for name, n in sorted(counts.items(), key=lambda x: -x[1]):
            print(f"    {name:<12} {n}")

    print(f"\n结果已保存到 {args.project}/{run_name}/")


if __name__ == "__main__":
    main()
