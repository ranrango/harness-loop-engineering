"""YOLOv8 验证命令行入口。"""

from __future__ import annotations

import argparse

from src.utils import build_run_name, resolve_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="在 VisDrone val 集上验证 YOLOv8 检测器。",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--model", required=True, help="训练好的权重路径（.pt）。")
    parser.add_argument("--data", default="data.yaml", help="数据集配置 YAML。")
    parser.add_argument("--imgsz", type=int, default=640, help="输入图片尺寸。")
    parser.add_argument("--batch", type=int, default=8, help="批次大小。")
    parser.add_argument("--device", default="cpu", help="推理设备：cpu、0、mps 等。")
    parser.add_argument("--project", default="runs/detect", help="输出根目录。")
    parser.add_argument("--name", default=None, help="run 名称（默认自动生成）。")
    parser.add_argument("--exist-ok", action="store_true", help="允许复用已有 run 目录。")
    parser.add_argument("--conf", type=float, default=0.001, help="置信度阈值。")
    parser.add_argument("--iou", type=float, default=0.6, help="NMS IoU 阈值。")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model_path = resolve_model(args.model)
    run_name = args.name or build_run_name("val", model_path.stem)

    from ultralytics import YOLO

    model = YOLO(str(model_path))
    metrics = model.val(
        data=args.data,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project=args.project,
        name=run_name,
        exist_ok=args.exist_ok,
        conf=args.conf,
        iou=args.iou,
    )

    print(f"\n{'─'*40}")
    print(f"  mAP@0.5      : {metrics.box.map50:.4f}")
    print(f"  mAP@0.5:0.95 : {metrics.box.map:.4f}")
    print(f"  精确率       : {metrics.box.mp:.4f}")
    print(f"  召回率       : {metrics.box.mr:.4f}")
    print(f"{'─'*40}")
    print(f"结果已保存到 {args.project}/{run_name}/")


if __name__ == "__main__":
    main()
