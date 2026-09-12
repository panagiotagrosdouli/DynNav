from __future__ import annotations

import pytest

from dynnav.planners.grid_map import GridMap
from dynnav.recoverability import analyze_recoverability
from dynnav.recoverability_belief import (
    TopologyHazardBelief,
    exact_recoverability_degradation,
    exact_safe_return_probability,
)


def test_exact_oracle_matches_deterministic_connectivity_without_hazards():
    grid = GridMap.from_obstacles(4, 1)
    hazard = TopologyHazardBelief({})

    assert exact_safe_return_probability(grid, (3, 0), {(0, 0)}, hazard) == 1.0

    blocked = GridMap.from_obstacles(4, 1, obstacles={(1, 0)})
    assert exact_safe_return_probability(blocked, (3, 0), {(0, 0)}, hazard) == 0.0


def test_single_future_closure_has_analytic_safe_return_probability():
    grid = GridMap.from_obstacles(5, 1)
    hazard = TopologyHazardBelief({(2, 0): 0.35})

    probability = exact_safe_return_probability(grid, (4, 0), {(0, 0)}, hazard)

    assert probability == pytest.approx(0.65)


def test_parallel_future_closures_preserve_return_if_either_route_survives():
    grid = GridMap.from_obstacles(3, 3, obstacles={(1, 1)})
    hazard = TopologyHazardBelief({(1, 0): 0.2, (1, 2): 0.3})

    probability = exact_safe_return_probability(grid, (2, 1), {(0, 1)}, hazard)

    assert probability == pytest.approx(1.0 - 0.2 * 0.3)


def test_degradation_is_positive_after_committing_beyond_future_closure():
    grid = GridMap.from_obstacles(5, 1)
    hazard = TopologyHazardBelief({(2, 0): 0.4})

    degradation = exact_recoverability_degradation(
        grid,
        current=(1, 0),
        candidate=(3, 0),
        safe_cells={(0, 0)},
        hazard=hazard,
    )

    assert degradation == pytest.approx(0.4)


def test_structural_score_cannot_distinguish_different_closure_probabilities():
    grid = GridMap.from_obstacles(5, 1)
    candidate = (3, 0)
    safe_cells = {(0, 0)}

    structural = analyze_recoverability(grid, candidate, safe_cells)
    low_hazard = exact_safe_return_probability(
        grid,
        candidate,
        safe_cells,
        TopologyHazardBelief({(2, 0): 0.1}),
    )
    high_hazard = exact_safe_return_probability(
        grid,
        candidate,
        safe_cells,
        TopologyHazardBelief({(2, 0): 0.9}),
    )

    assert structural.irreversibility == analyze_recoverability(grid, candidate, safe_cells).irreversibility
    assert low_hazard == pytest.approx(0.9)
    assert high_hazard == pytest.approx(0.1)
    assert low_hazard > high_hazard


def test_hazard_model_rejects_cells_already_known_blocked():
    grid = GridMap.from_obstacles(3, 1, obstacles={(1, 0)})
    hazard = TopologyHazardBelief({(1, 0): 0.5})

    with pytest.raises(ValueError, match="already a known obstacle"):
        exact_safe_return_probability(grid, (2, 0), {(0, 0)}, hazard)


def test_current_robot_cell_must_be_conditioned_usable():
    grid = GridMap.from_obstacles(3, 1)
    hazard = TopologyHazardBelief({(2, 0): 0.5})

    with pytest.raises(ValueError, match="conditioned usable"):
        exact_safe_return_probability(grid, (2, 0), {(0, 0)}, hazard)


def test_exact_enumeration_guard_prevents_accidental_exponential_benchmark():
    grid = GridMap.from_obstacles(5, 1)
    hazard = TopologyHazardBelief({(1, 0): 0.1, (2, 0): 0.2, (3, 0): 0.3})

    with pytest.raises(ValueError, match="exact enumeration limited"):
        exact_safe_return_probability(
            grid,
            (4, 0),
            {(0, 0)},
            hazard,
            max_hazard_cells=2,
        )
