from __future__ import annotations

import pytest

from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.planners.commitment_aware_astar import (
    CommitmentAwareAStarConfig,
    CommitmentPlannerMode,
    commitment_aware_astar,
)
from dynnav.planners.grid_map import GridMap
from dynnav.planners.robust_commitment_astar import (
    RobustCommitmentAStarConfig,
    robust_commitment_astar,
)


def _two_return_corridor_problem():
    width, height = 5, 3
    free = {(x, 0) for x in range(width)}
    free.update({(x, 2) for x in range(width)})
    free.update({(0, 1), (4, 1)})
    obstacles = {
        (x, y)
        for x in range(width)
        for y in range(height)
        if (x, y) not in free
    }
    grid = GridMap.from_obstacles(width, height, obstacles=obstacles)
    start = (0, 0)
    goal = (4, 0)
    model = CommitmentHazardModel(
        (
            CommitmentClosure(
                trigger=((2, 0), (3, 0)),
                closure_cell=(1, 0),
                closure_probability=0.5,
            ),
            CommitmentClosure(
                trigger=((3, 0), (4, 0)),
                closure_cell=(1, 2),
                closure_probability=0.5,
            ),
        )
    )
    return grid, start, goal, model


def test_dependence_ambiguity_changes_route_choice() -> None:
    grid, start, goal, model = _two_return_corridor_problem()

    independent = commitment_aware_astar(
        grid,
        start,
        goal,
        safe_cells={start},
        hazard_model=model,
        mode=CommitmentPlannerMode.HISTORY_AWARE,
        config=CommitmentAwareAStarConfig(recoverability_weight=12.0),
    )
    robust = robust_commitment_astar(
        grid,
        start,
        goal,
        safe_cells={start},
        hazard_model=model,
        config=RobustCommitmentAStarConfig(recoverability_weight=12.0),
    )

    assert independent.success
    assert robust.success

    assert independent.geometric_length == 4
    assert independent.activated_closure_count == 2
    assert independent.final_return_probability == pytest.approx(0.75)

    assert robust.geometric_length == 8
    assert robust.activated_hazard_count == 0
    assert robust.final_worst_case_return_probability == pytest.approx(1.0)
