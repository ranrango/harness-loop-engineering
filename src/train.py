"""YOLOv8 训练命令行入口。"""

from __future__ import annotations

import argparse
from pathlib import Path

from src.utils import build_run_name


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="在 VisDrone 数据集上训练 YOLOv8 检测器。",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--model", default="yolov8n.pt", help="预训练权重或模型 YAML。")
    parser.add_argument("--data", default="data.yaml", help="数据集配置 YAML。")
    parser.add_argument("--epochs", type=int, default=10, help="训练轮数。")
    parser.add_argument("--batch", type=int, default=8, help="批次大小。")
    parser.add_argument("--imgsz", type=int, default=640, help="输入图片尺寸。")
    parser.add_argument("--device", default="cpu", help="训练设备：cpu、0、mps 等。")
    parser.add_argument("--project", default="runs/detect", help="输出根目录。")
    parser.add_argument("--name", default=None, help="run 名称（默认自动生成）。")
    parser.add_argument("--exist-ok", action="store_true", help="允许复用已有 run 目录。")
    parser.add_argument("--workers", type=int, default=4, help="数据加载线程数。")
    parser.add_argument("--patience", type=int, default=50, help="早停轮数。")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model_path = args.model
    run_name = args.name or build_run_name("train", Path(model_path).stem)

    from ultralytics import YOLO  # 延迟导入，使测试无需安装 torch

    model = YOLO(model_path)
    model.train(
        data=args.data,
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        device=args.device,
        project=args.project,
        name=run_name,
        exist_ok=args.exist_ok,
        workers=args.workers,
        patience=args.patience,
    )
    print(f"训练完成。结果保存到 {args.project}/{run_name}/")


if __name__ == "__main__":
    main()
