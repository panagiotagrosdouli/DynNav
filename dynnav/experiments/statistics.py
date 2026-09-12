"""Dependency-light statistics for reproducible navigation experiments."""
from __future__ import annotations

import math
import random
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from statistics import mean, median, stdev


@dataclass(frozen=True)
class IntervalEstimate:
    estimate: float
    lower: float
    upper: float
    confidence: float
    sample_size: int


@dataclass(frozen=True)
class PairedEffect:
    mean_difference: float
    standardized_effect: float
    probability_of_superiority: float
    interval: IntervalEstimate


@dataclass(frozen=True)
class PairedBinaryEffect:
    baseline_rate: float
    proposed_rate: float
    risk_difference: float
    interval: IntervalEstimate
    baseline_only_events: int
    proposed_only_events: int
    discordant_pairs: int
    mcnemar_exact_pvalue: float


def _values(values: Iterable[float]) -> list[float]:
    result = [float(value) for value in values]
    if not result:
        raise ValueError("at least one observation is required")
    if any(not math.isfinite(value) for value in result):
        raise ValueError("observations must be finite")
    return result


def bootstrap_mean_interval(
    values: Iterable[float], *, confidence: float = 0.95,
    resamples: int = 2000, seed: int = 0,
) -> IntervalEstimate:
    data = _values(values)
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in (0, 1)")
    if resamples < 100:
        raise ValueError("resamples must be at least 100")
    if len(data) == 1:
        return IntervalEstimate(data[0], data[0], data[0], confidence, 1)
    rng = random.Random(seed)
    estimates = sorted(mean(rng.choices(data, k=len(data))) for _ in range(resamples))
    tail = (1.0 - confidence) / 2.0
    lo = min(resamples - 1, max(0, int(tail * resamples)))
    hi = min(resamples - 1, max(0, int((1.0 - tail) * resamples) - 1))
    return IntervalEstimate(mean(data), estimates[lo], estimates[hi], confidence, len(data))


def paired_effect(
    baseline: Sequence[float], proposed: Sequence[float], *,
    confidence: float = 0.95, resamples: int = 2000, seed: int = 0,
) -> PairedEffect:
    if len(baseline) != len(proposed) or not baseline:
        raise ValueError("paired samples must have equal non-zero length")
    left, right = _values(baseline), _values(proposed)
    differences = [candidate - reference for reference, candidate in zip(left, right, strict=False)]
    spread = stdev(differences) if len(differences) > 1 else 0.0
    standardized = mean(differences) / spread if spread > 0.0 else 0.0
    wins = sum(diff < 0.0 for diff in differences)
    ties = sum(diff == 0.0 for diff in differences)
    superiority = (wins + 0.5 * ties) / len(differences)
    return PairedEffect(
        mean_difference=mean(differences),
        standardized_effect=standardized,
        probability_of_superiority=superiority,
        interval=bootstrap_mean_interval(
            differences, confidence=confidence, resamples=resamples, seed=seed
        ),
    )


def _binary(values: Sequence[bool | int]) -> list[int]:
    if not values:
        raise ValueError("at least one binary observation is required")
    result: list[int] = []
    for value in values:
        integer = int(value)
        if integer not in (0, 1) or integer != value:
            raise ValueError("binary observations must be bool/0/1")
        result.append(integer)
    return result


def exact_mcnemar_pvalue(baseline_only: int, proposed_only: int) -> float:
    """Two-sided exact McNemar p-value using the conditional binomial test."""
    if baseline_only < 0 or proposed_only < 0:
        raise ValueError("discordant counts must be non-negative")
    n = baseline_only + proposed_only
    if n == 0:
        return 1.0
    k = min(baseline_only, proposed_only)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2.0 ** n)
    return min(1.0, 2.0 * tail)


def paired_binary_effect(
    baseline: Sequence[bool | int],
    proposed: Sequence[bool | int],
    *,
    confidence: float = 0.95,
    resamples: int = 5000,
    seed: int = 0,
) -> PairedBinaryEffect:
    """Paired binary effect for event indicators (e.g. irreversible failure).

    ``risk_difference`` is proposed minus baseline, so negative values indicate
    fewer events under the proposed method when the event is undesirable.
    """
    if len(baseline) != len(proposed) or not baseline:
        raise ValueError("paired samples must have equal non-zero length")
    left = _binary(baseline)
    right = _binary(proposed)
    differences = [candidate - reference for reference, candidate in zip(left, right, strict=True)]
    baseline_only = sum(reference == 1 and candidate == 0 for reference, candidate in zip(left, right, strict=True))
    proposed_only = sum(reference == 0 and candidate == 1 for reference, candidate in zip(left, right, strict=True))
    return PairedBinaryEffect(
        baseline_rate=mean(left),
        proposed_rate=mean(right),
        risk_difference=mean(differences),
        interval=bootstrap_mean_interval(
            differences,
            confidence=confidence,
            resamples=resamples,
            seed=seed,
        ),
        baseline_only_events=baseline_only,
        proposed_only_events=proposed_only,
        discordant_pairs=baseline_only + proposed_only,
        mcnemar_exact_pvalue=exact_mcnemar_pvalue(baseline_only, proposed_only),
    )


def summarize(values: Iterable[float]) -> dict[str, float]:
    data = _values(values)
    return {
        "count": float(len(data)),
        "mean": mean(data),
        "median": median(data),
        "std": stdev(data) if len(data) > 1 else 0.0,
        "minimum": min(data),
        "maximum": max(data),
    }
