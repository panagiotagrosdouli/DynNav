"""Falsification benchmark for noisy activation history.

The experiment distinguishes physical trigger-edge execution, its noisy
observation, and the later uncertain topology closure. It is a mechanism study,
not evidence for a new general POMDP algorithm.
"""

from __future__ import annotations

import csv
import json
import random
from dataclasses import asdict, dataclass
from math import isfinite
from pathlib import Path

from dynnav.activation_belief import ActivationBelief


@dataclass(frozen=True)
class ActivationObservationScenario:
    name: str
    activation_probability: float
    closure_probability: float
    true_sensitivity: float
    true_specificity: float
    assumed_sensitivity: float
    assumed_specificity: float

    def validate(self) -> None:
        for name in (
            "activation_probability",
            "closure_probability",
            "true_sensitivity",
            "true_specificity",
            "assumed_sensitivity",
            "assumed_specificity",
        ):
            value = getattr(self, name)
            if not isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")
        if not self.name:
            raise ValueError("scenario name must be non-empty")


@dataclass(frozen=True)
class NoisyActivationRecord:
    scenario: str
    method: str
    activation_probability: float
    closure_probability: float
    true_sensitivity: float
    true_specificity: float
    assumed_sensitivity: float
    assumed_specificity: float
    trials: int
    scenario_seed: int
    empirical_failure_rate: float
    mean_predicted_failure_probability: float
    brier_score: float
    false_safe_rate_at_0_2: float
    safe_decision_rate_at_0_2: float


DEFAULT_SCENARIOS = (
    ActivationObservationScenario("informative_correct", 0.5, 0.8, 0.9, 0.9, 0.9, 0.9),
    ActivationObservationScenario("weak_correct", 0.5, 0.8, 0.6, 0.6, 0.6, 0.6),
    ActivationObservationScenario("missed_activation", 0.5, 0.8, 0.6, 0.9, 0.95, 0.9),
    ActivationObservationScenario("false_positive_sensor", 0.5, 0.8, 0.9, 0.6, 0.9, 0.95),
    ActivationObservationScenario("low_activation_risk", 0.2, 0.8, 0.7, 0.9, 0.7, 0.9),
    ActivationObservationScenario("high_activation_risk", 0.8, 0.8, 0.7, 0.9, 0.7, 0.9),
)


def run_noisy_activation_benchmark(
    *,
    scenarios: tuple[ActivationObservationScenario, ...] = DEFAULT_SCENARIOS,
    trials: int = 10_000,
    seed: int = 0,
) -> list[NoisyActivationRecord]:
    """Compare posterior, prior-only, detector-as-truth, and oracle estimates."""

    if trials <= 0:
        raise ValueError("trials must be positive")
    if not scenarios:
        raise ValueError("scenarios cannot be empty")

    records: list[NoisyActivationRecord] = []
    methods = ("bayes_posterior", "prior_only", "detector_as_truth", "activation_oracle")
    for scenario_index, scenario in enumerate(scenarios):
        scenario.validate()
        rng = random.Random(seed + scenario_index)
        brier_sum = {method: 0.0 for method in methods}
        predicted_sum = {method: 0.0 for method in methods}
        false_safe = {method: 0 for method in methods}
        safe_decisions = {method: 0 for method in methods}
        failure_count = 0

        for _ in range(trials):
            crossed = rng.random() < scenario.activation_probability
            observed = (
                rng.random() < scenario.true_sensitivity
                if crossed
                else rng.random() < 1.0 - scenario.true_specificity
            )
            failed = crossed and rng.random() < scenario.closure_probability
            failure_count += int(failed)

            posterior = ActivationBelief.certain_inactive().update_after_trigger_attempt(
                0,
                execution_probability=scenario.activation_probability,
                observed_crossing=observed,
                detection_sensitivity=scenario.assumed_sensitivity,
                detection_specificity=scenario.assumed_specificity,
            )
            posterior_activation = sum(
                probability for active, probability in posterior.probability_by_active_set.items() if 0 in active
            )
            estimates = {
                "bayes_posterior": scenario.closure_probability * posterior_activation,
                "prior_only": scenario.closure_probability * scenario.activation_probability,
                "detector_as_truth": scenario.closure_probability * float(observed),
                "activation_oracle": scenario.closure_probability * float(crossed),
            }
            for method, estimate in estimates.items():
                predicted_sum[method] += estimate
                brier_sum[method] += (estimate - float(failed)) ** 2
                if estimate <= 0.2:
                    safe_decisions[method] += 1
                    false_safe[method] += int(failed)

        empirical_failure_rate = failure_count / trials
        for method in methods:
            records.append(
                NoisyActivationRecord(
                    scenario=scenario.name,
                    method=method,
                    activation_probability=scenario.activation_probability,
                    closure_probability=scenario.closure_probability,
                    true_sensitivity=scenario.true_sensitivity,
                    true_specificity=scenario.true_specificity,
                    assumed_sensitivity=scenario.assumed_sensitivity,
                    assumed_specificity=scenario.assumed_specificity,
                    trials=trials,
                    scenario_seed=seed + scenario_index,
                    empirical_failure_rate=empirical_failure_rate,
                    mean_predicted_failure_probability=predicted_sum[method] / trials,
                    brier_score=brier_sum[method] / trials,
                    false_safe_rate_at_0_2=(
                        false_safe[method] / safe_decisions[method] if safe_decisions[method] else 0.0
                    ),
                    safe_decision_rate_at_0_2=safe_decisions[method] / trials,
                )
            )
    return records


def summarize_noisy_activation(records: list[NoisyActivationRecord]) -> dict[str, dict[str, dict[str, float]]]:
    """Return compact per-scenario calibration and false-safe summaries."""

    summary: dict[str, dict[str, dict[str, float]]] = {}
    for record in records:
        summary.setdefault(record.scenario, {})[record.method] = {
            "empirical_failure_rate": record.empirical_failure_rate,
            "mean_predicted_failure_probability": record.mean_predicted_failure_probability,
            "brier_score": record.brier_score,
            "false_safe_rate_at_0_2": record.false_safe_rate_at_0_2,
            "safe_decision_rate_at_0_2": record.safe_decision_rate_at_0_2,
        }
    return summary


def write_noisy_activation_artifacts(records: list[NoisyActivationRecord], output_dir: str | Path) -> None:
    """Write raw per-method aggregates and their deterministic summary."""

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    rows = [asdict(record) for record in records]
    if not rows:
        raise ValueError("records cannot be empty")
    with (destination / "noisy_activation_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    with (destination / "noisy_activation_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summarize_noisy_activation(records), handle, indent=2, sort_keys=True)
    manifest = {
        "trials_per_scenario": records[0].trials,
        "scenario_seeds": {record.scenario: record.scenario_seed for record in records},
        "decision_threshold_failure_probability": 0.2,
        "methods": sorted({record.method for record in records}),
        "scenarios": sorted({record.scenario for record in records}),
        "metrics": [
            "empirical_failure_rate",
            "mean_predicted_failure_probability",
            "brier_score",
            "false_safe_rate_at_0_2",
            "safe_decision_rate_at_0_2",
        ],
    }
    with (destination / "run_metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
