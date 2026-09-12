from __future__ import annotations

import pytest

from dynnav.planners.grid_map import GridMap
from dynnav.recoverability_belief import TopologyBelief, exact_safe_return_probability
from dynnav.recoverability_estimation import most_reliable_return_path


def test_most_reliable_path_is_exact_for_single_bridge_topology() -> None:
    grid = GridMap.from_obstacles(5, 1)
    belief = TopologyBelief({(2, 0): 0.35})

    estimate = most_reliable_return_path(grid, (4, 0), {(0, 0)}, belief)
    exact = exact_safe_return_probability(grid, (4, 0), {(0, 0)}, belief)

    assert estimate.probability == pytest.approx(0.65)
    assert estimate.probability == pytest.approx(exact)
    assert estimate.path[0] == (4, 0)
    assert estimate.path[-1] == (0, 0)


def test_most_reliable_path_is_conservative_when_redundancy_matters() -> None:
    grid = GridMap.from_obstacles(3, 3, obstacles={(1, 1)})
    belief = TopologyBelief({(1, 0): 0.2, (1, 2): 0.3})

    estimate = most_reliable_return_path(grid, (2, 1), {(0, 1)}, belief)
    exact = exact_safe_return_probability(grid, (2, 1), {(0, 1)}, belief)

    assert estimate.probability == pytest.approx(0.8)
    assert exact == pytest.approx(0.94)
    assert estimate.probability < exact


def test_estimator_prefers_more_reliable_of_two_return_routes() -> None:
    grid = GridMap.from_obstacles(3, 3, obstacles={(1, 1)})
    belief = TopologyBelief({(1, 0): 0.6, (1, 2): 0.1})

    estimate = most_reliable_return_path(grid, (2, 1), {(0, 1)}, belief)

    assert estimate.probability == pytest.approx(0.9)
    assert (1, 2) in estimate.path
    assert (1, 0) not in estimate.path


def test_estimator_conditions_current_robot_cell_free() -> None:
    grid = GridMap.from_obstacles(3, 1)
    belief = TopologyBelief({(2, 0): 0.5})

    with pytest.raises(ValueError, match="conditioned free"):
        most_reliable_return_path(grid, (2, 0), {(0, 0)}, belief)


def test_estimator_reports_zero_if_all_return_routes_are_certainly_blocked() -> None:
    grid = GridMap.from_obstacles(3, 1)
    belief = TopologyBelief({(1, 0): 1.0})

    estimate = most_reliable_return_path(grid, (2, 0), {(0, 0)}, belief)

    assert estimate.probability == 0.0
    assert estimate.path == ()
