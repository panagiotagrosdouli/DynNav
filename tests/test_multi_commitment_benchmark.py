from __future__ import annotations

import pytest

from dynnav.experiments.multi_commitment_benchmark import (
    multi_commitment_world,
    run_multi_commitment_benchmark,
    summarize_multi_commitment,
)
from dynnav.planners.commitment_aware_astar import CommitmentPlannerMode, commitment_aware_astar


def test_shortest_activates_every_module_trigger() -> None:
    grid, start, goal, safe, model = multi_commitment_world(3, 0.5)
    result = commitment_aware_astar(
        grid,
        start,
        goal,
        safe_cells=safe,
        hazard_model=model,
        mode=CommitmentPlannerMode.SHORTEST,
    )
    assert result.success
    assert result.activated_closure_count == 3
    assert result.geometric_length == 12


def test_exact_and_cut_agree_on_series_critical_family() -> None:
    records = run_multi_commitment_benchmark(
        module_counts=(1, 2, 3),
        closure_probabilities=(0.2, 0.8),
        recoverability_weights=(1.0, 8.0),
    )
    summary = summarize_multi_commitment(records)
    assert summary["exact_cut_route_agreement_rate"] == pytest.approx(1.0)


def test_high_penalty_avoids_high_probability_commitments() -> None:
    records = run_multi_commitment_benchmark(
        module_counts=(2,),
        closure_probabilities=(0.8,),
        recoverability_weights=(8.0,),
    )
    exact = next(row for row in records if row.planner == "history_exact")
    cut = next(row for row in records if row.planner == "history_cut")
    shortest = next(row for row in records if row.planner == "shortest")

    assert shortest.activated_closure_count == 2
    assert exact.activated_closure_count < shortest.activated_closure_count
    assert cut.activated_closure_count == exact.activated_closure_count
    assert exact.final_exact_return_probability >= shortest.final_exact_return_probability
