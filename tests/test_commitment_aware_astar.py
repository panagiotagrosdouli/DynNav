from __future__ import annotations

import pytest

from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.planners.commitment_aware_astar import (
    CommitmentAwareAStarConfig,
    CommitmentPlannerMode,
    commitment_aware_astar,
)
from dynnav.planners.grid_map import GridMap


def _trap_problem():
    # The left safe region is connected to a right-side loop through the sole
    # bridge (1,1). The direct edge into the goal is a commitment trigger: using
    # it can close the bridge behind the robot with probability 0.8. A two-step
    # detour through the upper loop reaches the same goal without activating it.
    grid = GridMap.from_obstacles(4, 3, obstacles={(1, 0), (1, 2)})
    start = (0, 1)
    goal = (3, 1)
    model = CommitmentHazardModel(
        (
            CommitmentClosure(
                trigger=((2, 1), (3, 1)),
                closure_cell=(1, 1),
                closure_probability=0.8,
            ),
        )
    )
    return grid, start, goal, model


def test_shortest_planner_commits_to_risky_direct_edge() -> None:
    grid, start, goal, model = _trap_problem()

    result = commitment_aware_astar(
        grid,
        start,
        goal,
        safe_cells={start},
        hazard_model=model,
        mode=CommitmentPlannerMode.SHORTEST,
    )

    assert result.success
    assert result.geometric_length == 3
    assert result.activated_closure_count == 1
    assert result.final_return_probability == pytest.approx(0.2)


def test_history_aware_planner_takes_detour_to_preserve_return_reliability() -> None:
    grid, start, goal, model = _trap_problem()

    result = commitment_aware_astar(
        grid,
        start,
        goal,
        safe_cells={start},
        hazard_model=model,
        mode=CommitmentPlannerMode.HISTORY_AWARE,
        config=CommitmentAwareAStarConfig(recoverability_weight=4.0),
    )

    assert result.success
    assert result.geometric_length == 5
    assert result.activated_closure_count == 0
    assert result.final_return_probability == pytest.approx(1.0)
    assert result.path[-1] == goal


def test_zero_recoverability_weight_collapses_to_direct_geometric_choice() -> None:
    grid, start, goal, model = _trap_problem()

    result = commitment_aware_astar(
        grid,
        start,
        goal,
        safe_cells={start},
        hazard_model=model,
        mode=CommitmentPlannerMode.HISTORY_AWARE,
        config=CommitmentAwareAStarConfig(recoverability_weight=0.0),
    )

    assert result.geometric_length == 3
    assert result.activated_closure_count == 1


def test_low_closure_probability_does_not_force_unnecessary_detour() -> None:
    grid = GridMap.from_obstacles(4, 3, obstacles={(1, 0), (1, 2)})
    start, goal = (0, 1), (3, 1)
    model = CommitmentHazardModel(
        (
            CommitmentClosure(
                trigger=((2, 1), (3, 1)),
                closure_cell=(1, 1),
                closure_probability=0.05,
            ),
        )
    )

    result = commitment_aware_astar(
        grid,
        start,
        goal,
        safe_cells={start},
        hazard_model=model,
        mode=CommitmentPlannerMode.HISTORY_AWARE,
        config=CommitmentAwareAStarConfig(recoverability_weight=4.0),
    )

    assert result.success
    assert result.geometric_length == 3
    assert result.final_return_probability == pytest.approx(0.95)
