"""Experiment harness runner orchestration."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from src.harness.config import ExperimentConfig, load_experiment_config

VALID_STAGES = {"audit", "convert", "train", "val", "report", "all"}


def create_run_dir(
    config: ExperimentConfig,
    outputs_root: str | Path | None = None,
    timestamp: str | None = None,
) -> Path:
    root = Path(outputs_root) if outputs_root is not None else config.outputs.root
    stamp = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = root / config.experiment.name / stamp
    run_dir.mkdir(parents=True, exist_ok=False)
    shutil.copy2(config.path, run_dir / "resolved_config.yaml")
    return run_dir


def build_stage_commands(
    config: ExperimentConfig,
    stage: str,
    run_dir: Path,
    skip_train: bool,
    model_path: str | None,
) -> list[list[str]]:
    if stage not in VALID_STAGES:
        raise ValueError(f"invalid stage: {stage}")
    commands: list[list[str]] = []
    if stage in {"audit", "all"}:
        commands.append(
            [
                sys.executable,
                "-m",
                "src.harness.audit_data",
                "--config",
                str(config.path),
                "--format",
                "json",
                "--output",
                str(run_dir / "audit.json"),
            ]
        )
    if stage in {"convert", "all"}:
        commands.append(
            [
                sys.executable,
                "scripts/convert_visdrone_to_yolo.py",
                "--data-root",
                str(config.data.root),
                "--splits",
                *config.data.splits,
                "--img-ext",
                config.data.image_ext,
            ]
        )
    if stage in {"train", "all"} and config.train.enabled and not skip_train:
        commands.append(
            [
                sys.executable,
                "-m",
                "src.train",
                "--model",
                config.model.weights,
                "--data",
                str(config.data.dataset_yaml),
                "--epochs",
                str(config.train.epochs),
                "--batch",
                str(config.train.batch),
                "--imgsz",
                str(config.train.imgsz),
                "--device",
                config.train.device,
                "--project",
                str(run_dir / "detect"),
                "--workers",
                str(config.train.workers),
                "--patience",
                str(config.train.patience),
            ]
        )
    resolved_model = model_path
    if resolved_model is None and not skip_train:
        resolved_model = str(run_dir / "detect" / "train" / "weights" / "best.pt")
    if stage in {"val", "all"} and config.val.enabled:
        if resolved_model is None:
            raise ValueError("validation requires --model when --skip-train is used")
        commands.append(
            [
                sys.executable,
                "-m",
                "src.val",
                "--model",
                resolved_model,
                "--data",
                str(config.data.dataset_yaml),
                "--imgsz",
                str(config.val.imgsz),
                "--batch",
                str(config.val.batch),
                "--device",
                config.val.device,
                "--conf",
                str(config.val.conf),
                "--iou",
                str(config.val.iou),
                "--project",
                str(run_dir / "detect"),
            ]
        )
    if stage in {"report", "all"}:
        commands.append(
            [
                sys.executable,
                "-m",
                "src.harness.report",
                "--config",
                str(config.path),
                "--audit-json",
                str(run_dir / "audit.json"),
                "--metrics",
                str(run_dir / "metrics.json"),
                "--timestamp",
                run_dir.name,
                "--output",
                str(run_dir / "loop_report.md"),
            ]
        )
    return commands


def run_harness(
    config_path: str | Path,
    stage: str,
    dry_run: bool,
    skip_train: bool,
    model_path: str | None,
) -> Path:
    config = load_experiment_config(config_path)
    run_dir = create_run_dir(config)
    commands = build_stage_commands(config, stage, run_dir, skip_train, model_path)
    (run_dir / "commands.txt").write_text(
        "\n".join(" ".join(command) for command in commands) + "\n",
        encoding="utf-8",
    )
    if dry_run:
        for command in commands:
            print(" ".join(command))
        return run_dir
    for command in commands:
        subprocess.run(command, check=True)
    return run_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the configured experiment harness loop.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--config", default="configs/experiments/baseline_yolov8n.yaml")
    parser.add_argument("--stage", choices=sorted(VALID_STAGES), default="all")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-train", action="store_true")
    parser.add_argument("--model", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_dir = run_harness(
        config_path=args.config,
        stage=args.stage,
        dry_run=args.dry_run,
        skip_train=args.skip_train,
        model_path=args.model,
    )
    print(f"Harness run directory: {run_dir}")


if __name__ == "__main__":
    main()
