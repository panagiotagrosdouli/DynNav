from __future__ import annotations

import pytest

from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.planners.approx_commitment_aware_astar import (
    ApproxCommitmentAStarConfig,
    ApproxCommitmentMode,
    approx_commitment_aware_astar,
)
from dynnav.planners.commitment_aware_astar import (
    CommitmentAwareAStarConfig,
    CommitmentPlannerMode,
    commitment_aware_astar,
)
from dynnav.planners.grid_map import GridMap


def _single_trigger_trap(probability: float = 0.8):
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


@pytest.mark.parametrize(
    "mode",
    [ApproxCommitmentMode.SINGLE_RETURN, ApproxCommitmentMode.REDUNDANT_RETURN],
)
def test_approximate_history_planner_avoids_high_probability_trigger(mode) -> None:
    grid, start, goal, model = _single_trigger_trap(0.8)

    result = approx_commitment_aware_astar(
        grid,
        start,
        goal,
        safe_cells={start},
        hazard_model=model,
        mode=mode,
        config=ApproxCommitmentAStarConfig(recoverability_weight=4.0),
    )

    assert result.success
    assert result.geometric_length == 5
    assert result.activated_closure_count == 0
    assert result.minimum_estimated_return_probability == pytest.approx(1.0)


def test_approximate_and_exact_planners_agree_on_single_trigger_trap() -> None:
    grid, start, goal, model = _single_trigger_trap(0.8)

    exact = commitment_aware_astar(
        grid,
        start,
        goal,
        safe_cells={start},
        hazard_model=model,
        mode=CommitmentPlannerMode.HISTORY_AWARE,
        config=CommitmentAwareAStarConfig(recoverability_weight=4.0),
    )
    approximate = approx_commitment_aware_astar(
        grid,
        start,
        goal,
        safe_cells={start},
        hazard_model=model,
        mode=ApproxCommitmentMode.REDUNDANT_RETURN,
        config=ApproxCommitmentAStarConfig(recoverability_weight=4.0),
    )

    assert approximate.path == exact.path
    assert approximate.geometric_length == exact.geometric_length
    assert approximate.activated_closure_count == exact.activated_closure_count
    assert approximate.final_estimated_return_probability == pytest.approx(
        exact.final_return_probability
    )


def test_low_probability_trigger_keeps_direct_route() -> None:
    grid, start, goal, model = _single_trigger_trap(0.05)

    result = approx_commitment_aware_astar(
        grid,
        start,
        goal,
        safe_cells={start},
        hazard_model=model,
        mode=ApproxCommitmentMode.REDUNDANT_RETURN,
        config=ApproxCommitmentAStarConfig(recoverability_weight=4.0),
    )

    assert result.success
    assert result.geometric_length == 3
    assert result.activated_closure_count == 1
    assert result.final_estimated_return_probability == pytest.approx(0.95)


def test_non_enumerative_planner_operates_beyond_exact_oracle_guard() -> None:
    # Construct 17 independent trigger definitions. Their presence exceeds the
    # exact planner's configured outcome-enumeration guard. They lie off the
    # direct mission route, so this test isolates the algorithmic guard rather
    # than claiming that augmented-history search itself is polynomial.
    grid = GridMap.from_obstacles(20, 2)
    closures = tuple(
        CommitmentClosure(
            trigger=((index, 1), (index + 1, 1)),
            closure_cell=(index, 1),
            closure_probability=0.2,
        )
        for index in range(17)
    )
    model = CommitmentHazardModel(closures)

    with pytest.raises(ValueError, match="exceeds max_hazard_cells"):
        commitment_aware_astar(
            grid,
            (0, 0),
            (19, 0),
            safe_cells={(0, 0)},
            hazard_model=model,
            mode=CommitmentPlannerMode.HISTORY_AWARE,
        )

    result = approx_commitment_aware_astar(
        grid,
        (0, 0),
        (19, 0),
        safe_cells={(0, 0)},
        hazard_model=model,
        mode=ApproxCommitmentMode.REDUNDANT_RETURN,
    )

    assert result.success
    assert result.geometric_length == 19
    assert result.activated_closure_count == 0
