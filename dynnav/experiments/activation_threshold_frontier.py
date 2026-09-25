"""Safety/availability frontier for noisy trigger-activation inference."""

from __future__ import annotations

import random
from dataclasses import dataclass

from dynnav.activation_belief import ActivationBelief
from dynnav.experiments.noisy_activation_benchmark import ActivationObservationScenario


@dataclass(frozen=True)
class ActivationFrontierRecord:
    scenario: str
    method: str
    threshold: float
    trials: int
    safe_decision_rate: float
    false_safe_rate: float
    empirical_failure_rate: float
    brier_score: float


def run_activation_threshold_frontier(
    scenario: ActivationObservationScenario,
    *,
    thresholds: tuple[float, ...] = (0.05, 0.10, 0.20, 0.30, 0.40, 0.50),
    trials: int = 10_000,
    seed: int = 0,
) -> list[ActivationFrontierRecord]:
    """Evaluate matched latent trials across a frozen decision-threshold grid."""

    scenario.validate()
    if trials <= 0:
        raise ValueError("trials must be positive")
    if not thresholds:
        raise ValueError("thresholds cannot be empty")
    if any(threshold < 0.0 or threshold > 1.0 for threshold in thresholds):
        raise ValueError("thresholds must be in [0, 1]")

    methods = (
        "bayes_posterior",
        "prior_only",
        "detector_as_truth",
        "activation_oracle",
    )
    predicted: dict[str, list[float]] = {method: [] for method in methods}
    failures: list[bool] = []
    rng = random.Random(seed)

    for _ in range(trials):
        crossed = rng.random() < scenario.activation_probability
        observed = (
            rng.random() < scenario.true_sensitivity
            if crossed
            else rng.random() < 1.0 - scenario.true_specificity
        )
        failed = crossed and rng.random() < scenario.closure_probability
        failures.append(failed)

        posterior = ActivationBelief.certain_inactive().update_after_trigger_attempt(
            0,
            execution_probability=scenario.activation_probability,
            observed_crossing=observed,
            detection_sensitivity=scenario.assumed_sensitivity,
            detection_specificity=scenario.assumed_specificity,
        )
        posterior_activation = sum(
            probability
            for active, probability in posterior.probability_by_active_set.items()
            if 0 in active
        )
        estimates = {
            "bayes_posterior": scenario.closure_probability * posterior_activation,
            "prior_only": (
                scenario.closure_probability * scenario.activation_probability
            ),
            "detector_as_truth": scenario.closure_probability * float(observed),
            "activation_oracle": scenario.closure_probability * float(crossed),
        }
        for method, estimate in estimates.items():
            predicted[method].append(estimate)

    empirical_failure = sum(failures) / trials
    records: list[ActivationFrontierRecord] = []
    for method in methods:
        brier = sum(
            (estimate - float(failed)) ** 2
            for estimate, failed in zip(predicted[method], failures, strict=True)
        ) / trials
        for threshold in thresholds:
            safe_mask = [estimate <= threshold for estimate in predicted[method]]
            safe_count = sum(safe_mask)
            false_safe_count = sum(
                int(is_safe and failed)
                for is_safe, failed in zip(safe_mask, failures, strict=True)
            )
            records.append(
                ActivationFrontierRecord(
                    scenario=scenario.name,
                    method=method,
                    threshold=float(threshold),
                    trials=trials,
                    safe_decision_rate=safe_count / trials,
                    false_safe_rate=(
                        false_safe_count / safe_count if safe_count else 0.0
                    ),
                    empirical_failure_rate=empirical_failure,
                    brier_score=brier,
                )
            )
    return records
