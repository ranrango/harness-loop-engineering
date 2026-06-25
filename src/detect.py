"""Small CLI wrapper for YOLOv8 prediction."""

from __future__ import annotations

import argparse
from pathlib import Path

from ultralytics import YOLO


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run YOLOv8 prediction.")
    parser.add_argument("--model", required=True, help="Path to a YOLO model file.")
    parser.add_argument("--source", required=True, help="Image, video, directory, or stream source.")
    parser.add_argument("--project", default="runs/detect", help="Output project directory.")
    parser.add_argument("--name", default="predict", help="Output run name.")
    parser.add_argument("--imgsz", type=int, default=640, help="Inference image size.")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold.")
    parser.add_argument("--device", default="cpu", help="Device, for example cpu, 0, or mps.")
    parser.add_argument(
        "--exist-ok",
        action="store_true",
        help="Allow writing into an existing output run directory.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model_path = Path(args.model)
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    model = YOLO(str(model_path))
    results = model.predict(
        source=args.source,
        project=args.project,
        name=args.name,
        imgsz=args.imgsz,
        conf=args.conf,
        device=args.device,
        exist_ok=args.exist_ok,
        save=True,
    )
    if results:
        print(f"detections={len(results[0].boxes)}")


if __name__ == "__main__":
    main()
