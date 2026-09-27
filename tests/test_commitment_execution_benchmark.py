from __future__ import annotations

import pytest

from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.experiments.commitment_execution_benchmark import (
    _realize_after_commitment,
    run_commitment_execution_benchmark,
    summarize_commitment_execution,
)
from dynnav.planners.grid_map import GridMap


def test_shortest_empirical_failure_matches_series_closure_probability() -> None:
    module_count = 3
    probability = 0.5
    records = run_commitment_execution_benchmark(
        seeds=tuple(range(2000)),
        module_count=module_count,
        closure_probabilities=(probability,),
        recoverability_weight=8.0,
    )
    shortest = [row for row in records if row.planner == "shortest"]
    observed = sum(row.irreversible_failure for row in shortest) / len(shortest)
    expected = 1.0 - (1.0 - probability) ** module_count
    assert observed == pytest.approx(expected, abs=0.03)


def test_state_only_marginal_risk_cannot_value_trigger_avoiding_detours() -> None:
    records = run_commitment_execution_benchmark(
        seeds=tuple(range(500)),
        module_count=2,
        closure_probabilities=(0.8,),
        recoverability_weight=8.0,
    )
    summary = summarize_commitment_execution(records)

    shortest = summary["shortest:p=0.8"]
    state_only = summary["state_only_single:p=0.8"]
    state_only_exact = summary["state_only_exact:p=0.8"]
    assert state_only["activated_closure_count"] == shortest["activated_closure_count"] == 2
    assert state_only["path_length"] == shortest["path_length"]
    assert state_only["irreversible_failure_rate"] == pytest.approx(
        shortest["irreversible_failure_rate"]
    )
    assert state_only_exact["activated_closure_count"] == shortest["activated_closure_count"]
    assert state_only_exact["path_length"] == shortest["path_length"]
    assert state_only_exact["irreversible_failure_rate"] == pytest.approx(
        shortest["irreversible_failure_rate"]
    )


def test_high_penalty_history_and_hard_planners_avoid_high_probability_irreversibility() -> None:
    records = run_commitment_execution_benchmark(
        seeds=tuple(range(500)),
        module_count=2,
        closure_probabilities=(0.8,),
        recoverability_weight=8.0,
        safe_return_threshold=0.9,
    )
    summary = summarize_commitment_execution(records)

    assert summary["shortest:p=0.8"]["irreversible_failure_rate"] > 0.9
    for planner in ("history_exact", "history_cut", "hard_return_0.9"):
        assert summary[f"{planner}:p=0.8"]["activated_closure_count"] == 0
        assert summary[f"{planner}:p=0.8"]["irreversible_failure_rate"] == pytest.approx(0.0)
        effect = summary["paired_binary_effects"]["p=0.8"][planner]
        assert effect["risk_difference"] < -0.9
        assert effect["proposed_only_events"] == 0
        assert effect["mcnemar_exact_pvalue"] < 0.05


def test_execution_records_are_paired_by_seed_across_planners() -> None:
    records = run_commitment_execution_benchmark(
        seeds=(3, 7, 11),
        module_count=1,
        closure_probabilities=(0.5,),
        recoverability_weight=8.0,
        safe_return_threshold=0.9,
    )
    for planner in (
        "shortest",
        "state_only_single",
        "state_only_exact",
        "history_exact",
        "history_cut",
        "hard_return_0.9",
    ):
        assert {row.seed for row in records if row.planner == planner} == {3, 7, 11}


def test_same_seed_assigns_same_latent_draw_to_shared_event_index() -> None:
    # random.Random(1) gives draw0 ~= 0.134 and draw1 ~= 0.847. Event 1
    # therefore must remain open at p=0.5 whether event 0 is active or not.
    grid = GridMap.from_obstacles(5, 1)
    model = CommitmentHazardModel(
        (
            CommitmentClosure(((0, 0), (1, 0)), (1, 0), 0.5),
            CommitmentClosure(((3, 0), (4, 0)), (3, 0), 0.5),
        )
    )
    only_second, _ = _realize_after_commitment(
        grid, (4, 0), model, {1}, seed=1
    )
    both, _ = _realize_after_commitment(
        grid, (4, 0), model, {0, 1}, seed=1
    )

    assert (3, 0) not in only_second.obstacles
    assert (3, 0) not in both.obstacles
