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
