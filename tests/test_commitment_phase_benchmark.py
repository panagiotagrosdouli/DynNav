from __future__ import annotations

import pytest

from dynnav.experiments.commitment_phase_benchmark import (
    commitment_phase_world,
    run_commitment_phase_benchmark,
    summarize_commitment_phase,
)
from dynnav.planners.commitment_aware_astar import (
    CommitmentAwareAStarConfig,
    CommitmentPlannerMode,
    commitment_aware_astar,
)


def test_detour_overhead_is_exactly_twice_depth() -> None:
    for depth in (1, 2, 3):
        grid, start, goal, safe, model = commitment_phase_world(depth, 0.8)
        direct = commitment_aware_astar(
            grid, start, goal, safe_cells=safe, hazard_model=model,
            mode=CommitmentPlannerMode.SHORTEST,
        )
        robust = commitment_aware_astar(
            grid, start, goal, safe_cells=safe, hazard_model=model,
            mode=CommitmentPlannerMode.HISTORY_AWARE,
            config=CommitmentAwareAStarConfig(recoverability_weight=100.0),
        )
        # start -> bridge -> junction -> midpoint -> goal
        assert direct.geometric_length == 4
        assert robust.geometric_length == direct.geometric_length + 2 * depth
        assert direct.activated_closure_count == 1
        assert robust.activated_closure_count == 0


def test_history_aware_choice_matches_strict_analytic_boundary() -> None:
    records = run_commitment_phase_benchmark(
        detour_depths=(1, 2, 3),
        closure_probabilities=(0.2, 0.5, 0.8),
        recoverability_weights=(1.0, 4.0, 8.0, 16.0),
    )
    history = [row for row in records if row.planner == "history_aware"]
    shortest = [row for row in records if row.planner == "shortest"]

    assert history
    assert all(row.matches_analytic_boundary for row in history)
    assert all(row.matches_analytic_boundary for row in shortest)
    assert all(not row.chose_detour for row in shortest)


def test_history_conditioned_reliability_changes_only_after_trigger() -> None:
    grid, start, goal, safe, model = commitment_phase_world(2, 0.7)
    direct = commitment_aware_astar(
        grid, start, goal, safe_cells=safe, hazard_model=model,
        mode=CommitmentPlannerMode.SHORTEST,
    )
    robust = commitment_aware_astar(
        grid, start, goal, safe_cells=safe, hazard_model=model,
        mode=CommitmentPlannerMode.HISTORY_AWARE,
        config=CommitmentAwareAStarConfig(recoverability_weight=16.0),
    )

    assert direct.path[-1] == robust.path[-1] == goal
    assert direct.final_return_probability == pytest.approx(0.3)
    assert robust.final_return_probability == pytest.approx(1.0)


def test_phase_summary_reports_perfect_boundary_match() -> None:
    summary = summarize_commitment_phase(
        run_commitment_phase_benchmark(
            detour_depths=(1, 2),
            closure_probabilities=(0.3, 0.7),
            recoverability_weights=(2.0, 8.0, 16.0),
        )
    )
    assert summary["shortest"]["analytic_boundary_match_rate"] == pytest.approx(1.0)
    assert summary["history_aware"]["analytic_boundary_match_rate"] == pytest.approx(1.0)
