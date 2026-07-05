"""Loop report rendering and rule-based next experiment suggestions."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from src.harness.audit_data import DatasetAudit, SplitAudit, render_audit_markdown
from src.harness.config import load_experiment_config
from src.harness.metrics import (
    MetricGateReport,
    check_metric_gates,
    load_metrics,
    render_gate_table,
)


@dataclass(frozen=True)
class LoopReportInput:
    experiment_name: str
    timestamp: str
    audit: DatasetAudit
    metrics: dict[str, float]
    gate_report: MetricGateReport
    commands: list[str]
    artifacts: list[str]


@dataclass(frozen=True)
class ReportPaths:
    audit_json: Path
    metrics: Path
    timestamp: str
    output: Path
    commands_file: Path | None
    artifacts: list[str]


DEFAULT_REPORT_ARTIFACTS = (
    "resolved_config.yaml",
    "audit.json",
    "metrics.json",
    "commands.txt",
    "loop_report.md",
)


def load_commands_file(path: str | Path | None) -> list[str]:
    if path is None:
        return []
    return [
        line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def resolve_report_paths(
    *,
    run_dir: str | Path | None = None,
    audit_json: str | Path | None = None,
    metrics: str | Path | None = None,
    timestamp: str | None = None,
    output: str | Path | None = None,
    commands_file: str | Path | None = None,
    artifacts: list[str] | None = None,
) -> ReportPaths:
    if run_dir is not None:
        base = Path(run_dir)
        resolved_artifacts = artifacts or [
            str(base / artifact_name) for artifact_name in DEFAULT_REPORT_ARTIFACTS
        ]
        return ReportPaths(
            audit_json=Path(audit_json) if audit_json is not None else base / "audit.json",
            metrics=Path(metrics) if metrics is not None else base / "metrics.json",
            timestamp=timestamp or base.name,
            output=Path(output) if output is not None else base / "loop_report.md",
            commands_file=(
                Path(commands_file) if commands_file is not None else base / "commands.txt"
            ),
            artifacts=list(resolved_artifacts),
        )

    missing = [
        name
        for name, value in (
            ("--audit-json", audit_json),
            ("--metrics", metrics),
            ("--timestamp", timestamp),
            ("--output", output),
        )
        if value is None
    ]
    if missing:
        raise ValueError("provide --run-dir or set required report inputs: " + ", ".join(missing))
    return ReportPaths(
        audit_json=Path(audit_json),
        metrics=Path(metrics),
        timestamp=str(timestamp),
        output=Path(output),
        commands_file=Path(commands_file) if commands_file is not None else None,
        artifacts=list(artifacts or []),
    )


def suggest_next_experiments(metrics: dict[str, float], audit_ok: bool) -> list[str]:
    if not audit_ok:
        return ["先修复数据质量：补齐缺失标签、清理无效 YOLO 行，然后再训练。"]
    suggestions: list[str] = []
    if metrics.get("recall", 1.0) < 0.28:
        suggestions.append(
            "召回率偏低：尝试降低置信度阈值、增加 epoch、增大 imgsz 或检查类别不平衡。"
        )
    if metrics.get("precision", 1.0) < 0.35:
        suggestions.append("精确率偏低：抽查误检样本，并尝试提高 conf 或加强负样本覆盖。")
    if metrics.get("map50", 1.0) < 0.26 or metrics.get("map", 1.0) < 0.15:
        suggestions.append("mAP 偏低：优先复核小目标类别，尝试 imgsz=960 或更强数据增强。")
    if not suggestions:
        suggestions.append("指标达到当前门槛：可以尝试 yolov8s、更多 epoch 或验证集错误样本分析。")
    return suggestions


def render_loop_report(data: LoopReportInput) -> str:
    lines = [
        "# Harness Loop Report",
        "",
        f"- Experiment: `{data.experiment_name}`",
        f"- Timestamp: `{data.timestamp}`",
        "",
        "## Data Audit",
        "",
        render_audit_markdown(data.audit).strip(),
        "",
        "## Commands",
        "",
    ]
    if data.commands:
        lines.extend(f"- `{command}`" for command in data.commands)
    else:
        lines.append("- No commands recorded.")
    lines.extend(
        [
            "",
            "## Metrics",
            "",
            "| metric | value |",
            "| --- | ---: |",
        ]
    )
    for name in ("precision", "recall", "map50", "map"):
        if name in data.metrics:
            lines.append(f"| {name} | {data.metrics[name]:.4f} |")
    lines.extend(
        [
            "",
            "## Metric Gates",
            "",
            render_gate_table(data.gate_report),
            "",
            "## Artifacts",
            "",
        ]
    )
    if data.artifacts:
        lines.extend(f"- `{artifact}`" for artifact in data.artifacts)
    else:
        lines.append("- No artifacts recorded.")
    lines.extend(["", "## Risks And Missing Resources", ""])
    if data.audit.ok:
        lines.append("- No blocking data quality issue detected by the audit.")
    else:
        lines.append(
            "- Data audit failed. Fix data quality before trusting training or validation metrics."
        )
    if not data.gate_report.ok:
        lines.append("- One or more metrics failed configured gates.")
    lines.extend(["", "## Next Experiments", ""])
    lines.extend(f"- {item}" for item in suggest_next_experiments(data.metrics, data.audit.ok))
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a Markdown loop report from audit and metric artifacts.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--config", default="configs/experiments/baseline_yolov8n.yaml")
    parser.add_argument("--run-dir", default=None)
    parser.add_argument("--audit-json", default=None)
    parser.add_argument("--metrics", default=None)
    parser.add_argument("--timestamp", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--commands-file", default=None)
    parser.add_argument("--artifact", action="append", default=[])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_experiment_config(args.config)
    try:
        paths = resolve_report_paths(
            run_dir=args.run_dir,
            audit_json=args.audit_json,
            metrics=args.metrics,
            timestamp=args.timestamp,
            output=args.output,
            commands_file=args.commands_file,
            artifacts=args.artifact,
        )
    except ValueError as exc:
        raise SystemExit(f"error: {exc}") from exc
    audit_raw = json.loads(paths.audit_json.read_text(encoding="utf-8"))
    audit = _audit_from_dict(audit_raw)
    metrics = load_metrics(paths.metrics)
    gate_report = check_metric_gates(config, metrics)
    report = render_loop_report(
        LoopReportInput(
            experiment_name=config.experiment.name,
            timestamp=paths.timestamp,
            audit=audit,
            metrics=metrics,
            gate_report=gate_report,
            commands=load_commands_file(paths.commands_file),
            artifacts=paths.artifacts,
        )
    )
    paths.output.write_text(report, encoding="utf-8")


def _audit_from_dict(raw: dict) -> DatasetAudit:
    return DatasetAudit(
        data_root=raw["data_root"],
        ok=raw["ok"],
        error_count=raw["error_count"],
        warning_count=raw["warning_count"],
        splits=[SplitAudit(**split) for split in raw["splits"]],
    )


if __name__ == "__main__":
    main()
