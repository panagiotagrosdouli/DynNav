from __future__ import annotations

import pytest

from dynnav.planners.grid_map import GridMap
from dynnav.recoverability_belief import (
    TopologyBelief,
    exact_recoverability_degradation,
    exact_safe_return_probability,
)


def test_exact_oracle_matches_deterministic_connectivity_without_uncertainty():
    grid = GridMap.from_obstacles(4, 1)
    belief = TopologyBelief({})

    assert exact_safe_return_probability(grid, (3, 0), {(0, 0)}, belief) == 1.0

    blocked = GridMap.from_obstacles(4, 1, obstacles={(1, 0)})
    assert exact_safe_return_probability(blocked, (3, 0), {(0, 0)}, belief) == 0.0


def test_single_uncertain_bridge_has_analytic_safe_return_probability():
    grid = GridMap.from_obstacles(5, 1)
    belief = TopologyBelief({(2, 0): 0.35})

    probability = exact_safe_return_probability(grid, (4, 0), {(0, 0)}, belief)

    assert probability == pytest.approx(0.65)


def test_parallel_uncertain_bridges_preserve_return_if_either_survives():
    obstacles = {(0, 1), (2, 1)}
    grid = GridMap.from_obstacles(3, 3, obstacles=obstacles)
    belief = TopologyBelief({(1, 0): 0.2, (1, 2): 0.3})

    probability = exact_safe_return_probability(grid, (2, 0), {(0, 0)}, belief)

    # The two crossings are independent; return fails only if both are blocked.
    assert probability == pytest.approx(1.0 - 0.2 * 0.3)


def test_degradation_is_positive_after_committing_beyond_uncertain_bridge():
    grid = GridMap.from_obstacles(5, 1)
    belief = TopologyBelief({(2, 0): 0.4})

    degradation = exact_recoverability_degradation(
        grid,
        current=(1, 0),
        candidate=(3, 0),
        safe_cells={(0, 0)},
        belief=belief,
    )

    assert degradation == pytest.approx(0.4)


def test_oracle_rejects_hidden_information_encoded_as_known_obstacle():
    grid = GridMap.from_obstacles(3, 1, obstacles={(1, 0)})
    belief = TopologyBelief({(1, 0): 0.5})

    with pytest.raises(ValueError, match="already a known obstacle"):
        exact_safe_return_probability(grid, (2, 0), {(0, 0)}, belief)


def test_exact_enumeration_guard_prevents_accidental_exponential_benchmark():
    grid = GridMap.from_obstacles(5, 1)
    belief = TopologyBelief({(1, 0): 0.1, (2, 0): 0.2, (3, 0): 0.3})

    with pytest.raises(ValueError, match="exact enumeration limited"):
        exact_safe_return_probability(
            grid,
            (4, 0),
            {(0, 0)},
            belief,
            max_uncertain_cells=2,
        )
