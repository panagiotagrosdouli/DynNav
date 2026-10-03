from __future__ import annotations

import pytest

from dynnav.activation_belief import ActivationBelief
from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.experiments.belief_route_mechanism import redundant_corridor_world
from dynnav.planners.grid_map import GridMap

from dynnav.experiments.unavoidable_history_benchmark import unavoidable_choice_world
from dynnav.experiments.v4_belief_execution import (
    V4ExecutionScenario,
    V4Planner,
    _plan_next,
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
        assert record.path[0] == scenario.start
        assert record.path_length == len(record.path) - 1
        if planner is V4Planner.HARD_BELIEF:
            # A hard safe-return constraint is allowed to make the mission
            # infeasible. That is a meaningful baseline outcome, not a
            # protocol failure to be hidden or coerced into success.
            continue
        assert record.mission_success
        assert record.path[-1] == scenario.goal
        if planner is V4Planner.SHORTEST:
            assert record.predicted_return_probability != record.predicted_return_probability
        else:
            assert 0.0 <= record.predicted_return_probability <= 1.0


def test_hard_belief_can_refuse_an_outbound_mission_without_protocol_failure() -> None:
    scenario = _two_module_scenario(sensitivity=0.85, specificity=0.85)

    record = run_v4_execution_trial(
        scenario,
        seed=3,
        planner=V4Planner.HARD_BELIEF,
    )

    assert record.protocol_valid
    assert not record.mission_success
    assert record.path == (scenario.start,)
    assert record.planning_calls == 1


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



def _forced_misspecification_scenario(
    *,
    assumed_sensitivity: float | None = None,
    assumed_specificity: float | None = None,
    assumed_q: float | None = None,
) -> V4ExecutionScenario:
    grid = GridMap.from_obstacles(3, 1)
    model = CommitmentHazardModel(
        (
            CommitmentClosure(
                trigger=((0, 0), (1, 0)),
                closure_cell=(1, 0),
                closure_probability=0.8,
            ),
        )
    )
    return V4ExecutionScenario(
        name="v4_forced_misspecification",
        grid=grid,
        start=(0, 0),
        goal=(2, 0),
        safe_cells=frozenset({(0, 0)}),
        hazard_model=model,
        arming_probabilities=(0.5,),
        detection_sensitivities=(0.8,),
        detection_specificities=(0.8,),
        assumed_arming_probabilities=(
            None if assumed_q is None else (assumed_q,)
        ),
        assumed_detection_sensitivities=(
            None
            if assumed_sensitivity is None
            else (assumed_sensitivity,)
        ),
        assumed_detection_specificities=(
            None
            if assumed_specificity is None
            else (assumed_specificity,)
        ),
    )


def test_model_misspecification_changes_inference_not_keyed_truth() -> None:
    correct = _forced_misspecification_scenario()
    misspecified = _forced_misspecification_scenario(
        assumed_sensitivity=0.95,
        assumed_specificity=0.95,
        assumed_q=0.7,
    )

    prediction_differences = 0
    for seed in range(12):
        left = run_v4_execution_trial(
            correct,
            seed=seed,
            planner=V4Planner.BELIEF,
        )
        right = run_v4_execution_trial(
            misspecified,
            seed=seed,
            planner=V4Planner.BELIEF,
        )

        assert left.path == right.path
        assert left.true_armed_set == right.true_armed_set
        assert left.detector_observations == right.detector_observations
        assert left.realized_closure_cells == right.realized_closure_cells
        assert left.return_feasible == right.return_feasible
        prediction_differences += int(
            abs(
                left.predicted_return_probability
                - right.predicted_return_probability
            )
            > 1e-12
        )

    assert prediction_differences > 0


def test_execution_scenario_rejects_invalid_assumed_model() -> None:
    scenario = _forced_misspecification_scenario(
        assumed_sensitivity=1.2,
    )

    with pytest.raises(ValueError, match="planning_detection_sensitivities"):
        scenario.validate()



def _information_barrier_scenario() -> tuple[V4ExecutionScenario, tuple[int, int]]:
    grid, current, goal, safe, model = redundant_corridor_world(
        closure_probability=0.8
    )
    scenario = V4ExecutionScenario(
        name="v4_information_barrier",
        grid=grid,
        start=current,
        goal=goal,
        safe_cells=frozenset(safe),
        hazard_model=model,
        arming_probabilities=(0.0, 1.0),
        detection_sensitivities=(0.85, 0.85),
        detection_specificities=(0.85, 0.85),
    )
    return scenario, current


@pytest.mark.parametrize(
    "planner",
    (
        V4Planner.SHORTEST,
        V4Planner.FIXED_MARGINAL_EXACT,
        V4Planner.DETECTOR_AS_TRUTH,
        V4Planner.BELIEF,
        V4Planner.HARD_BELIEF,
        V4Planner.PRIOR_ONLY,
    ),
)
def test_non_oracle_planners_cannot_change_action_when_only_hidden_truth_changes(
    planner: V4Planner,
) -> None:
    scenario, current = _information_barrier_scenario()
    observed_belief = ActivationBelief.certain_inactive()
    prior_only = ActivationBelief.certain_inactive()
    detector_active: set[int] = set()

    latent_inactive = _plan_next(
        scenario,
        planner,
        current,
        true_active=set(),
        detector_active=detector_active,
        belief=observed_belief,
        prior_only_belief=prior_only,
    )
    latent_armed = _plan_next(
        scenario,
        planner,
        current,
        true_active={0},
        detector_active=detector_active,
        belief=observed_belief,
        prior_only_belief=prior_only,
    )

    assert latent_inactive.success == latent_armed.success
    assert latent_inactive.path == latent_armed.path
    assert latent_inactive.cost == pytest.approx(latent_armed.cost)


def test_oracle_is_the_only_condition_allowed_to_change_action_with_hidden_truth() -> None:
    scenario, current = _information_barrier_scenario()
    belief = ActivationBelief.certain_inactive()

    latent_inactive = _plan_next(
        scenario,
        V4Planner.ACTIVATION_ORACLE,
        current,
        true_active=set(),
        detector_active=set(),
        belief=belief,
        prior_only_belief=belief,
    )
    latent_armed = _plan_next(
        scenario,
        V4Planner.ACTIVATION_ORACLE,
        current,
        true_active={0},
        detector_active=set(),
        belief=belief,
        prior_only_belief=belief,
    )

    assert latent_inactive.success
    assert latent_armed.success
    assert latent_inactive.path != latent_armed.path
