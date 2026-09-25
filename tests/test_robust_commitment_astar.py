from __future__ import annotations

import pytest

from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.planners.grid_map import GridMap
from dynnav.planners.robust_commitment_astar import (
    RobustCommitmentAStarConfig,
    robust_commitment_astar,
)


def test_robust_planner_preserves_return_on_single_hazard_trap() -> None:
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

    result = robust_commitment_astar(
        grid,
        start,
        goal,
        safe_cells={start},
        hazard_model=model,
        config=RobustCommitmentAStarConfig(recoverability_weight=4.0),
    )

    assert result.success
    assert result.geometric_length == 5
    assert result.activated_hazard_count == 0
    assert result.final_worst_case_return_probability == pytest.approx(1.0)
