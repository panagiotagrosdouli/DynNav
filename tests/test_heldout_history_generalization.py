from __future__ import annotations

from dynnav.experiments.heldout_history_generalization import (
    HELDOUT_SCENARIOS,
    heterogeneous_commitment_world,
    run_heldout_history_generalization,
    summarize_heldout_history_generalization,
)


def test_heterogeneous_world_preserves_frozen_probabilities() -> None:
    probabilities = HELDOUT_SCENARIOS["low_to_high_6"]
    grid, start, goal, safe, model = heterogeneous_commitment_world(probabilities)

    assert grid.passable(start)
    assert grid.passable(goal)
    assert safe == {start}
    assert tuple(c.closure_probability for c in model.closures) == probabilities
    assert len(model.closures) == len(probabilities)


def test_state_only_marginal_model_cannot_exploit_trigger_avoiding_detours() -> None:
    scenario = {"probe": HELDOUT_SCENARIOS["alternating_7"]}
    records = run_heldout_history_generalization(
        seeds=tuple(range(20)),
        scenarios=scenario,
    )
    shortest = [row for row in records if row.planner == "shortest"]
    state_only = [row for row in records if row.planner == "state_only_single"]

    assert len(shortest) == len(state_only) == 20
    assert shortest[0].path_length == state_only[0].path_length
    assert (
        shortest[0].activated_closure_count
        == state_only[0].activated_closure_count
        == len(scenario["probe"])
    )
    assert [row.irreversible_failure for row in shortest] == [
        row.irreversible_failure for row in state_only
    ]


def test_history_aware_planners_reduce_heldout_commitment_exposure() -> None:
    records = run_heldout_history_generalization(
        seeds=(0, 1, 2),
        scenarios={"probe": HELDOUT_SCENARIOS["mixed_8"]},
    )
    by_planner = {}
    for row in records:
        by_planner.setdefault(row.planner, row)

    shortest = by_planner["shortest"]
    assert by_planner["history_exact"].activated_closure_count < shortest.activated_closure_count
    assert by_planner["history_cut"].activated_closure_count < shortest.activated_closure_count
    assert by_planner["hard_return_0.9"].activated_closure_count <= shortest.activated_closure_count


def test_heldout_summary_keeps_paired_state_only_null_effect() -> None:
    records = run_heldout_history_generalization(
        seeds=tuple(range(25)),
        scenarios={"probe": HELDOUT_SCENARIOS["low_to_high_6"]},
    )
    summary = summarize_heldout_history_generalization(records)
    effect = summary["probe"]["paired_binary_effects_vs_shortest"]["state_only_single"]

    assert effect["risk_difference"] == 0.0
    assert effect["discordant_pairs"] == 0
    assert effect["mcnemar_exact_pvalue"] == 1.0
