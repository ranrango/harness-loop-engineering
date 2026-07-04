# Release Candidate Manifest

Generated: 2026-06-25

## Included

- `README.md`
- `pyproject.toml`
- `.gitignore`
- `data.yaml`
- `test.py`
- `src/detect.py`
- `scripts/convert_visdrone_to_yolo.py`
- `docs/environment.md`
- `docs/reproducibility.md`
- `docs/results.csv`
- `assets/codex_predict_bestpt_image_2.jpg`
- `assets/results.png`
- `assets/confusion_matrix.png`
- `assets/BoxPR_curve.png`
- `PUBLICATION_CHECKLIST.md`

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
- local notebooks and temporary files

## Source Notes

- Documentation comes from the Codex output candidates.
- `test.py`, `.gitignore`, and `pyproject.toml` come from the clean main worktree.
- `data.yaml` and `scripts/convert_visdrone_to_yolo.py` come from the local experiment worktree.
- Assets are selected copies from the Codex visual project artifact directory.
