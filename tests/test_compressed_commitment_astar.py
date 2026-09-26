from __future__ import annotations

import pytest

from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.planners.commitment_aware_astar import (
    CommitmentAwareAStarConfig,
    CommitmentPlannerMode,
    commitment_aware_astar,
)
from dynnav.planners.compressed_commitment_astar import (
    CompressedCommitmentAStarConfig,
    compressed_commitment_astar,
)
from dynnav.planners.grid_map import GridMap


def test_compressed_planner_preserves_path_cost_and_return_probability() -> None:
    grid = GridMap.from_obstacles(5, 1)
    start = (0, 0)
    goal = (4, 0)
    model = CommitmentHazardModel(
        (
            CommitmentClosure(
                trigger=((1, 0), (2, 0)),
                closure_cell=(1, 0),
                closure_probability=0.5,
            ),
            CommitmentClosure(
                trigger=((2, 0), (3, 0)),
                closure_cell=(1, 0),
                closure_probability=0.5,
            ),
        )
    )

    raw = commitment_aware_astar(
        grid,
        start,
        goal,
        safe_cells={start},
        hazard_model=model,
        mode=CommitmentPlannerMode.HISTORY_AWARE,
        config=CommitmentAwareAStarConfig(recoverability_weight=2.0),
    )
    compressed = compressed_commitment_astar(
        grid,
        start,
        goal,
        safe_cells={start},
        hazard_model=model,
        config=CompressedCommitmentAStarConfig(recoverability_weight=2.0),
    )

    assert raw.success and compressed.success
    assert compressed.path == raw.path
    assert compressed.cost == pytest.approx(raw.cost)
    assert compressed.final_return_probability == pytest.approx(raw.final_return_probability)
    assert compressed.minimum_return_probability == pytest.approx(raw.minimum_return_probability)

    assert raw.activated_closure_count == 2
    assert compressed.activated_event_count == 1
    assert compressed.raw_hazard_count == 2
    assert compressed.quotient_event_count == 1
