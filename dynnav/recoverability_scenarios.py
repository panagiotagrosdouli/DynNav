"""Exact safe-return oracle for correlated future topology-closure scenarios."""
from __future__ import annotations

from dataclasses import dataclass

from dynnav.planners.grid_map import GridCell, GridMap
from dynnav.recoverability_belief import _can_reach_safe_region


@dataclass(frozen=True)
class ClosureScenario:
    closed_cells: frozenset[GridCell]
    probability: float


@dataclass(frozen=True)
class TopologyScenarioBelief:
    scenarios: tuple[ClosureScenario, ...]

    def validate(self, grid: GridMap, *, tolerance: float = 1e-9) -> None:
        if not self.scenarios:
            raise ValueError("at least one closure scenario is required")
        total = 0.0
        for scenario in self.scenarios:
            if not 0.0 <= scenario.probability <= 1.0:
                raise ValueError("scenario probability must be in [0, 1]")
            total += scenario.probability
            for cell in scenario.closed_cells:
                if not grid.in_bounds(cell):
                    raise ValueError(f"scenario closure outside grid: {cell}")
                if not grid.passable(cell):
                    raise ValueError(f"scenario closure is already blocked: {cell}")
        if abs(total - 1.0) > tolerance:
            raise ValueError(f"scenario probabilities must sum to 1, got {total}")


def exact_scenario_safe_return_probability(
    grid: GridMap,
    start: GridCell,
    safe_cells: set[GridCell],
    belief: TopologyScenarioBelief,
) -> float:
    """Return exact safe-return probability under arbitrary correlated scenarios.

    The current robot cell is conditioned usable at the evaluation instant, as
    in the independent Bernoulli oracle. A scenario may close any number of
    other currently-free cells jointly.
    """
    grid.validate()
    belief.validate(grid)
    probability = 0.0
    for scenario in belief.scenarios:
        obstacles = set(grid.obstacles)
        obstacles.update(cell for cell in scenario.closed_cells if cell != start)
        realized = GridMap.from_obstacles(
            grid.width,
            grid.height,
            obstacles=obstacles,
            risk=grid.risk,
            uncertainty=grid.uncertainty,
        )
        if _can_reach_safe_region(realized, start, safe_cells):
            probability += scenario.probability
    return min(1.0, max(0.0, probability))
