from __future__ import annotations

import pytest

from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.planners.commitment_aware_astar import (
    CommitmentAwareAStarConfig,
    commitment_aware_astar,
)
from dynnav.planners.grid_map import GridMap


def _model() -> tuple[GridMap, CommitmentHazardModel]:
    grid = GridMap.from_obstacles(width=5, height=3, obstacles=())
    model = CommitmentHazardModel(
        (
            CommitmentClosure(
                trigger=((1, 1), (2, 1)),
                closure_cell=(0, 1),
                closure_probability=0.8,
            ),
        )
    )
    return grid, model


def test_online_replan_preserves_already_activated_hazard() -> None:
    grid, model = _model()
    result = commitment_aware_astar(
        grid,
        (2, 1),
        (4, 1),
        safe_cells={(0, 1)},
        hazard_model=model,
        config=CommitmentAwareAStarConfig(recoverability_weight=4.0),
        initial_activated_closures=frozenset({0}),
    )

    assert result.success
    assert result.activated_closure_count == 1
    assert result.final_return_probability == pytest.approx(0.2)


def test_online_replan_rejects_unknown_hazard_indices() -> None:
    grid, model = _model()
    with pytest.raises(ValueError, match="out of range"):
        commitment_aware_astar(
            grid,
            (2, 1),
            (4, 1),
            safe_cells={(0, 1)},
            hazard_model=model,
            initial_activated_closures=frozenset({1}),
        )
