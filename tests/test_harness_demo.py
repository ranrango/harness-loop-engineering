from __future__ import annotations

import importlib
import importlib.util
import json


def test_demo_loop_generates_traceable_run(tmp_path):
    spec = importlib.util.find_spec("src.harness.demo")
    assert spec is not None, "src.harness.demo module should provide a self-contained demo"
    demo = importlib.import_module("src.harness.demo")

    result = demo.create_demo_loop(output_root=tmp_path, timestamp="20260705_120000")

    assert result.run_dir == tmp_path / "harness_loop_demo" / "20260705_120000"
    assert result.report_path == result.run_dir / "loop_report.md"
    assert (result.run_dir / "resolved_config.yaml").is_file()
    assert (result.run_dir / "audit.json").is_file()
    assert (result.run_dir / "metrics.json").is_file()
    assert (result.run_dir / "commands.txt").is_file()
    assert result.report_path.is_file()

    audit = json.loads((result.run_dir / "audit.json").read_text(encoding="utf-8"))
    assert audit["ok"] is True
    assert audit["error_count"] == 0

    commands = (result.run_dir / "commands.txt").read_text(encoding="utf-8")
    assert "drone-audit-data" in commands
    assert "drone-check-metrics" in commands
    assert "drone-loop-report" in commands

    report = result.report_path.read_text(encoding="utf-8")
    assert "# Harness Loop Report" in report
    assert "## Artifacts" in report
    assert "`" + str(result.run_dir / "demo_data") + "`" in report
    assert "`" + str(result.run_dir / "commands.txt") + "`" in report
    assert "指标达到当前门槛" in report


def test_demo_loop_supports_metric_profiles(tmp_path):
    demo = importlib.import_module("src.harness.demo")

    baseline = demo.create_demo_loop(
        output_root=tmp_path,
        timestamp="baseline",
        profile="baseline",
    )
    improved = demo.create_demo_loop(
        output_root=tmp_path,
        timestamp="improved",
        profile="improved",
    )

    baseline_metrics = json.loads((baseline.run_dir / "metrics.json").read_text(encoding="utf-8"))
    improved_metrics = json.loads((improved.run_dir / "metrics.json").read_text(encoding="utf-8"))

    assert improved_metrics["map50"] > baseline_metrics["map50"]
    assert improved_metrics["recall"] > baseline_metrics["recall"]
