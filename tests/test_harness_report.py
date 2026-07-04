from __future__ import annotations

from src.harness.audit_data import DatasetAudit, SplitAudit
from src.harness.config import load_experiment_config
from src.harness.metrics import check_metric_gates
from src.harness.report import LoopReportInput, render_loop_report, suggest_next_experiments


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
