from __future__ import annotations

from dataclasses import asdict

from dynnav_nav2_benchmark.v4_hidden_arming import (
    PlannerArmingObservation,
    V4ArmingModel,
    keyed_v4_draw,
    oracle_observation,
    sample_hidden_arming_after_executed_trigger,
)


def test_v4_hidden_arming_draws_are_keyed_and_order_independent() -> None:
    first = keyed_v4_draw(17, "scenario", 3, "h0", "arming", 0)
    _ = keyed_v4_draw(17, "scenario", 3, "h1", "observation", 2)
    repeated = keyed_v4_draw(17, "scenario", 3, "h0", "arming", 0)

    assert first == repeated
    assert first != keyed_v4_draw(17, "scenario", 3, "h0", "closure", 0)


def test_non_oracle_detector_message_contains_no_latent_truth_field() -> None:
    outcome = sample_hidden_arming_after_executed_trigger(
        seed=17,
        scenario="scenario",
        repetition=3,
        hazard_id="h0",
        model=V4ArmingModel(
            arming_probability=0.7,
            detection_sensitivity=0.85,
            detection_specificity=0.85,
            closure_probability_given_armed=0.8,
        ),
    )

    payload = asdict(outcome.detector_message)
    assert isinstance(outcome.detector_message, PlannerArmingObservation)
    assert "true_armed" not in payload
    assert "future_closure_realized" not in payload


def test_oracle_truth_requires_explicit_oracle_conversion() -> None:
    outcome = sample_hidden_arming_after_executed_trigger(
        seed=8,
        scenario="scenario",
        repetition=1,
        hazard_id="h0",
        model=V4ArmingModel(
            arming_probability=1.0,
            detection_sensitivity=0.0,
            detection_specificity=1.0,
            closure_probability_given_armed=0.8,
        ),
    )

    assert outcome.true_armed
    assert not outcome.detector_message.observed_armed

    oracle = oracle_observation(outcome)
    assert oracle.true_armed
    assert not hasattr(outcome.detector_message, "true_armed")


def test_future_closure_cannot_realize_when_hazard_is_not_armed() -> None:
    model = V4ArmingModel(
        arming_probability=0.0,
        detection_sensitivity=1.0,
        detection_specificity=1.0,
        closure_probability_given_armed=1.0,
    )
    for repetition in range(10):
        outcome = sample_hidden_arming_after_executed_trigger(
            seed=9,
            scenario="scenario",
            repetition=repetition,
            hazard_id="h0",
            model=model,
        )
        assert not outcome.true_armed
        assert not outcome.future_closure_realized
