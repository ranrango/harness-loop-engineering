# Harness and Loop Engineering Design

Date: 2026-07-04
Project: `ai-harness-loop-lab`

## Purpose

This project already has a clean YOLOv8 baseline: conversion, training, validation,
prediction, tests, Makefile targets, CI, and reproducibility notes. The next step is
to make the project easier to iterate as an engineering system, not just a set of
one-off commands.

This design adds:

- harness engineering: a standard experiment contract for data checks, training,
  validation, metric gates, and report artifacts.
- loop engineering: a repeatable cycle from data audit to experiment run to metric
  review to next-step recommendations.

The implementation must not commit datasets, model weights, credentials, or training
outputs. CI must remain lightweight and runnable without VisDrone, YOLO weights, GPU,
or network downloads.

## Chosen Approach

Use a configuration-driven lightweight MLOps loop.

Rejected alternatives:

- Minimal script-only approach: faster to add, but experiments remain too informal and
  hard to compare.
- Full ML platform approach with MLflow, DVC, W&B, or a remote runner: useful later,
  but too heavy for the current repository and would require extra services and user
  resources.

The chosen approach adds local, testable Python modules and CLI entry points. It keeps
the current project style and does not replace existing commands.

## Scope

In scope:

- Experiment YAML configuration.
- Data audit for VisDrone-style folders and YOLO label outputs.
- Harness runner that orchestrates existing conversion, training, validation, and
  reporting steps.
- Metric gate checking against a baseline or configured thresholds.
- Loop report generation with next-step recommendations.
- Documentation and Makefile shortcuts.
- Unit tests for all logic that can run without real datasets or weights.

Out of scope for this phase:

- Downloading VisDrone automatically.
- Committing real data, weights, or run outputs.
- Running real training in CI.
- Adding a web dashboard.
- Adding external experiment tracking services.

## Architecture

Add a new package:

```text
src/harness/
  __init__.py
  config.py
  audit_data.py
  metrics.py
  report.py
  runner.py
```

Add configuration and documentation:

```text
configs/experiments/baseline_yolov8n.yaml
docs/harness_loop.md
```

Add tests:

```text
tests/test_harness_config.py
tests/test_harness_audit.py
tests/test_harness_metrics.py
tests/test_harness_report.py
```

Add console scripts:

```text
drone-audit-data
drone-run-harness
drone-check-metrics
drone-loop-report
```

The existing commands stay intact:

- `drone-convert`
- `drone-train`
- `drone-val`
- `drone-detect`

The new harness calls or mirrors those flows instead of duplicating YOLO-specific
behavior.

## Experiment Configuration

`configs/experiments/baseline_yolov8n.yaml` defines one experiment contract:

```yaml
experiment:
  name: baseline_yolov8n
  description: YOLOv8n VisDrone baseline loop

data:
  root: data
  dataset_yaml: data.yaml
  splits: [train, val]
  image_ext: jpg
  require_labels: true

model:
  weights: yolov8n.pt

train:
  enabled: true
  epochs: 10
  batch: 8
  imgsz: 640
  device: cpu
  workers: 4
  patience: 50

val:
  enabled: true
  batch: 8
  imgsz: 640
  device: cpu
  conf: 0.001
  iou: 0.6

gates:
  map50_min: 0.258
  map_min: 0.147
  precision_min: 0.354
  recall_min: 0.274
  allowed_drop: 0.02

outputs:
  root: runs/harness
```

The parser should use the standard library when practical. If YAML parsing requires
PyYAML, it can be added as a small dependency. The implementation should keep the
schema explicit and fail with actionable error messages when required fields are
missing or types are invalid.

## Data Audit

`drone-audit-data` checks whether the local dataset is ready for the loop.

Inputs:

- `--config configs/experiments/baseline_yolov8n.yaml`
- optional `--data-root`
- optional `--format json|markdown`
- optional `--output path`

Checks:

- Expected split directories exist.
- `images/` exists for each split.
- `annotations/` exists when raw VisDrone annotations are expected.
- `labels/` exists when converted labels are required.
- Image count and label count per split.
- Missing labels for images.
- Empty label files.
- Invalid YOLO rows: wrong column count, non-numeric values, class ID outside 0-9,
  normalized box values outside 0-1, non-positive width or height.
- Class distribution across label files.

Outputs:

- JSON summary for automation.
- Markdown summary for humans.

Exit behavior:

- Exit 0 when the dataset passes required checks.
- Exit non-zero when required directories are missing or invalid labels are found.
- Warnings such as empty labels should be reported but configurable as non-fatal.

## Harness Runner

`drone-run-harness` is the single command for an experiment cycle.

Inputs:

- `--config configs/experiments/baseline_yolov8n.yaml`
- `--stage audit|convert|train|val|report|all`
- `--dry-run`
- `--skip-train`
- `--model path/to/best.pt`

Behavior:

1. Load and validate the experiment config.
2. Create a timestamped run directory under `runs/harness/<experiment>/<timestamp>/`.
3. Copy the resolved config into the run directory.
4. Run data audit.
5. Optionally convert raw VisDrone annotations to YOLO labels.
6. Optionally train using the existing `src.train` flow.
7. Validate using the existing `src.val` flow or a supplied model path.
8. Check metric gates.
9. Generate a loop report.

The first implementation may use subprocess calls to existing CLI entry points where
that keeps behavior closest to the current project. Shared pure logic should live in
small functions so it remains unit-testable.

## Metric Gates

`drone-check-metrics` compares observed metrics to configured thresholds.

Inputs:

- `--config configs/experiments/baseline_yolov8n.yaml`
- `--metrics path/to/metrics.json`
- optional direct values: `--map50`, `--map`, `--precision`, `--recall`

Metrics:

- `precision`
- `recall`
- `map50`
- `map`

Gate behavior:

- Pass if every configured metric is at or above its minimum after applying
  `allowed_drop`.
- Fail with a clear per-metric table if any metric is below the gate.
- Exit non-zero on gate failure so this can be used in local automation.

The checker should support both current baseline values and future experiments with
different threshold files.

## Loop Report

`drone-loop-report` generates a Markdown report for each iteration.

Report sections:

- Experiment identity and timestamp.
- Data audit summary.
- Training and validation command summary.
- Metric table with pass/fail gates.
- Artifact locations.
- Observed risks and missing resources.
- Suggested next experiments.

Suggested next experiments should be deterministic and rule-based in this phase, for
example:

- Low recall: try lower confidence threshold, more epochs, larger image size, or
  class imbalance review.
- Low precision: inspect false positives and raise confidence threshold.
- Weak small-object classes: increase image size or add targeted augmentation.
- Missing labels or invalid boxes: fix conversion/data quality before training.

No LLM API or external service is required.

## Error Handling

Errors should be specific and actionable:

- Missing data root: say which path is missing and how to create the expected layout.
- Missing labels: suggest running `drone-convert`.
- Missing model for validation: suggest `--model path/to/best.pt` or running training.
- Invalid config: include field name and expected type.
- Metric gate failure: print the exact metric, observed value, required value, and
  difference.

Commands should avoid stack traces for expected user errors. Unexpected errors can
still surface normally during development.

## Testing

Tests must remain lightweight.

Add unit tests for:

- Loading valid experiment config.
- Rejecting config with missing required fields.
- Auditing a tiny synthetic VisDrone-like directory.
- Detecting missing labels and invalid YOLO rows.
- Passing and failing metric gates.
- Rendering a loop report with all required sections.

Do not test real YOLO training, real VisDrone data, downloaded weights, or GPU
execution in CI.

Existing tests must keep passing:

```bash
python3 -m pytest tests/ --tb=short -q
```

Recommended verification after implementation:

```bash
make test
make lint
make format
```

## Documentation

Update README and add `docs/harness_loop.md` with:

- What harness engineering means in this project.
- What loop engineering means in this project.
- Quick commands for audit, dry-run, validation-only, and full local loop.
- Required resources for real training.
- Expected output directories.
- How to interpret metric gate failures.

The docs should be bilingual-friendly with concise Chinese explanations, matching the
current README style.

## Resource Needs

Implementation and CI tests do not require extra resources.

To run the real loop, the user must provide:

- VisDrone2019-DET dataset in the documented `data/` layout.
- A local Python environment with project dependencies installed.
- A trained `best.pt` for validation-only loops, or enough CPU/GPU time to train.

GPU is optional. The default config stays CPU-safe, matching the current baseline.

## Success Criteria

The work is complete when:

- The project has a committed experiment config.
- New harness CLIs install through `pyproject.toml`.
- A synthetic dataset audit can run in tests.
- Metric gates can pass and fail deterministically.
- A loop report can be generated without real data or YOLO weights.
- README or docs explain the complete loop.
- Existing tests and new tests pass locally.
