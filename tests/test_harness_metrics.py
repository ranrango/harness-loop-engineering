from __future__ import annotations

import json

from src.harness.config import load_experiment_config
from src.harness.metrics import check_metric_gates, load_metrics, render_gate_table


def test_metric_gates_pass_with_baseline_values():
    config = load_experiment_config("configs/experiments/baseline_yolov8n.yaml")
    report = check_metric_gates(
        config,
        {"precision": 0.354, "recall": 0.274, "map50": 0.258, "map": 0.147},
    )

    assert report.ok is True
    assert all(result.passed for result in report.results)


def test_metric_gates_allow_configured_drop():
    config = load_experiment_config("configs/experiments/baseline_yolov8n.yaml")
    report = check_metric_gates(
        config,
        {"precision": 0.334, "recall": 0.254, "map50": 0.238, "map": 0.127},
    )

    assert report.ok is True


def test_metric_gates_fail_below_allowed_drop():
    config = load_experiment_config("configs/experiments/baseline_yolov8n.yaml")
    report = check_metric_gates(
        config,
        {"precision": 0.20, "recall": 0.274, "map50": 0.258, "map": 0.147},
    )

    assert report.ok is False
    failed = [result for result in report.results if not result.passed]
    assert failed[0].name == "precision"


def test_load_metrics_from_json(tmp_path):
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(
        json.dumps({"precision": 0.4, "recall": 0.3, "map50": 0.27, "map": 0.15}),
        encoding="utf-8",
    )

    metrics = load_metrics(metrics_path)

    assert metrics["map50"] == 0.27


def test_render_gate_table_contains_failure_status():
    config = load_experiment_config("configs/experiments/baseline_yolov8n.yaml")
    report = check_metric_gates(
        config,
        {"precision": 0.20, "recall": 0.274, "map50": 0.258, "map": 0.147},
    )
    table = render_gate_table(report)

    assert "precision" in table
    assert "FAIL" in table
