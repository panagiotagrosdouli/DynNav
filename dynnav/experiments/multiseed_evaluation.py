"""Reproducible multi-seed evaluation for recoverability-aware navigation."""
from __future__ import annotations

import csv
import json
import math
import random
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from dynnav.experiments.statistics import bootstrap_mean_interval, paired_effect, summarize


@dataclass(frozen=True)
class TrialRecord:
    seed: int
    method: str
    success: bool
    irreversible_failure: bool
    path_length: float
    planning_time_ms: float
    nodes_expanded: float
    cumulative_risk: float
    cumulative_irreversibility: float
    minimum_escape_options: float
    planning_failure: bool = False


@dataclass(frozen=True)
class EvaluationConfig:
    seeds: tuple[int, ...] = tuple(range(30))
    confidence: float = 0.95
    bootstrap_resamples: int = 2000

    def validate(self) -> None:
        if not self.seeds:
            raise ValueError("at least one seed is required")
        if len(set(self.seeds)) != len(self.seeds):
            raise ValueError("seeds must be unique")
        if not 0.0 < self.confidence < 1.0:
            raise ValueError("confidence must be in (0, 1)")
        if self.bootstrap_resamples < 100:
            raise ValueError("bootstrap_resamples must be at least 100")


TrialRunner = Callable[[int, str, Mapping[str, float]], TrialRecord]


def run_multiseed(
    runner: TrialRunner,
    methods: Sequence[str],
    *,
    parameters: Mapping[str, float] | None = None,
    config: EvaluationConfig | None = None,
) -> list[TrialRecord]:
    cfg = config or EvaluationConfig()
    cfg.validate()
    if not methods or len(set(methods)) != len(methods):
        raise ValueError("methods must be a non-empty unique sequence")
    params = dict(parameters or {})
    records: list[TrialRecord] = []
    for seed in cfg.seeds:
        random.seed(seed)
        for method in methods:
            record = runner(seed, method, params)
            if record.seed != seed or record.method != method:
                raise ValueError("runner returned mismatched seed or method")
            records.append(record)
    return records


def aggregate(
    records: Iterable[TrialRecord], *, config: EvaluationConfig | None = None
) -> dict[str, dict]:
    """Aggregate trials without silently replacing undefined failure metrics.

    Planner failures can legitimately produce non-finite path-dependent metrics
    such as cumulative risk. Those trials remain in the binary outcome rates,
    while each continuous metric reports exactly how many finite observations
    contributed to its descriptive statistics and interval.
    """

    cfg = config or EvaluationConfig()
    cfg.validate()
    grouped: dict[str, list[TrialRecord]] = {}
    for record in records:
        grouped.setdefault(record.method, []).append(record)
    output: dict[str, dict] = {}
    metrics = (
        "path_length",
        "planning_time_ms",
        "nodes_expanded",
        "cumulative_risk",
        "cumulative_irreversibility",
        "minimum_escape_options",
    )
    for method, rows in sorted(grouped.items()):
        summary: dict[str, object] = {
            "trials": len(rows),
            "success_rate": sum(row.success for row in rows) / len(rows),
            "planning_failure_rate": sum(row.planning_failure for row in rows)
            / len(rows),
            "irreversible_failure_rate": sum(row.irreversible_failure for row in rows) / len(rows),
        }
        for metric in metrics:
            raw_values = [float(getattr(row, metric)) for row in rows]
            values = [value for value in raw_values if math.isfinite(value)]
            excluded = len(raw_values) - len(values)
            if values:
                interval = bootstrap_mean_interval(
                    values,
                    confidence=cfg.confidence,
                    resamples=cfg.bootstrap_resamples,
                    seed=sum(row.seed for row in rows) + len(metric),
                )
                metric_summary: dict[str, object] = {
                    "summary": summarize(values),
                    "mean_interval": asdict(interval),
                    "finite_trials": len(values),
                    "excluded_non_finite": excluded,
                }
            else:
                metric_summary = {
                    "summary": None,
                    "mean_interval": None,
                    "finite_trials": 0,
                    "excluded_non_finite": excluded,
                }
            summary[metric] = metric_summary
        output[method] = summary
    return output


def paired_comparisons(
    records: Iterable[TrialRecord],
    baseline: str,
    proposed: str,
    *,
    metric: str = "planning_time_ms",
    config: EvaluationConfig | None = None,
) -> dict:
    """Compute a paired effect using only pairs where the metric is defined.

    Pair exclusion is reported explicitly so failed/undefined observations can
    never disappear from an analysis without an auditable count.
    """

    cfg = config or EvaluationConfig()
    cfg.validate()
    by_key = {(row.seed, row.method): row for row in records}
    common = sorted(
        seed
        for seed, method in by_key
        if method == baseline and (seed, proposed) in by_key
    )
    if not common:
        raise ValueError("no paired seeds available")

    finite_common: list[int] = []
    for seed in common:
        left_value = float(getattr(by_key[(seed, baseline)], metric))
        right_value = float(getattr(by_key[(seed, proposed)], metric))
        if math.isfinite(left_value) and math.isfinite(right_value):
            finite_common.append(seed)

    if not finite_common:
        raise ValueError(f"no finite paired observations available for metric {metric!r}")

    left = [float(getattr(by_key[(seed, baseline)], metric)) for seed in finite_common]
    right = [float(getattr(by_key[(seed, proposed)], metric)) for seed in finite_common]
    result = asdict(
        paired_effect(
            left,
            right,
            confidence=cfg.confidence,
            resamples=cfg.bootstrap_resamples,
            seed=sum(finite_common) + len(metric),
        )
    )
    result["paired_trials"] = len(finite_common)
    result["excluded_non_finite_pairs"] = len(common) - len(finite_common)
    return result


def sensitivity_grid(
    runner: TrialRunner,
    method: str,
    parameter: str,
    values: Sequence[float],
    *,
    config: EvaluationConfig | None = None,
) -> dict[str, dict]:
    if not values:
        raise ValueError("sensitivity values cannot be empty")
    result: dict[str, dict] = {}
    for value in values:
        records = run_multiseed(
            runner,
            [method],
            parameters={parameter: float(value)},
            config=config,
        )
        result[str(value)] = aggregate(records, config=config)[method]
    return result


def write_artifacts(
    records: Sequence[TrialRecord], summary: Mapping, output_dir: str | Path
) -> None:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    with (target / "trials.csv").open("w", newline="", encoding="utf-8") as handle:
        fieldnames = (
            list(asdict(records[0]).keys())
            if records
            else [field.name for field in TrialRecord.__dataclass_fields__.values()]
        )
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(asdict(record))
    with (target / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
