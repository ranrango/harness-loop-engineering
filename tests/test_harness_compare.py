from __future__ import annotations

import importlib
import importlib.util
import json
import sys

from src.harness.demo import create_demo_loop


def test_compare_runs_renders_metric_deltas_and_decision(tmp_path):
    spec = importlib.util.find_spec("src.harness.compare")
    assert spec is not None, "src.harness.compare should compare two loop runs"
    compare = importlib.import_module("src.harness.compare")

    base = create_demo_loop(output_root=tmp_path, timestamp="baseline", profile="baseline")
    candidate = create_demo_loop(output_root=tmp_path, timestamp="candidate", profile="improved")

    comparison = compare.compare_runs(
        base_run=base.run_dir,
        candidate_run=candidate.run_dir,
        min_delta=0.005,
    )
    report = compare.render_comparison_report(comparison)

    assert "# Harness Loop Comparison" in report
    assert "| map50 | 0.2900 | 0.3300 | +0.0400 | IMPROVED |" in report
    assert "| recall | 0.3100 | 0.3500 | +0.0400 | IMPROVED |" in report
    assert "候选 run 整体改善" in report


def test_compare_runs_flags_regression(tmp_path):
    compare = importlib.import_module("src.harness.compare")
    base = create_demo_loop(output_root=tmp_path, timestamp="baseline", profile="baseline")
    candidate = create_demo_loop(output_root=tmp_path, timestamp="candidate", profile="regressed")

    comparison = compare.compare_runs(
        base_run=base.run_dir,
        candidate_run=candidate.run_dir,
        min_delta=0.005,
    )

    assert any(item.status == "REGRESSED" for item in comparison.metrics)
    assert any("回滚" in item for item in comparison.recommendations)


def test_compare_main_writes_output_file(tmp_path, monkeypatch):
    compare = importlib.import_module("src.harness.compare")
    base = create_demo_loop(output_root=tmp_path, timestamp="baseline", profile="baseline")
    candidate = create_demo_loop(output_root=tmp_path, timestamp="candidate", profile="improved")
    output = tmp_path / "comparison.md"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "drone-compare-runs",
            "--base-run",
            str(base.run_dir),
            "--candidate-run",
            str(candidate.run_dir),
            "--output",
            str(output),
        ],
    )

    compare.main()

    assert output.is_file()
    assert "## Loop Decision" in output.read_text(encoding="utf-8")


def test_compare_main_writes_machine_readable_json_output(tmp_path, monkeypatch):
    compare = importlib.import_module("src.harness.compare")
    base = create_demo_loop(output_root=tmp_path, timestamp="baseline", profile="baseline")
    candidate = create_demo_loop(output_root=tmp_path, timestamp="candidate", profile="improved")
    report_output = tmp_path / "comparison.md"
    json_output = tmp_path / "comparison.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "drone-compare-runs",
            "--base-run",
            str(base.run_dir),
            "--candidate-run",
            str(candidate.run_dir),
            "--output",
            str(report_output),
            "--json-output",
            str(json_output),
        ],
    )

    compare.main()

    payload = json.loads(json_output.read_text(encoding="utf-8"))
    assert payload["base"]["run_dir"] == str(base.run_dir)
    assert payload["candidate"]["run_dir"] == str(candidate.run_dir)
    assert payload["candidate"]["audit"]["ok"] is True
    assert payload["metrics"]["map50"]["delta"] == 0.04
    assert payload["metrics"]["map50"]["status"] == "IMPROVED"
    assert payload["loop_decision"][0].startswith("候选 run 整体改善")
