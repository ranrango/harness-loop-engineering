# Release Manifest

Release: `v0.1.0`  
Published: 2026-07-05  
Repository: `ranrango/harness-loop-engineering`

## Included

- Harness & Loop Engineering guide material:
  - `PRACTICAL_GUIDE.md`
  - `applications/`
  - `harness/`
  - `loop/`
- Drone object detection project:
  - `src/detect.py`
  - `src/train.py`
  - `src/val.py`
  - `src/utils.py`
  - `scripts/convert_visdrone_to_yolo.py`
  - `data.yaml`
  - `configs/experiments/baseline_yolov8n.yaml`
- Harness workflow implementation:
  - `src/harness/config.py`
  - `src/harness/audit_data.py`
  - `src/harness/metrics.py`
  - `src/harness/report.py`
  - `src/harness/runner.py`
- Documentation:
  - `README.md`
  - `CHANGELOG.md`
  - `CONTRIBUTING.md`
  - `docs/environment.md`
  - `docs/reproducibility.md`
  - `docs/harness_loop.md`
  - `docs/superpowers/specs/`
  - `docs/superpowers/plans/`
- Verification and packaging:
  - `.github/workflows/ci.yml`
  - `pyproject.toml`
  - `Makefile`
  - `tests/`
  - `.env.example`
  - `LICENSE`
- Baseline evidence and visual assets:
  - `docs/results.csv`
  - `assets/codex_predict_bestpt_image_2.jpg`
  - `assets/results.png`
  - `assets/confusion_matrix.png`
  - `assets/BoxPR_curve.png`

## Intentionally Excluded

- `data/`
- `runs/`
- `*.pt`
- `*.pth`
- `*.onnx`
- `*.engine`
- `.env`
- `.env.*`
- `*.key`
- Local notebooks and temporary files

## Release Verification

- PR #1: `Add drone detection harness and loop workflow`
- PR #2: `Remove local path from Chinese implementation plan`
- Release tag: `v0.1.0`
- Main branch CI: passing on Python 3.9, 3.10, 3.11, plus black format check.
