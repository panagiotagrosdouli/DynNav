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



def equal_marginal_common_cause_belief(
    closure_cells: tuple[GridCell, ...],
    *,
    marginal_probability: float,
    correlation: float,
) -> TopologyScenarioBelief:
    """Build the V4 equal-marginal positive-dependence closure model.

    With probability correlation all cells share one Bernoulli closure
    outcome. Otherwise they close independently. Every cell therefore retains
    marginal closure probability marginal_probability while dependence
    increases from independence at 0 to a common outcome at 1.
    """

    p = float(marginal_probability)
    rho = float(correlation)
    if not 0.0 <= p <= 1.0:
        raise ValueError("marginal_probability must be in [0, 1]")
    if not 0.0 <= rho <= 1.0:
        raise ValueError("correlation must be in [0, 1]")
    if len(set(closure_cells)) != len(closure_cells):
        raise ValueError("closure_cells must be unique")
    if not closure_cells:
        return TopologyScenarioBelief((ClosureScenario(frozenset(), 1.0),))

    from itertools import product

    mass: dict[frozenset[GridCell], float] = {}

    common_open = rho * (1.0 - p)
    common_closed = rho * p
    if common_open:
        mass[frozenset()] = mass.get(frozenset(), 0.0) + common_open
    if common_closed:
        all_closed = frozenset(closure_cells)
        mass[all_closed] = mass.get(all_closed, 0.0) + common_closed

    independent_weight = 1.0 - rho
    if independent_weight:
        for flags in product((False, True), repeat=len(closure_cells)):
            probability = independent_weight
            closed: set[GridCell] = set()
            for cell, flag in zip(closure_cells, flags, strict=True):
                probability *= p if flag else 1.0 - p
                if flag:
                    closed.add(cell)
            if probability:
                key = frozenset(closed)
                mass[key] = mass.get(key, 0.0) + probability

    return TopologyScenarioBelief(
        tuple(
            ClosureScenario(cells, probability)
            for cells, probability in sorted(
                mass.items(),
                key=lambda item: (len(item[0]), sorted(item[0])),
            )
        )
    )
