"""Repeated-sample causal effect controls for DynNav G4.

The benchmark separates two questions:

1. Under randomized/ignorable trigger assignment with correctly logged
   propensities, how do IPW bias, RMSE and interval coverage scale with sample
   size, treatment propensity and injected effect?
2. Under a binary common cause with true causal effect zero, how different are
   estimates obtained with the correct record-level assignment propensity and a
   deliberately misspecified marginal propensity?

This remains a bounded interventional/propensity benchmark, not arbitrary SCM
discovery.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from dynnav.causal_trigger_discovery import (
    TriggerOutcomeRecord,
    estimate_ipw_trigger_effect,
)


@dataclass(frozen=True)
class CausalSweepSummary:
    condition: str
    sample_size: int
    repetitions: int
    true_ate: float
    treatment_propensity: float | None
    mean_estimate: float
    bias: float
    rmse: float
    interval_coverage: float
    positive_interval_rate: float


def _summarize(
    *,
    condition: str,
    estimates: list[tuple[float, float, float]],
    sample_size: int,
    true_ate: float,
    treatment_propensity: float | None,
) -> CausalSweepSummary:
    if not estimates:
        raise ValueError("estimates cannot be empty")
    values = [value for value, _lower, _upper in estimates]
    mean_estimate = sum(values) / len(values)
    rmse = math.sqrt(
        sum((value - true_ate) ** 2 for value in values) / len(values)
    )
    coverage = sum(
        lower <= true_ate <= upper for _value, lower, upper in estimates
    ) / len(estimates)
    positive = sum(lower > 0.0 for _value, lower, _upper in estimates) / len(
        estimates
    )
    return CausalSweepSummary(
        condition=condition,
        sample_size=sample_size,
        repetitions=len(estimates),
        true_ate=true_ate,
        treatment_propensity=treatment_propensity,
        mean_estimate=mean_estimate,
        bias=mean_estimate - true_ate,
        rmse=rmse,
        interval_coverage=coverage,
        positive_interval_rate=positive,
    )


def _randomized_records(
    rng: random.Random,
    *,
    sample_size: int,
    propensity: float,
    baseline_probability: float,
    effect: float,
) -> list[TriggerOutcomeRecord]:
    records: list[TriggerOutcomeRecord] = []
    for _ in range(sample_size):
        executed = rng.random() < propensity
        outcome_probability = baseline_probability + effect * float(executed)
        records.append(
            TriggerOutcomeRecord(
                trigger_id="trigger",
                closure_id="closure",
                executed=executed,
                closure_observed=rng.random() < outcome_probability,
                execution_propensity=propensity,
            )
        )
    return records


def run_randomized_ipw_sweep(
    *,
    sample_sizes: tuple[int, ...] = (200, 1_000, 5_000),
    propensities: tuple[float, ...] = (0.2, 0.5, 0.8),
    effects: tuple[float, ...] = (0.0, 0.1, 0.3, 0.5),
    repetitions: int = 50,
    baseline_probability: float = 0.1,
    seed: int = 20260925,
) -> list[CausalSweepSummary]:
    """Evaluate repeated randomized IPW effect recovery."""

    if repetitions <= 0:
        raise ValueError("repetitions must be positive")
    if any(size <= 1 for size in sample_sizes):
        raise ValueError("sample sizes must exceed one")
    if any(not 0.0 < value < 1.0 for value in propensities):
        raise ValueError("propensities must be strictly between zero and one")
    if not 0.0 <= baseline_probability <= 1.0:
        raise ValueError("baseline_probability must be in [0, 1]")
    if any(
        effect < 0.0 or baseline_probability + effect > 1.0
        for effect in effects
    ):
        raise ValueError("effects must keep outcome probabilities in [0, 1]")

    summaries: list[CausalSweepSummary] = []
    condition_index = 0
    for sample_size in sample_sizes:
        for propensity in propensities:
            for effect in effects:
                estimates: list[tuple[float, float, float]] = []
                for repetition in range(repetitions):
                    rng = random.Random(
                        seed + condition_index * 100_000 + repetition
                    )
                    records = _randomized_records(
                        rng,
                        sample_size=sample_size,
                        propensity=propensity,
                        baseline_probability=baseline_probability,
                        effect=effect,
                    )
                    estimate = estimate_ipw_trigger_effect(
                        records,
                        trigger_id="trigger",
                        closure_id="closure",
                    )
                    lower, upper = estimate.approximate_95_interval
                    estimates.append((estimate.ate, lower, upper))
                summaries.append(
                    _summarize(
                        condition=(
                            f"randomized_p{propensity:g}_effect{effect:g}"
                        ),
                        estimates=estimates,
                        sample_size=sample_size,
                        true_ate=effect,
                        treatment_propensity=propensity,
                    )
                )
                condition_index += 1
    return summaries


def run_confounding_propensity_control(
    *,
    sample_size: int = 5_000,
    repetitions: int = 100,
    confounder_probability: float = 0.5,
    treatment_given_high: float = 0.8,
    treatment_given_low: float = 0.2,
    outcome_given_high: float = 0.8,
    outcome_given_low: float = 0.1,
    seed: int = 20260925,
) -> tuple[CausalSweepSummary, CausalSweepSummary]:
    """Compare correct versus misspecified propensity under zero true ATE.

    Outcome depends only on the binary context/confounder, not on treatment.
    The true causal treatment effect is therefore exactly zero.

    The corrected condition records the actual context-specific assignment
    propensity for every trial. The misspecified condition records only the
    marginal treatment propensity, deliberately violating the ignorability
    representation needed by IPW.
    """

    values = (
        confounder_probability,
        treatment_given_high,
        treatment_given_low,
        outcome_given_high,
        outcome_given_low,
    )
    if any(not 0.0 <= value <= 1.0 for value in values):
        raise ValueError("probabilities must lie in [0, 1]")
    if sample_size <= 1 or repetitions <= 0:
        raise ValueError("invalid sample_size or repetitions")
    if not 0.0 < treatment_given_high < 1.0:
        raise ValueError("treatment_given_high must be strictly inside (0, 1)")
    if not 0.0 < treatment_given_low < 1.0:
        raise ValueError("treatment_given_low must be strictly inside (0, 1)")

    marginal_propensity = (
        confounder_probability * treatment_given_high
        + (1.0 - confounder_probability) * treatment_given_low
    )
    corrected_estimates: list[tuple[float, float, float]] = []
    misspecified_estimates: list[tuple[float, float, float]] = []

    for repetition in range(repetitions):
        rng = random.Random(seed + repetition)
        corrected: list[TriggerOutcomeRecord] = []
        misspecified: list[TriggerOutcomeRecord] = []
        for _ in range(sample_size):
            high = rng.random() < confounder_probability
            actual_propensity = (
                treatment_given_high if high else treatment_given_low
            )
            executed = rng.random() < actual_propensity
            outcome_probability = outcome_given_high if high else outcome_given_low
            outcome = rng.random() < outcome_probability
            corrected.append(
                TriggerOutcomeRecord(
                    "trigger",
                    "closure",
                    executed,
                    outcome,
                    actual_propensity,
                )
            )
            misspecified.append(
                TriggerOutcomeRecord(
                    "trigger",
                    "closure",
                    executed,
                    outcome,
                    marginal_propensity,
                )
            )

        for records, destination in (
            (corrected, corrected_estimates),
            (misspecified, misspecified_estimates),
        ):
            estimate = estimate_ipw_trigger_effect(
                records,
                trigger_id="trigger",
                closure_id="closure",
            )
            lower, upper = estimate.approximate_95_interval
            destination.append((estimate.ate, lower, upper))

    return (
        _summarize(
            condition="confounded_correct_record_propensity",
            estimates=corrected_estimates,
            sample_size=sample_size,
            true_ate=0.0,
            treatment_propensity=None,
        ),
        _summarize(
            condition="confounded_misspecified_marginal_propensity",
            estimates=misspecified_estimates,
            sample_size=sample_size,
            true_ate=0.0,
            treatment_propensity=marginal_propensity,
        ),
    )
