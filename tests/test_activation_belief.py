from __future__ import annotations

import pytest

from dynnav.activation_belief import ActivationBelief, expected_safe_return_probability
from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.experiments.noisy_activation_benchmark import (
    ActivationObservationScenario,
    run_noisy_activation_benchmark,
)
from dynnav.planners.grid_map import GridMap


def _bridge_model():
    grid = GridMap.from_obstacles(4, 3, obstacles={(1, 0), (1, 2)})
    safe, current = {(0, 1)}, (3, 1)
    model = CommitmentHazardModel(
        (CommitmentClosure(((2, 1), (3, 1)), (1, 1), 0.8),)
    )
    return grid, safe, current, model


def test_noisy_trigger_observation_updates_activation_posterior_by_bayes_rule() -> None:
    prior = ActivationBelief.certain_inactive()

    detected = prior.update_after_trigger_attempt(
        0,
        execution_probability=0.5,
        observed_crossing=True,
        detection_sensitivity=0.9,
        detection_specificity=0.9,
    )
    missed = prior.update_after_trigger_attempt(
        0,
        execution_probability=0.5,
        observed_crossing=False,
        detection_sensitivity=0.9,
        detection_specificity=0.9,
    )

    assert detected.probability_by_active_set[frozenset({0})] == pytest.approx(0.9)
    assert missed.probability_by_active_set[frozenset({0})] == pytest.approx(0.1)


def test_expected_return_probability_mixes_hidden_activation_states() -> None:
    grid, safe, current, model = _bridge_model()
    belief = ActivationBelief(
        {frozenset(): 0.25, frozenset({0}): 0.75}
    )

    probability = expected_safe_return_probability(grid, current, safe, model, belief)

    assert probability == pytest.approx(0.4)


def test_exact_posterior_is_no_worse_than_prior_for_brier_under_correct_sensor_model() -> None:
    records = run_noisy_activation_benchmark(
        # Sensitivity/specificity match the observation generator.
        scenarios=(ActivationObservationScenario("test", 0.5, 0.8, 0.8, 0.85, 0.8, 0.85),),
        trials=20_000,
        seed=73,
    )
    by_method = {record.method: record for record in records}

    assert by_method["bayes_posterior"].brier_score < by_method["prior_only"].brier_score


def test_benchmark_exposes_sensor_miscalibration_false_safe_risk() -> None:
    records = run_noisy_activation_benchmark(
        scenarios=(
            ActivationObservationScenario("correct", 0.5, 0.8, 0.6, 0.9, 0.6, 0.9),
            ActivationObservationScenario("miscalibrated", 0.5, 0.8, 0.6, 0.9, 0.95, 0.9),
        ),
        trials=20_000,
        seed=91,
    )
    summary = {(record.scenario, record.method): record for record in records}

    assert (
        summary[("correct", "bayes_posterior")].brier_score
        < summary[("correct", "prior_only")].brier_score
    )
    assert (
        summary[("miscalibrated", "bayes_posterior")].false_safe_rate_at_0_2
        > summary[("miscalibrated", "prior_only")].false_safe_rate_at_0_2
    )
