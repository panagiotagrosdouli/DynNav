"""Past executed triggers must survive replanning in both return baselines."""

import pytest

from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.planners.commitment_cut_astar import commitment_cut_astar
from dynnav.planners.commitment_safe_return_astar import commitment_safe_return_astar
from dynnav.planners.grid_map import GridMap


def problem():
    # The robot already crossed the trigger and bridge; all routes back to
    # safety now depend on the bridge remaining open with probability 0.2.
    grid = GridMap.from_obstacles(4, 1)
    model = CommitmentHazardModel((CommitmentClosure(((0, 0), (1, 0)), (1, 0), 0.8),))
    return grid, model


def test_cut_replanning_retains_known_bridge_hazard():
    grid, model = problem()
    empty = commitment_cut_astar(grid, (2, 0), (3, 0), safe_cells={(0, 0)}, hazard_model=model)
    history = frozenset({0})
    retained = commitment_cut_astar(
        grid, (2, 0), (3, 0), safe_cells={(0, 0)}, hazard_model=model,
        initial_activated_closures=history,
    )
    assert empty.final_return_upper_bound == 1.0
    assert retained.success
    assert retained.final_return_upper_bound == pytest.approx(0.2)
    assert retained.activated_closure_count == 1
    assert history == frozenset({0})


def test_hard_constraint_rejects_already_unsafe_replanning_state():
    grid, model = problem()
    assert commitment_safe_return_astar(
        grid, (2, 0), (3, 0), safe_cells={(0, 0)}, hazard_model=model,
    ).success
    retained = commitment_safe_return_astar(
        grid, (2, 0), (3, 0), safe_cells={(0, 0)}, hazard_model=model,
        initial_activated_closures=frozenset({0}),
    )
    assert not retained.success
    assert retained.nodes_expanded == 0
    assert retained.activated_closure_count == 1


@pytest.mark.parametrize("planner", [commitment_cut_astar, commitment_safe_return_astar])
@pytest.mark.parametrize("index", [-1, 1])
def test_invalid_prior_hazard_is_rejected(planner, index):
    grid, model = problem()
    with pytest.raises(ValueError, match="out of range"):
        planner(grid, (2, 0), (3, 0), hazard_model=model, initial_activated_closures=frozenset({index}))
