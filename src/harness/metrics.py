"""Metric gate checking for experiment loops."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from src.harness.config import ExperimentConfig, load_experiment_config


FLOAT_TOLERANCE = 1e-12


@dataclass(frozen=True)
class MetricGateResult:
    name: str
    observed: float
    minimum: float
    allowed_drop: float
    required: float
    delta: float
    passed: bool


@dataclass(frozen=True)
class MetricGateReport:
    ok: bool
    results: list[MetricGateResult]


def load_metrics(path: str | Path) -> dict[str, float]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("metrics JSON must be an object")
    metrics: dict[str, float] = {}
    for key in ("precision", "recall", "map50", "map"):
        if key in raw:
            value = raw[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{key} must be numeric")
            metrics[key] = float(value)
    return metrics


def check_metric_gates(config: ExperimentConfig, metrics: dict[str, float]) -> MetricGateReport:
    results: list[MetricGateResult] = []
    for name, minimum in config.gates.thresholds().items():
        if name not in metrics:
            raise ValueError(f"missing metric: {name}")
        observed = float(metrics[name])
        required = minimum - config.gates.allowed_drop
        delta = observed - required
        results.append(
            MetricGateResult(
                name=name,
                observed=observed,
                minimum=minimum,
                allowed_drop=config.gates.allowed_drop,
                required=required,
                delta=delta,
                passed=observed + FLOAT_TOLERANCE >= required,
            )
        )
    return MetricGateReport(ok=all(result.passed for result in results), results=results)


def gate_report_to_dict(report: MetricGateReport) -> dict[str, Any]:
    return asdict(report)


def render_gate_table(report: MetricGateReport) -> str:
    lines = [
        "| metric | observed | minimum | allowed_drop | required | delta | status |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for result in report.results:
        lines.append(
            f"| {result.name} | {result.observed:.4f} | {result.minimum:.4f} | "
            f"{result.allowed_drop:.4f} | {result.required:.4f} | {result.delta:.4f} | "
            f"{'PASS' if result.passed else 'FAIL'} |"
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check validation metrics against experiment gates.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--config", default="configs/experiments/baseline_yolov8n.yaml")
    parser.add_argument("--metrics", default=None)
    parser.add_argument("--map50", type=float, default=None)
    parser.add_argument("--map", type=float, default=None)
    parser.add_argument("--precision", type=float, default=None)
    parser.add_argument("--recall", type=float, default=None)
    parser.add_argument("--json", action="store_true", help="Print machine-readable gate report.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_experiment_config(args.config)
    metrics = load_metrics(args.metrics) if args.metrics else {}
    direct = {
        "precision": args.precision,
        "recall": args.recall,
        "map50": args.map50,
        "map": args.map,
    }
    metrics.update({key: value for key, value in direct.items() if value is not None})
    report = check_metric_gates(config, metrics)
    if args.json:
        print(json.dumps(gate_report_to_dict(report), ensure_ascii=False, indent=2))
    else:
        print(render_gate_table(report))
    raise SystemExit(0 if report.ok else 1)


if __name__ == "__main__":
    main()
