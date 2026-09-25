from __future__ import annotations

from dynnav_nav2_benchmark.correlated_history_runtime import (
    CorrelatedHazardRuntimeSpec,
    CorrelatedHistoryRuntimeState,
    paired_closure_outcomes,
)


def test_correlated_latent_outcomes_are_planner_independent_and_marginally_defined() -> None:
    first = paired_closure_outcomes(
        seed=20260925,
        scenario_name="correlated_return",
        repetition=3,
        dependence="common_cause",
    )
    second = paired_closure_outcomes(
        seed=20260925,
        scenario_name="correlated_return",
        repetition=3,
        dependence="common_cause",
    )
    assert first == second
    assert first[0] == first[1]

    anti = paired_closure_outcomes(
        seed=20260925,
        scenario_name="correlated_return",
        repetition=3,
        dependence="anti_correlated",
    )
    assert anti[0] != anti[1]


def test_two_hazard_runtime_activates_only_executed_directed_triggers() -> None:
    hazards = (
        CorrelatedHazardRuntimeSpec(
            "h0",
            ((10, 10), (11, 10)),
            0.5,
        ),
        CorrelatedHazardRuntimeSpec(
            "h1",
            ((12, 10), (13, 10)),
            0.5,
        ),
    )
    state = CorrelatedHistoryRuntimeState(hazards, (True, False))
    state.observe((10, 10))
    state.observe((11, 10))
    assert state.trigger_observed == [True, False]
    assert state.closure_requested == [True, False]

    # Traverse toward the second trigger and execute it directly.
    state.observe((12, 10))
    state.observe((13, 10))
    assert state.trigger_observed == [True, True]
    assert state.closure_requested == [True, False]
    assert state.activated_count == 2
    assert state.requested_closure_count == 1
    assert state.observation_valid


def test_continuous_gate_crossing_activates_without_adjacent_cell_sampling() -> None:
    gate_edges = tuple((((72, y), (73, y))) for y in range(90, 121))
    hazards = (
        CorrelatedHazardRuntimeSpec(
            "h0",
            ((72, 104), (73, 104)),
            0.5,
            trigger_edges=gate_edges,
            gate_x=3.65,
            gate_center_y=5.225,
            gate_half_width_m=0.75,
            origin_y=0.0,
            resolution=0.05,
        ),
        CorrelatedHazardRuntimeSpec(
            "h1",
            ((92, 104), (93, 104)),
            0.5,
            gate_x=4.65,
            gate_center_y=5.225,
            gate_half_width_m=0.75,
            origin_y=0.0,
            resolution=0.05,
        ),
    )
    state = CorrelatedHistoryRuntimeState(hazards, (True, False))
    assert state.observe_world(3.50, 5.30) == ()
    emitted = state.observe_world(3.80, 5.30)
    assert len(emitted) == 1
    assert state.trigger_observed == [True, False]
    assert state.closure_requested == [True, False]
    assert state.observation_valid


def test_normal_multi_cell_motion_is_not_a_sampling_failure() -> None:
    hazards = (
        CorrelatedHazardRuntimeSpec("h0", ((10, 10), (11, 10)), 0.5),
        CorrelatedHazardRuntimeSpec("h1", ((12, 10), (13, 10)), 0.5),
    )
    state = CorrelatedHistoryRuntimeState(hazards, (False, False))
    state.observe_world(0.0, 0.0)
    state.observe_world(0.25, 0.0)
    assert state.observation_valid
    assert state.localization_jumps == []

    state.observe_world(2.0, 0.0)
    assert not state.observation_valid
    assert len(state.localization_jumps) == 1
