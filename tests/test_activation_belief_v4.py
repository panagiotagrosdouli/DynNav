from __future__ import annotations

import pytest

from dynnav.activation_belief import ActivationBelief


def test_predictive_arming_probability_after_known_trigger_execution() -> None:
    belief = ActivationBelief.certain_inactive()

    predicted = belief.predict_after_trigger_execution(
        0,
        arming_probability=0.7,
    )

    assert predicted.probability_by_active_set[frozenset()] == pytest.approx(0.3)
    assert predicted.probability_by_active_set[frozenset({0})] == pytest.approx(0.7)
    assert predicted.probability_armed(0) == pytest.approx(0.7)


def test_perfect_arming_sensor_collapses_posterior_to_truth() -> None:
    prior = ActivationBelief.certain_inactive()

    detected = prior.update_after_trigger_execution(
        0,
        arming_probability=0.4,
        observed_armed=True,
        detection_sensitivity=1.0,
        detection_specificity=1.0,
    )
    not_detected = prior.update_after_trigger_execution(
        0,
        arming_probability=0.4,
        observed_armed=False,
        detection_sensitivity=1.0,
        detection_specificity=1.0,
    )

    assert detected.probability_by_active_set == {frozenset({0}): 1.0}
    assert not_detected.probability_by_active_set == {frozenset(): 1.0}


def test_uninformative_sensor_leaves_predictive_belief_unchanged() -> None:
    prior = ActivationBelief.certain_inactive()
    predictive = prior.predict_after_trigger_execution(0, arming_probability=0.7)

    posterior = predictive.condition_on_arming_observation(
        0,
        observed_armed=True,
        detection_sensitivity=0.5,
        detection_specificity=0.5,
    )

    assert posterior.probability_by_active_set[frozenset()] == pytest.approx(0.3)
    assert posterior.probability_by_active_set[frozenset({0})] == pytest.approx(0.7)


def test_repeated_trigger_execution_preserves_monotone_arming() -> None:
    active = ActivationBelief.certain_active({0})

    predicted = active.predict_after_trigger_execution(
        0,
        arming_probability=0.1,
    )

    assert predicted.probability_by_active_set == {frozenset({0}): 1.0}


def test_multiple_hazard_predictions_preserve_joint_support() -> None:
    belief = ActivationBelief.certain_inactive()
    belief = belief.predict_after_trigger_execution(0, arming_probability=0.5)
    belief = belief.predict_after_trigger_execution(1, arming_probability=0.25)

    assert belief.probability_by_active_set[frozenset()] == pytest.approx(0.375)
    assert belief.probability_by_active_set[frozenset({0})] == pytest.approx(0.375)
    assert belief.probability_by_active_set[frozenset({1})] == pytest.approx(0.125)
    assert belief.probability_by_active_set[frozenset({0, 1})] == pytest.approx(0.125)


def test_legacy_noisy_crossing_wrapper_matches_v4_update_numerically() -> None:
    prior = ActivationBelief.certain_inactive()

    legacy = prior.update_after_trigger_attempt(
        0,
        execution_probability=0.5,
        observed_crossing=True,
        detection_sensitivity=0.9,
        detection_specificity=0.9,
    )
    v4 = prior.update_after_trigger_execution(
        0,
        arming_probability=0.5,
        observed_armed=True,
        detection_sensitivity=0.9,
        detection_specificity=0.9,
    )

    assert legacy.probability_by_active_set == v4.probability_by_active_set


def test_entropy_is_zero_for_point_belief_and_one_for_balanced_binary_belief() -> None:
    point = ActivationBelief.certain_inactive()
    balanced = ActivationBelief(
        {
            frozenset(): 0.5,
            frozenset({0}): 0.5,
        }
    )

    assert point.entropy_bits() == pytest.approx(0.0)
    assert balanced.entropy_bits() == pytest.approx(1.0)
