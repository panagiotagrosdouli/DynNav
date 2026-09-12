from __future__ import annotations

import pytest

from dynnav.commitment_hazard import (
    CommitmentClosure,
    CommitmentHazardModel,
    exact_history_conditioned_return_probability,
)
from dynnav.planners.grid_map import GridMap
from dynnav.recoverability_belief import TopologyHazardBelief, exact_safe_return_probability


def test_same_geometric_state_can_have_different_recoverability_after_commitment() -> None:
    # A single bridge at (1,1) connects the safe region on the left to a loop on
    # the right. Both histories cross the bridge and end at the same state, but
    # only the lower loop activates a future closure of the bridge behind the robot.
    grid = GridMap.from_obstacles(4, 3, obstacles={(1, 0), (1, 2)})
    safe = {(0, 1)}
    current = (3, 1)
    model = CommitmentHazardModel(
        (
            CommitmentClosure(
                trigger=((2, 2), (3, 2)),
                closure_cell=(1, 1),
                closure_probability=0.8,
            ),
        )
    )

    uncommitted_path = ((0, 1), (1, 1), (2, 1), (2, 0), (3, 0), current)
    committed_path = ((0, 1), (1, 1), (2, 1), (2, 2), (3, 2), current)

    uncommitted = exact_history_conditioned_return_probability(
        grid, uncommitted_path, safe, model
    )
    committed = exact_history_conditioned_return_probability(
        grid, committed_path, safe, model
    )

    assert uncommitted == pytest.approx(1.0)
    assert committed == pytest.approx(0.2)


def test_state_only_oracle_cannot_represent_trigger_history_without_augmented_state() -> None:
    grid = GridMap.from_obstacles(4, 3, obstacles={(1, 0), (1, 2)})
    current = (3, 1)
    safe = {(0, 1)}

    state_only = exact_safe_return_probability(
        grid,
        current,
        safe,
        TopologyHazardBelief({}),
    )

    assert state_only == pytest.approx(1.0)


def test_model_only_activates_hazards_from_traversed_directed_edges() -> None:
    grid = GridMap.from_obstacles(3, 2)
    closure = CommitmentClosure(
        trigger=((1, 0), (2, 0)),
        closure_cell=(1, 0),
        closure_probability=0.6,
    )
    model = CommitmentHazardModel((closure,))

    forward = model.activated_hazard_for_path(grid, ((0, 0), (1, 0), (2, 0)))
    reverse = model.activated_hazard_for_path(grid, ((2, 0), (1, 0), (0, 0)))

    assert forward.closure_probability == {(1, 0): 0.6}
    assert reverse.closure_probability == {}


def test_commitment_model_rejects_non_adjacent_trigger() -> None:
    grid = GridMap.from_obstacles(4, 1)
    model = CommitmentHazardModel(
        (
            CommitmentClosure(
                trigger=((0, 0), (2, 0)),
                closure_cell=(1, 0),
                closure_probability=0.5,
            ),
        )
    )

    with pytest.raises(ValueError, match="not a traversable grid edge"):
        model.validate(grid)
