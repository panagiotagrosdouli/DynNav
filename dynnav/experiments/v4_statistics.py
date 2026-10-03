"""V4 held-out analysis utilities.

These functions operate on retained per-trial records.  They do not generate
planner outcomes.  Primary estimands are scenario-weighted paired differences
with hierarchical bootstrap intervals, plus calibration summaries.
"""
from __future__ import annotations

import math
import random
from collections import defaultdict
from dataclasses import dataclass
from statistics import mean
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class V4Interval:
    estimate: float
    lower: float
    upper: float
    confidence: float
    scenario_count: int


@dataclass(frozen=True)
class CalibrationSummary:
    brier_score: float
    calibration_in_the_large: float
    expected_calibration_error: float
    count: int


def _finite(values: Iterable[float]) -> list[float]:
    out = [float(v) for v in values]
    if not out:
        raise ValueError("at least one value is required")
    if any(not math.isfinite(v) for v in out):
        raise ValueError("values must be finite")
    return out


def brier_score(predictions: Sequence[float], outcomes: Sequence[bool | int]) -> float:
    if len(predictions) != len(outcomes) or not predictions:
        raise ValueError("predictions/outcomes must have equal non-zero length")
    ps = _finite(predictions)
    ys = [int(v) for v in outcomes]
    if any(y not in (0, 1) for y in ys):
        raise ValueError("outcomes must be binary")
    if any(p < 0.0 or p > 1.0 for p in ps):
        raise ValueError("predictions must be in [0, 1]")
    return mean((p - y) ** 2 for p, y in zip(ps, ys, strict=True))


def fixed_bin_ece(
    predictions: Sequence[float],
    outcomes: Sequence[bool | int],
    *,
    bin_count: int = 10,
) -> float:
    if bin_count < 2:
        raise ValueError("bin_count must be >= 2")
    if len(predictions) != len(outcomes) or not predictions:
        raise ValueError("predictions/outcomes must have equal non-zero length")
    ps = _finite(predictions)
    ys = [int(v) for v in outcomes]
    if any(y not in (0, 1) for y in ys):
        raise ValueError("outcomes must be binary")
    if any(p < 0.0 or p > 1.0 for p in ps):
        raise ValueError("predictions must be in [0, 1]")

    n = len(ps)
    total = 0.0
    for index in range(bin_count):
        lo = index / bin_count
        hi = (index + 1) / bin_count
        members = [
            (p, y)
            for p, y in zip(ps, ys, strict=True)
            if (lo <= p < hi) or (index == bin_count - 1 and p == 1.0)
        ]
        if not members:
            continue
        confidence = mean(p for p, _ in members)
        frequency = mean(y for _, y in members)
        total += (len(members) / n) * abs(confidence - frequency)
    return total


def calibration_summary(
    predictions: Sequence[float],
    outcomes: Sequence[bool | int],
) -> CalibrationSummary:
    ps = _finite(predictions)
    ys = [int(v) for v in outcomes]
    if len(ps) != len(ys) or not ps:
        raise ValueError("predictions/outcomes must have equal non-zero length")
    return CalibrationSummary(
        brier_score=brier_score(ps, ys),
        calibration_in_the_large=mean(ps) - mean(ys),
        expected_calibration_error=fixed_bin_ece(ps, ys),
        count=len(ps),
    )


def scenario_paired_differences(
    rows: Sequence[Mapping[str, object]],
    *,
    baseline: str,
    proposed: str,
    value_field: str,
    scenario_field: str = "scenario_id",
    seed_field: str = "execution_seed",
    planner_field: str = "planner",
) -> dict[str, list[float]]:
    """Return paired proposed-minus-baseline values grouped by scenario."""
    by_key: dict[tuple[str, int, str], float] = {}
    for row in rows:
        scenario = str(row[scenario_field])
        seed = int(row[seed_field])
        planner = str(row[planner_field])
        if planner not in (baseline, proposed):
            continue
        value = float(row[value_field])
        if not math.isfinite(value):
            raise ValueError(f"non-finite {value_field} for {scenario}/{seed}/{planner}")
        key = (scenario, seed, planner)
        if key in by_key:
            raise ValueError(f"duplicate row for {key}")
        by_key[key] = value

    scenarios = sorted({key[0] for key in by_key})
    result: dict[str, list[float]] = {}
    for scenario in scenarios:
        seeds = sorted({
            key[1]
            for key in by_key
            if key[0] == scenario and key[2] in (baseline, proposed)
        })
        diffs: list[float] = []
        for seed in seeds:
            left = (scenario, seed, baseline)
            right = (scenario, seed, proposed)
            if left not in by_key or right not in by_key:
                raise ValueError(f"unpaired trial for {scenario}/{seed}")
            diffs.append(by_key[right] - by_key[left])
        if diffs:
            result[scenario] = diffs
    if not result:
        raise ValueError("no paired rows found")
    return result


def hierarchical_bootstrap(
    differences_by_scenario: Mapping[str, Sequence[float]],
    *,
    confidence: float = 0.95,
    resamples: int = 5000,
    seed: int = 2026100304,
) -> V4Interval:
    if not differences_by_scenario:
        raise ValueError("at least one scenario is required")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in (0, 1)")
    if resamples < 100:
        raise ValueError("resamples must be at least 100")

    data = {str(k): _finite(v) for k, v in differences_by_scenario.items()}
    names = sorted(data)
    estimate = mean(mean(data[name]) for name in names)

    rng = random.Random(seed)
    replicates: list[float] = []
    for _ in range(resamples):
        sampled_names = rng.choices(names, k=len(names))
        scenario_means = []
        for name in sampled_names:
            values = data[name]
            within = rng.choices(values, k=len(values))
            scenario_means.append(mean(within))
        replicates.append(mean(scenario_means))
    replicates.sort()

    alpha = (1.0 - confidence) / 2.0
    lo = min(resamples - 1, max(0, int(alpha * resamples)))
    hi = min(resamples - 1, max(0, int((1.0 - alpha) * resamples) - 1))
    return V4Interval(
        estimate=estimate,
        lower=replicates[lo],
        upper=replicates[hi],
        confidence=confidence,
        scenario_count=len(names),
    )


def calibration_bins(
    predictions: Sequence[float],
    outcomes: Sequence[bool | int],
    *,
    bin_count: int = 10,
) -> list[dict[str, float]]:
    if len(predictions) != len(outcomes) or not predictions:
        raise ValueError("predictions/outcomes must have equal non-zero length")
    ps = _finite(predictions)
    ys = [int(v) for v in outcomes]
    rows: list[dict[str, float]] = []
    for index in range(bin_count):
        lo = index / bin_count
        hi = (index + 1) / bin_count
        members = [
            (p, y)
            for p, y in zip(ps, ys, strict=True)
            if (lo <= p < hi) or (index == bin_count - 1 and p == 1.0)
        ]
        if not members:
            continue
        rows.append({
            "bin_lower": lo,
            "bin_upper": hi,
            "count": float(len(members)),
            "mean_prediction": mean(p for p, _ in members),
            "empirical_frequency": mean(y for _, y in members),
        })
    return rows
