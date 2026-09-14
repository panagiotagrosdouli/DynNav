from __future__ import annotations

import pytest

from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.planners.commitment_aware_astar import (
    CommitmentAwareAStarConfig,
    CommitmentPlannerMode,
    commitment_aware_astar,
)
from dynnav.planners.commitment_cut_astar import (
    CommitmentCutAStarConfig,
    commitment_cut_astar,
)
from dynnav.planners.grid_map import GridMap


def _single_cut_problem(probability: float = 0.8):
    grid = GridMap.from_obstacles(4, 3, obstacles={(1, 0), (1, 2)})
    start, goal = (0, 1), (3, 1)
    model = CommitmentHazardModel(
        (
            CommitmentClosure(
                trigger=((2, 1), (3, 1)),
                closure_cell=(1, 1),
                closure_probability=probability,
            ),
        )
    )
    return grid, start, goal, model


def test_cut_planner_matches_exact_choice_for_single_critical_bridge() -> None:
    grid, start, goal, model = _single_cut_problem(0.8)
    exact = commitment_aware_astar(
        grid, start, goal, safe_cells={start}, hazard_model=model,
        mode=CommitmentPlannerMode.HISTORY_AWARE,
        config=CommitmentAwareAStarConfig(recoverability_weight=4.0),
    )
    approx = commitment_cut_astar(
        grid, start, goal, safe_cells={start}, hazard_model=model,
        config=CommitmentCutAStarConfig(recoverability_weight=4.0),
    )

    assert exact.success and approx.success
    assert exact.geometric_length == approx.geometric_length == 5
    assert exact.activated_closure_count == approx.activated_closure_count == 0
    assert approx.final_return_upper_bound == pytest.approx(1.0)


def test_cut_planner_keeps_direct_route_when_hazard_is_weak() -> None:
    grid, start, goal, model = _single_cut_problem(0.05)
    approx = commitment_cut_astar(
        grid, start, goal, safe_cells={start}, hazard_model=model,
        config=CommitmentCutAStarConfig(recoverability_weight=4.0),
    )

    assert approx.success
    assert approx.geometric_length == 3
    assert approx.activated_closure_count == 1
    assert approx.final_return_upper_bound == pytest.approx(0.95)


def test_cut_upper_bound_can_miss_joint_parallel_cut() -> None:
    # Two triggered closure cells form a joint cut, but neither one is
    # individually critical. The approximation therefore remains optimistic.
    free = {
        (0, 1), (1, 1), (2, 1), (3, 1),
        (2, 0), (3, 0), (2, 2), (3, 2),
    }
    obstacles = {(x, y) for x in range(4) for y in range(3) if (x, y) not in free}
    grid = GridMap.from_obstacles(4, 3, obstacles=obstacles)
    start, goal = (0, 1), (3, 1)
    model = CommitmentHazardModel(
        (
            CommitmentClosure(((2, 1), (2, 0)), (1, 1), 0.5),
            CommitmentClosure(((2, 0), (3, 0)), (2, 1), 0.5),
        )
    )

    # This test is intentionally limited to checking the implementation remains
    # numerically valid in a regime where single-cell cut reasoning is incomplete.
    result = commitment_cut_astar(
        grid, start, goal, safe_cells={start}, hazard_model=model,
        config=CommitmentCutAStarConfig(recoverability_weight=4.0),
    )
    assert result.success
    assert 0.0 <= result.final_return_upper_bound <= 1.0
