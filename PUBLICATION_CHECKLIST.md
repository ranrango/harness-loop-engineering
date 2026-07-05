# Publication Checklist

Status: completed for `v0.1.0` on 2026-07-05.

Use this checklist before future public releases.

## Safety

- [x] No API keys, tokens, `.env` files, or private credentials are tracked.
- [x] No local absolute filesystem paths remain in public documentation.
- [x] No full datasets under `data/` are tracked.
- [x] No YOLO training outputs under `runs/` are tracked.
- [x] No model weights such as `*.pt`, `*.pth`, `*.onnx`, or `*.engine` are tracked.
- [x] Images in `assets/` do not expose private accounts, paths, or credentials.

## Repository

- [x] `README.md` describes the combined Harness/Loop and drone detection project without relying on local paths.
- [x] `docs/environment.md` matches `pyproject.toml`.
- [x] `docs/reproducibility.md` uses reproducible commands and avoids committing generated runs.
- [x] `data.yaml` uses relative dataset paths.
- [x] `.gitignore` excludes data, runs, weights, environments, and local secrets.
- [x] `CHANGELOG.md` records the public `v0.1.0` release.

## GitHub Workflow

- [x] Pull Request #1 merged the complete project into `main`.
- [x] Pull Request #2 removed a local absolute path from the Chinese implementation plan.
- [x] `main` CI passed after both merges.
- [x] `v0.1.0` GitHub Release was created from `main`.
- [x] Repository description, topics, and merge settings were updated.

## Verification Commands

```bash
python3 -m pytest tests/ --tb=short -q
ruff check src/ scripts/ tests/
black --check .
python3 -m src.harness.runner --config configs/experiments/baseline_yolov8n.yaml --stage audit --dry-run
```

Safety scans used during release:

- Search the repository for machine-specific absolute paths, local usernames, token prefixes, and private-key headers.
- Confirm Git is not tracking generated data, runs, model weights, `.env` files, or key files:

```bash
git ls-files 'runs/**' 'data/**' '*.pt' '*.pth' '*.onnx' '*.engine' '.env' '*.key'
```
