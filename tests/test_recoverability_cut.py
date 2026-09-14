from __future__ import annotations

import pytest

from dynnav.planners.grid_map import GridMap
from dynnav.recoverability_belief import TopologyHazardBelief, exact_safe_return_probability
from dynnav.recoverability_cut import critical_return_cut_upper_bound


def test_single_bridge_cut_matches_exact_oracle() -> None:
    grid = GridMap.from_obstacles(5, 1)
    cell = (4, 0)
    safe = {(0, 0)}
    hazard = TopologyHazardBelief({(2, 0): 0.7})

    estimate = critical_return_cut_upper_bound(grid, cell, safe, hazard)
    exact = exact_safe_return_probability(grid, cell, safe, hazard, max_hazard_cells=1)

    assert estimate.critical_hazard_cells == ((2, 0),)
    assert estimate.probability_upper_bound == pytest.approx(0.3)
    assert estimate.probability_upper_bound == pytest.approx(exact)


def test_two_series_critical_cells_multiply_and_match_exact() -> None:
    grid = GridMap.from_obstacles(6, 1)
    cell = (5, 0)
    safe = {(0, 0)}
    hazard = TopologyHazardBelief({(2, 0): 0.2, (4, 0): 0.5})

    estimate = critical_return_cut_upper_bound(grid, cell, safe, hazard)
    exact = exact_safe_return_probability(grid, cell, safe, hazard, max_hazard_cells=2)

    assert set(estimate.critical_hazard_cells) == {(2, 0), (4, 0)}
    assert estimate.probability_upper_bound == pytest.approx(0.4)
    assert estimate.probability_upper_bound == pytest.approx(exact)


def test_parallel_two_cell_cut_is_optimistic_as_documented() -> None:
    # Two independent corridors connect left and right. Neither middle hazard is
    # individually critical, but closing both disconnects the robot.
    free = {(0, 0), (1, 0), (2, 0), (0, 2), (1, 2), (2, 2), (0, 1), (2, 1)}
    obstacles = {(x, y) for x in range(3) for y in range(3) if (x, y) not in free}
    grid = GridMap.from_obstacles(3, 3, obstacles=obstacles)
    cell = (2, 1)
    safe = {(0, 1)}
    hazard = TopologyHazardBelief({(1, 0): 0.5, (1, 2): 0.5})

    estimate = critical_return_cut_upper_bound(grid, cell, safe, hazard)
    exact = exact_safe_return_probability(grid, cell, safe, hazard, max_hazard_cells=2)

    assert estimate.critical_hazard_cells == ()
    assert estimate.probability_upper_bound == pytest.approx(1.0)
    assert exact == pytest.approx(0.75)
    assert estimate.probability_upper_bound >= exact


def test_current_hazard_cell_is_conditioned_usable() -> None:
    grid = GridMap.from_obstacles(3, 1)
    hazard = TopologyHazardBelief({(2, 0): 0.9, (1, 0): 0.4})
    estimate = critical_return_cut_upper_bound(grid, (2, 0), {(0, 0)}, hazard)

    assert estimate.critical_hazard_cells == ((1, 0),)
    assert estimate.probability_upper_bound == pytest.approx(0.6)
