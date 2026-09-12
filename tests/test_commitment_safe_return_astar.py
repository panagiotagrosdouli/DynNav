from __future__ import annotations

import pytest

from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.planners.commitment_safe_return_astar import (
    SafeReturnConstraintConfig,
    commitment_safe_return_astar,
)
from dynnav.planners.grid_map import GridMap


def _problem(probability: float):
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


def test_strict_safe_return_threshold_forces_detour() -> None:
    grid, start, goal, model = _problem(0.8)
    result = commitment_safe_return_astar(
        grid,
        start,
        goal,
        safe_cells={start},
        hazard_model=model,
        config=SafeReturnConstraintConfig(minimum_return_probability=0.9),
    )

    assert result.success
    assert result.geometric_length == 5
    assert result.activated_closure_count == 0
    assert result.final_return_probability == pytest.approx(1.0)
    assert result.minimum_return_probability >= 0.9
    assert result.rejected_transitions > 0


def test_loose_threshold_allows_direct_commitment() -> None:
    grid, start, goal, model = _problem(0.8)
    result = commitment_safe_return_astar(
        grid,
        start,
        goal,
        safe_cells={start},
        hazard_model=model,
        config=SafeReturnConstraintConfig(minimum_return_probability=0.1),
    )

    assert result.success
    assert result.geometric_length == 3
    assert result.activated_closure_count == 1
    assert result.final_return_probability == pytest.approx(0.2)


def test_threshold_can_make_goal_infeasible_when_all_routes_trigger() -> None:
    grid = GridMap.from_obstacles(4, 1)
    start, goal = (0, 0), (3, 0)
    model = CommitmentHazardModel(
        (
            CommitmentClosure(
                trigger=((2, 0), (3, 0)),
                closure_cell=(1, 0),
                closure_probability=0.8,
            ),
        )
    )
    result = commitment_safe_return_astar(
        grid,
        start,
        goal,
        safe_cells={start},
        hazard_model=model,
        config=SafeReturnConstraintConfig(minimum_return_probability=0.9),
    )

    assert not result.success


def test_threshold_validation() -> None:
    with pytest.raises(ValueError):
        SafeReturnConstraintConfig(minimum_return_probability=1.1).validate()
