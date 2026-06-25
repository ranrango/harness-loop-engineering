# Drone Object Detection on VisDrone

YOLOv8 baseline for small object detection in UAV imagery using the VisDrone2019-DET dataset.

This repository keeps source code, configuration, and reproducibility notes in Git. Datasets, training runs, model weights, local credentials, and large generated artifacts are intentionally kept out of the repository.

## Highlights

- Converts VisDrone detection annotations to YOLO format.
- Trains a YOLOv8 detector on 10 VisDrone object classes.
- Includes a baseline training record and reproducible command templates.
- Uses environment variables for local API credentials.

## Dataset

Dataset: VisDrone2019-DET

Classes:

| id | class |
| ---: | --- |
| 0 | pedestrian |
| 1 | people |
| 2 | bicycle |
| 3 | car |
| 4 | van |
| 5 | truck |
| 6 | tricycle |
| 7 | awning-tricycle |
| 8 | bus |
| 9 | motor |

Expected local layout after download/conversion:

```text
data/
  VisDrone2019-DET-train/
    images/
    labels/
  VisDrone2019-DET-val/
    images/
    labels/
  VisDrone2019-DET-test/
    images/
```

The dataset is not included in this repository. Download it from the official VisDrone source and check its license before use.

## Environment

Requires Python 3.9 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
```

## Data Conversion

Convert VisDrone annotations to YOLO label files:

```bash
python scripts/convert_visdrone_to_yolo.py
```

Review `data.yaml` before training and make sure the `train`, `val`, and `test` paths match your local dataset layout.

## Baseline Training

Use a unique run name to avoid overwriting previous experiments:

```bash
yolo detect train \
  model=yolov8n.pt \
  data=data.yaml \
  epochs=10 \
  batch=8 \
  imgsz=640 \
  device=cpu \
  project=runs/detect \
  name=train_YYYYMMDD_yolov8n_visdrone \
  exist_ok=False
```

## Validation

```bash
yolo detect val \
  model=runs/detect/visdrone_baseline/weights/best.pt \
  data=data.yaml \
  imgsz=640 \
  batch=8 \
  project=runs/detect \
  name=val_YYYYMMDD_visdrone_baseline \
  exist_ok=False
```

## Sample Prediction

```bash
yolo detect predict \
  model=runs/detect/visdrone_baseline/weights/best.pt \
  source=path/to/image.jpg \
  imgsz=640 \
  conf=0.25 \
  project=runs/detect \
  name=predict_YYYYMMDD_sample \
  exist_ok=False
```

## Baseline Metrics

Historical 10-epoch baseline:

| metric | value |
| --- | ---: |
| precision | 0.35377 |
| recall | 0.27400 |
| mAP50 | 0.25755 |
| mAP50-95 | 0.14677 |

## Security

Do not commit API keys or local credentials. The smoke test reads credentials from environment variables:

```bash
export DEEPSEEK_API_KEY="your_local_key"
python test.py
```

Keep local secret files such as `.env`, `.env.*`, and `*.key` out of Git.

## Repository Hygiene

Recommended exclusions:

- `data/`
- `runs/`
- `weights/`
- `*.pt`, `*.pth`, `*.onnx`, `*.engine`
- `.env`, `.env.*`, `*.key`

For public release, include only source code, configuration, documentation, and selected result images that do not expose private paths or credentials.
