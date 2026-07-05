from dynnav.core import (
    NavigationState,
    PathEvaluation,
    SelfAwareCostWeights,
    estimate_self_awareness,
    expected_information_gain,
    self_aware_path_cost,
)


def test_self_awareness_recommends_active_sense_for_uncertain_low_confidence_state():
    state = NavigationState(
        pose=(0, 0),
        goal=(5, 5),
        localization_uncertainty=0.8,
        map_uncertainty=0.7,
        perception_confidence=0.4,
        planner_confidence=0.5,
        risk_estimate=0.3,
        recoverability=0.8,
    )

    score = estimate_self_awareness(state)

    assert score.recommended_mode == "ACTIVE_SENSE"
    assert 0.0 <= score.trust <= 1.0
    assert score.uncertainty_pressure > 0.6


def test_self_awareness_recommends_safe_stop_for_high_risk_state():
    state = NavigationState(
        pose=(0, 0),
        goal=(5, 5),
        localization_uncertainty=0.2,
        map_uncertainty=0.3,
        perception_confidence=0.8,
        planner_confidence=0.8,
        risk_estimate=0.9,
        recoverability=0.4,
    )

    assert estimate_self_awareness(state).recommended_mode == "SAFE_STOP"


def test_information_gain_is_high_for_unknown_cells():
    path = [(0, 0), (1, 0), (2, 0)]
    belief = {
        (0, 0): 0.5,
        (1, 0): 0.5,
        (2, 0): 0.5,
        (3, 0): 0.5,
    }

    gain = expected_information_gain(path, belief, sensor_radius=1)

    assert 0.9 <= gain <= 1.0


def test_information_gain_is_low_for_certain_cells():
    path = [(0, 0), (1, 0), (2, 0)]
    belief = {
        (0, 0): 0.0,
        (1, 0): 1.0,
        (2, 0): 0.0,
    }

    assert expected_information_gain(path, belief, sensor_radius=0) == 0.0


def test_self_aware_cost_rewards_information_gain():
    low_gain = PathEvaluation(
        path=[(0, 0), (1, 0)],
        path_length=2.0,
        expected_collision_risk=0.2,
        cvar_tail_risk=0.3,
        localization_uncertainty=0.4,
        map_uncertainty=0.4,
        information_gain=0.1,
        recoverability=0.8,
    )
    high_gain = PathEvaluation(
        path=[(0, 0), (1, 0)],
        path_length=2.0,
        expected_collision_risk=0.2,
        cvar_tail_risk=0.3,
        localization_uncertainty=0.4,
        map_uncertainty=0.4,
        information_gain=0.9,
        recoverability=0.8,
    )
    weights = SelfAwareCostWeights(kappa_information_gain=2.0)

    assert self_aware_path_cost(high_gain, weights) < self_aware_path_cost(low_gain, weights)


def test_validation_rejects_invalid_navigation_state():
    state = NavigationState(
        pose=(0, 0),
        goal=(5, 5),
        localization_uncertainty=1.2,
        map_uncertainty=0.0,
        perception_confidence=1.0,
        planner_confidence=1.0,
        risk_estimate=0.0,
        recoverability=1.0,
    )

    try:
        state.validate()
    except ValueError as exc:
        assert "localization_uncertainty" in str(exc)
    else:
        raise AssertionError("expected invalid state to raise ValueError")
