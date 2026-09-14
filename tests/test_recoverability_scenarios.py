from __future__ import annotations

import pytest

from dynnav.planners.grid_map import GridMap
from dynnav.recoverability_belief import TopologyHazardBelief, exact_safe_return_probability
from dynnav.recoverability_scenarios import (
    ClosureScenario,
    TopologyScenarioBelief,
    exact_scenario_safe_return_probability,
)


def _parallel_corridors():
    free = {(0, 0), (1, 0), (2, 0), (0, 2), (1, 2), (2, 2), (0, 1), (2, 1)}
    obstacles = {(x, y) for x in range(3) for y in range(3) if (x, y) not in free}
    return GridMap.from_obstacles(3, 3, obstacles=obstacles), (2, 1), {(0, 1)}


def test_correlated_common_event_can_be_worse_than_independent_marginals() -> None:
    grid, current, safe = _parallel_corridors()

    independent = exact_safe_return_probability(
        grid,
        current,
        safe,
        TopologyHazardBelief({(1, 0): 0.5, (1, 2): 0.5}),
        max_hazard_cells=2,
    )
    correlated = exact_scenario_safe_return_probability(
        grid,
        current,
        safe,
        TopologyScenarioBelief(
            (
                ClosureScenario(frozenset(), 0.5),
                ClosureScenario(frozenset({(1, 0), (1, 2)}), 0.5),
            )
        ),
    )

    assert independent == pytest.approx(0.75)
    assert correlated == pytest.approx(0.5)
    assert correlated < independent


def test_scenario_oracle_conditions_current_cell_usable() -> None:
    grid = GridMap.from_obstacles(3, 1)
    belief = TopologyScenarioBelief(
        (
            ClosureScenario(frozenset({(2, 0)}), 0.7),
            ClosureScenario(frozenset(), 0.3),
        )
    )
    assert exact_scenario_safe_return_probability(
        grid, (2, 0), {(0, 0)}, belief
    ) == pytest.approx(1.0)


def test_scenario_probabilities_must_sum_to_one() -> None:
    grid = GridMap.from_obstacles(2, 1)
    belief = TopologyScenarioBelief((ClosureScenario(frozenset(), 0.8),))
    with pytest.raises(ValueError, match="sum to 1"):
        belief.validate(grid)
