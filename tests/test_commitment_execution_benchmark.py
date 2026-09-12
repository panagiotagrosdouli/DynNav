from __future__ import annotations

import pytest

from dynnav.experiments.commitment_execution_benchmark import (
    run_commitment_execution_benchmark,
    summarize_commitment_execution,
)


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
    for planner in ("shortest", "history_exact", "history_cut", "hard_return_0.9"):
        assert {row.seed for row in records if row.planner == planner} == {3, 7, 11}
