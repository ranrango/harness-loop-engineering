# Publication Checklist

Use this checklist before copying the release candidate into the real repository or pushing to GitHub.

## Safety

- [ ] No API keys, tokens, `.env` files, or private credentials.
- [ ] No local absolute paths.
- [ ] No full datasets under `data/`.
- [ ] No YOLO training outputs under `runs/`.
- [ ] No model weights such as `*.pt`, `*.pth`, `*.onnx`, or `*.engine`.
- [ ] Images in `assets/` do not expose private accounts, paths, or credentials.

## Repository

- [ ] `README.md` describes the project without relying on local machine paths.
- [ ] `docs/environment.md` matches `pyproject.toml`.
- [ ] `docs/reproducibility.md` uses unique run names and avoids overwriting historical runs.
- [ ] `data.yaml` uses relative dataset paths.
- [ ] `.gitignore` excludes data, runs, weights, environments, and local secrets.

## Git Workflow

- [ ] Create a new branch from clean `main`.
- [ ] Copy only reviewed files from this candidate package.
- [ ] Run syntax checks.
- [ ] Run secret/path scans.
- [ ] Commit locally.
- [ ] Push only the safe branch after review.
