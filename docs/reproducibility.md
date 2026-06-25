# Reproducibility

This document describes a safe baseline workflow for reproducing the VisDrone YOLOv8 experiment without committing datasets, model weights, or training outputs to Git.

## 1. Prepare Data

Download VisDrone2019-DET from the official source and confirm the license terms.

Expected layout:

```text
data/
  VisDrone2019-DET-train/
    images/
    annotations/
  VisDrone2019-DET-val/
    images/
    annotations/
  VisDrone2019-DET-test/
    images/
```

Convert labels:

```bash
python scripts/convert_visdrone_to_yolo.py
```

Expected converted layout:

```text
data/
  VisDrone2019-DET-train/
    images/
    labels/
  VisDrone2019-DET-val/
    images/
    labels/
```

## 2. Check Configuration

Confirm `data.yaml` points to the local converted dataset:

```yaml
train: data/VisDrone2019-DET-train/images
val: data/VisDrone2019-DET-val/images
test: data/VisDrone2019-DET-test/images
```

## 3. Train Baseline

Use a unique run name:

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

## 4. Validate

```bash
yolo detect val \
  model=runs/detect/train_YYYYMMDD_yolov8n_visdrone/weights/best.pt \
  data=data.yaml \
  imgsz=640 \
  batch=8 \
  project=runs/detect \
  name=val_YYYYMMDD_yolov8n_visdrone \
  exist_ok=False
```

## 5. Predict

```bash
yolo detect predict \
  model=runs/detect/train_YYYYMMDD_yolov8n_visdrone/weights/best.pt \
  source=path/to/image.jpg \
  imgsz=640 \
  conf=0.25 \
  project=runs/detect \
  name=predict_YYYYMMDD_sample \
  exist_ok=False
```

## Historical Baseline

Historical 10-epoch baseline metrics:

| metric | value |
| --- | ---: |
| precision | 0.35377 |
| recall | 0.27400 |
| mAP50 | 0.25755 |
| mAP50-95 | 0.14677 |

## Output Hygiene

Keep these out of Git:

- datasets under `data/`
- training outputs under `runs/`
- model weights such as `*.pt` and `*.pth`
- local credentials such as `.env`, `.env.*`, and `*.key`

For a public repository, copy only selected result images and sanitized metrics into `assets/` or `docs/`.
