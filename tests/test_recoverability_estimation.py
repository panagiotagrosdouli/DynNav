from __future__ import annotations

import pytest

from dynnav.planners.grid_map import GridMap
from dynnav.recoverability_belief import TopologyHazardBelief, exact_safe_return_probability
from dynnav.recoverability_estimation import (
    most_reliable_return_path,
    two_hazard_disjoint_return_paths,
)


def test_most_reliable_path_is_exact_for_single_future_closure() -> None:
    grid = GridMap.from_obstacles(5, 1)
    hazard = TopologyHazardBelief({(2, 0): 0.35})

    estimate = most_reliable_return_path(grid, (4, 0), {(0, 0)}, hazard)
    exact = exact_safe_return_probability(grid, (4, 0), {(0, 0)}, hazard)

    assert estimate.probability == pytest.approx(0.65)
    assert estimate.probability == pytest.approx(exact)
    assert estimate.path[0] == (4, 0)
    assert estimate.path[-1] == (0, 0)


def test_most_reliable_path_is_conservative_when_redundancy_matters() -> None:
    grid = GridMap.from_obstacles(3, 3, obstacles={(1, 1)})
    hazard = TopologyHazardBelief({(1, 0): 0.2, (1, 2): 0.3})

    estimate = most_reliable_return_path(grid, (2, 1), {(0, 1)}, hazard)
    exact = exact_safe_return_probability(grid, (2, 1), {(0, 1)}, hazard)

    assert estimate.probability == pytest.approx(0.8)
    assert exact == pytest.approx(0.94)
    assert estimate.probability < exact


def test_two_path_estimator_recovers_parallel_closure_reliability() -> None:
    grid = GridMap.from_obstacles(3, 3, obstacles={(1, 1)})
    hazard = TopologyHazardBelief({(1, 0): 0.2, (1, 2): 0.3})

    estimate = two_hazard_disjoint_return_paths(grid, (2, 1), {(0, 1)}, hazard)
    exact = exact_safe_return_probability(grid, (2, 1), {(0, 1)}, hazard)

    assert len(estimate.paths) == 2
    assert estimate.probability == pytest.approx(0.94)
    assert estimate.probability == pytest.approx(exact)


def test_two_path_estimator_does_not_double_count_shared_closure_hazard() -> None:
    grid = GridMap.from_obstacles(5, 3, obstacles={(2, 0), (2, 2)})
    hazard = TopologyHazardBelief({(2, 1): 0.4})

    estimate = two_hazard_disjoint_return_paths(grid, (4, 1), {(0, 1)}, hazard)
    exact = exact_safe_return_probability(grid, (4, 1), {(0, 1)}, hazard)

    assert len(estimate.paths) == 1
    assert estimate.probability == pytest.approx(0.6)
    assert estimate.probability == pytest.approx(exact)


def test_estimator_prefers_more_reliable_of_two_return_routes() -> None:
    grid = GridMap.from_obstacles(3, 3, obstacles={(1, 1)})
    hazard = TopologyHazardBelief({(1, 0): 0.6, (1, 2): 0.1})

    estimate = most_reliable_return_path(grid, (2, 1), {(0, 1)}, hazard)

    assert estimate.probability == pytest.approx(0.9)
    assert (1, 2) in estimate.path
    assert (1, 0) not in estimate.path


def test_estimator_conditions_current_hazard_cell_usable() -> None:
    grid = GridMap.from_obstacles(3, 1)
    hazard = TopologyHazardBelief({(2, 0): 0.5})

    estimate = most_reliable_return_path(grid, (2, 0), {(0, 0)}, hazard)

    assert estimate.probability == pytest.approx(1.0)


def test_estimator_keeps_other_hazards_after_conditioning_current_cell() -> None:
    grid = GridMap.from_obstacles(4, 1)
    hazard = TopologyHazardBelief({(3, 0): 0.5, (1, 0): 0.25})

    estimate = most_reliable_return_path(grid, (3, 0), {(0, 0)}, hazard)

    assert estimate.probability == pytest.approx(0.75)


def test_estimator_reports_zero_if_all_return_routes_certainly_close() -> None:
    grid = GridMap.from_obstacles(3, 1)
    hazard = TopologyHazardBelief({(1, 0): 1.0})

    estimate = most_reliable_return_path(grid, (2, 0), {(0, 0)}, hazard)

    assert estimate.probability == 0.0
    assert estimate.path == ()
