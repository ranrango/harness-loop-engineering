"""Compare two Harness/Loop run directories."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from src.harness.metrics import load_metrics
from src.harness.report import load_commands_file

METRIC_ORDER = ("precision", "recall", "map50", "map")


@dataclass(frozen=True)
class RunSnapshot:
    run_dir: Path
    audit_ok: bool
    error_count: int
    warning_count: int
    metrics: dict[str, float]
    commands: list[str]


@dataclass(frozen=True)
class MetricDelta:
    name: str
    base: float
    candidate: float
    delta: float
    status: str


@dataclass(frozen=True)
class RunComparison:
    base: RunSnapshot
    candidate: RunSnapshot
    metrics: list[MetricDelta]
    recommendations: list[str]


def load_run_snapshot(run_dir: str | Path) -> RunSnapshot:
    base = Path(run_dir)
    audit = json.loads((base / "audit.json").read_text(encoding="utf-8"))
    return RunSnapshot(
        run_dir=base,
        audit_ok=bool(audit["ok"]),
        error_count=int(audit["error_count"]),
        warning_count=int(audit["warning_count"]),
        metrics=load_metrics(base / "metrics.json"),
        commands=load_commands_file(base / "commands.txt"),
    )


def compare_runs(
    base_run: str | Path,
    candidate_run: str | Path,
    min_delta: float = 0.005,
) -> RunComparison:
    base = load_run_snapshot(base_run)
    candidate = load_run_snapshot(candidate_run)
    deltas = [
        _metric_delta(name, base.metrics[name], candidate.metrics[name], min_delta)
        for name in METRIC_ORDER
        if name in base.metrics and name in candidate.metrics
    ]
    return RunComparison(
        base=base,
        candidate=candidate,
        metrics=deltas,
        recommendations=recommend_next_loop(base, candidate, deltas),
    )


def recommend_next_loop(
    base: RunSnapshot,
    candidate: RunSnapshot,
    deltas: list[MetricDelta],
) -> list[str]:
    if base.audit_ok and not candidate.audit_ok:
        return ["候选 run 数据审计失败：先修复数据质量，不要把它提升为新 baseline。"]
    if any(item.status == "REGRESSED" for item in deltas):
        return ["候选 run 出现指标退化：建议回滚或复查本轮配置、数据和阈值变化。"]
    if deltas and all(item.status in {"IMPROVED", "STABLE"} for item in deltas):
        if any(item.status == "IMPROVED" for item in deltas):
            return ["候选 run 整体改善：可以把它作为下一轮 baseline，并继续做错误样本分析。"]
    return ["候选 run 变化不明显：继续收集失败样本，或一次只调整一个实验变量。"]


def render_comparison_report(comparison: RunComparison) -> str:
    lines = [
        "# Harness Loop Comparison",
        "",
        f"- Base run: `{comparison.base.run_dir}`",
        f"- Candidate run: `{comparison.candidate.run_dir}`",
        "",
        "## Data Audit",
        "",
        "| run | status | errors | warnings |",
        "| --- | --- | ---: | ---: |",
        _audit_row("base", comparison.base),
        _audit_row("candidate", comparison.candidate),
        "",
        "## Metric Deltas",
        "",
        "| metric | base | candidate | delta | status |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for item in comparison.metrics:
        lines.append(
            f"| {item.name} | {item.base:.4f} | {item.candidate:.4f} | "
            f"{item.delta:+.4f} | {item.status} |"
        )
    lines.extend(["", "## Candidate Commands", ""])
    if comparison.candidate.commands:
        lines.extend(f"- `{command}`" for command in comparison.candidate.commands)
    else:
        lines.append("- No commands recorded.")
    lines.extend(["", "## Loop Decision", ""])
    lines.extend(f"- {item}" for item in comparison.recommendations)
    return "\n".join(lines).rstrip() + "\n"


def _metric_delta(name: str, base: float, candidate: float, min_delta: float) -> MetricDelta:
    delta = candidate - base
    if delta >= min_delta:
        status = "IMPROVED"
    elif delta <= -min_delta:
        status = "REGRESSED"
    else:
        status = "STABLE"
    return MetricDelta(name=name, base=base, candidate=candidate, delta=delta, status=status)


def _audit_row(label: str, snapshot: RunSnapshot) -> str:
    status = "PASS" if snapshot.audit_ok else "FAIL"
    return f"| {label} | {status} | {snapshot.error_count} | {snapshot.warning_count} |"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare two Harness/Loop run directories.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--base-run", required=True)
    parser.add_argument("--candidate-run", required=True)
    parser.add_argument("--min-delta", type=float, default=0.005)
    parser.add_argument("--output", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = render_comparison_report(
        compare_runs(
            base_run=args.base_run,
            candidate_run=args.candidate_run,
            min_delta=args.min_delta,
        )
    )
    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
