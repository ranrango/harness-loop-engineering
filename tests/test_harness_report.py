from __future__ import annotations

import json
import sys

from src.harness import report as harness_report
from src.harness.audit_data import DatasetAudit, SplitAudit, audit_to_dict
from src.harness.config import load_experiment_config
from src.harness.metrics import check_metric_gates
from src.harness.report import (
    LoopReportInput,
    render_loop_report,
    suggest_next_experiments,
)


def sample_audit(ok: bool = True) -> DatasetAudit:
    return DatasetAudit(
        data_root="data",
        ok=ok,
        error_count=0 if ok else 1,
        warning_count=0,
        splits=[
            SplitAudit(
                split="train",
                path="data/VisDrone2019-DET-train",
                ok=ok,
                image_count=2,
                label_count=2,
                missing_dirs=[],
                missing_labels=[] if ok else ["img2.txt"],
                empty_labels=[],
                invalid_labels=[],
                class_distribution={3: 2},
            )
        ],
    )


def test_suggestions_for_low_recall():
    suggestions = suggest_next_experiments(
        metrics={"precision": 0.4, "recall": 0.1, "map50": 0.25, "map": 0.14},
        audit_ok=True,
    )

    assert any("召回率" in item for item in suggestions)


def test_suggestions_prioritize_data_quality_when_audit_fails():
    suggestions = suggest_next_experiments(
        metrics={"precision": 0.4, "recall": 0.3, "map50": 0.27, "map": 0.15},
        audit_ok=False,
    )

    assert suggestions[0].startswith("先修复数据质量")


def test_render_loop_report_contains_required_sections():
    config = load_experiment_config("configs/experiments/baseline_yolov8n.yaml")
    metrics = {"precision": 0.354, "recall": 0.274, "map50": 0.258, "map": 0.147}
    gate_report = check_metric_gates(config, metrics)
    report = render_loop_report(
        LoopReportInput(
            experiment_name=config.experiment.name,
            timestamp="20260704_120000",
            audit=sample_audit(),
            metrics=metrics,
            gate_report=gate_report,
            commands=["python3 -m src.train --epochs 10"],
            artifacts=["runs/harness/baseline_yolov8n/20260704_120000"],
        )
    )

    assert "# Harness Loop Report" in report
    assert "## Data Audit" in report
    assert "## Metric Gates" in report
    assert "## Next Experiments" in report


def test_load_commands_file_ignores_blank_lines(tmp_path):
    commands_file = tmp_path / "commands.txt"
    commands_file.write_text(
        "\npython3 -m src.harness.audit_data --config config.yaml\n\n"
        "python3 -m src.val --metrics-output metrics.json\n",
        encoding="utf-8",
    )

    assert harness_report.load_commands_file(commands_file) == [
        "python3 -m src.harness.audit_data --config config.yaml",
        "python3 -m src.val --metrics-output metrics.json",
    ]


def test_resolve_report_paths_from_run_dir(tmp_path):
    run_dir = tmp_path / "baseline_yolov8n" / "20260705_120000"
    run_dir.mkdir(parents=True)

    paths = harness_report.resolve_report_paths(run_dir=run_dir)

    assert paths.audit_json == run_dir / "audit.json"
    assert paths.metrics == run_dir / "metrics.json"
    assert paths.timestamp == "20260705_120000"
    assert paths.output == run_dir / "loop_report.md"
    assert paths.commands_file == run_dir / "commands.txt"
    assert paths.artifacts == [
        str(run_dir / "resolved_config.yaml"),
        str(run_dir / "audit.json"),
        str(run_dir / "metrics.json"),
        str(run_dir / "commands.txt"),
        str(run_dir / "loop_report.md"),
    ]


def test_main_generates_report_from_run_dir(tmp_path, monkeypatch):
    run_dir = tmp_path / "baseline_yolov8n" / "20260705_120000"
    run_dir.mkdir(parents=True)
    (run_dir / "audit.json").write_text(
        json.dumps(audit_to_dict(sample_audit()), ensure_ascii=False),
        encoding="utf-8",
    )
    (run_dir / "metrics.json").write_text(
        json.dumps({"precision": 0.354, "recall": 0.274, "map50": 0.258, "map": 0.147}),
        encoding="utf-8",
    )
    (run_dir / "commands.txt").write_text(
        "python3 -m src.harness.audit_data --config config.yaml\n"
        "python3 -m src.val --metrics-output metrics.json\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "drone-loop-report",
            "--config",
            "configs/experiments/baseline_yolov8n.yaml",
            "--run-dir",
            str(run_dir),
        ],
    )

    harness_report.main()

    report_text = (run_dir / "loop_report.md").read_text(encoding="utf-8")
    assert "python3 -m src.harness.audit_data --config config.yaml" in report_text
    assert f"`{run_dir / 'commands.txt'}`" in report_text
    assert f"`{run_dir / 'loop_report.md'}`" in report_text
