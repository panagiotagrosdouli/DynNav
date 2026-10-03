from __future__ import annotations

import pytest

from dynnav.experiments.unavoidable_history_benchmark import unavoidable_choice_world
from dynnav.experiments.v4_belief_execution import (
    V4ExecutionScenario,
    V4Planner,
    keyed_uniform,
    run_v4_execution_trial,
    update_latched_detector_estimate,
)


def _two_module_scenario(*, sensitivity: float = 1.0, specificity: float = 1.0):
    base = unavoidable_choice_world(
        direct_probabilities=(0.8, 0.65),
        detour_probabilities=(0.3, 0.25),
        detour_depths=(1, 1),
        detour_directions=(1, -1),
        name="v4_two_module_test",
    )
    n = len(base.model.closures)
    return V4ExecutionScenario(
        name=base.name,
        grid=base.grid,
        start=base.start,
        goal=base.goal,
        safe_cells=frozenset(base.safe),
        hazard_model=base.model,
        arming_probabilities=(0.7,) * n,
        detection_sensitivities=(sensitivity,) * n,
        detection_specificities=(specificity,) * n,
    )


def test_keyed_random_variables_are_call_order_independent() -> None:
    first = keyed_uniform("scenario", 7, 2, "arming", 0)
    _ = keyed_uniform("scenario", 7, 1, "observation", 4)
    repeated = keyed_uniform("scenario", 7, 2, "arming", 0)

    assert first == repeated
    assert first != keyed_uniform("scenario", 7, 2, "closure", 0)


@pytest.mark.parametrize("seed", range(8))
def test_perfect_sensor_collapses_belief_and_detector_to_oracle(seed: int) -> None:
    scenario = _two_module_scenario()

    oracle = run_v4_execution_trial(
        scenario,
        seed=seed,
        planner=V4Planner.ACTIVATION_ORACLE,
    )
    belief = run_v4_execution_trial(
        scenario,
        seed=seed,
        planner=V4Planner.BELIEF,
    )
    detector = run_v4_execution_trial(
        scenario,
        seed=seed,
        planner=V4Planner.DETECTOR_AS_TRUTH,
    )

    assert oracle.protocol_valid and belief.protocol_valid and detector.protocol_valid
    assert oracle.mission_success and belief.mission_success and detector.mission_success
    assert belief.path == oracle.path
    assert detector.path == oracle.path
    assert belief.true_armed_set == oracle.true_armed_set
    assert detector.true_armed_set == oracle.true_armed_set
    assert belief.return_feasible == oracle.return_feasible
    assert detector.return_feasible == oracle.return_feasible
    assert belief.predicted_return_probability == pytest.approx(
        oracle.predicted_return_probability
    )
    assert detector.predicted_return_probability == pytest.approx(
        oracle.predicted_return_probability
    )


def test_repeated_trial_is_identical_regardless_of_other_planner_execution() -> None:
    scenario = _two_module_scenario(sensitivity=0.85, specificity=0.85)

    first = run_v4_execution_trial(
        scenario,
        seed=13,
        planner=V4Planner.BELIEF,
    )
    _ = run_v4_execution_trial(
        scenario,
        seed=13,
        planner=V4Planner.SHORTEST,
    )
    repeated = run_v4_execution_trial(
        scenario,
        seed=13,
        planner=V4Planner.BELIEF,
    )

    assert repeated.scenario == first.scenario
    assert repeated.seed == first.seed
    assert repeated.planner == first.planner
    assert repeated.mission_success == first.mission_success
    assert repeated.path == first.path
    assert repeated.true_armed_set == first.true_armed_set
    assert repeated.estimated_armed_set == first.estimated_armed_set
    assert repeated.observation_count == first.observation_count
    assert repeated.predicted_return_probability == pytest.approx(
        first.predicted_return_probability
    )
    assert repeated.realized_closure_cells == first.realized_closure_cells
    assert repeated.return_feasible == first.return_feasible


def test_all_predeclared_planners_produce_valid_records_on_small_world() -> None:
    scenario = _two_module_scenario(sensitivity=0.85, specificity=0.85)

    for planner in V4Planner:
        record = run_v4_execution_trial(
            scenario,
            seed=3,
            planner=planner,
        )
        assert record.protocol_valid
        assert record.mission_success
        assert record.path[0] == scenario.start
        assert record.path[-1] == scenario.goal
        assert record.path_length == len(record.path) - 1
        if planner is V4Planner.SHORTEST:
            assert record.predicted_return_probability != record.predicted_return_probability
        else:
            assert 0.0 <= record.predicted_return_probability <= 1.0


def test_detector_as_truth_positive_observation_latches_monotonically() -> None:
    estimated: set[int] = set()

    update_latched_detector_estimate(estimated, 0, observed_armed=False)
    assert estimated == set()

    update_latched_detector_estimate(estimated, 0, observed_armed=True)
    assert estimated == {0}

    update_latched_detector_estimate(estimated, 0, observed_armed=False)
    assert estimated == {0}


def test_detector_latching_rejects_negative_hazard_index() -> None:
    with pytest.raises(ValueError, match="hazard_index"):
        update_latched_detector_estimate(set(), -1, observed_armed=True)
