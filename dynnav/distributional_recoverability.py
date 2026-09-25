"""Distributionally robust safe-return reliability under dependence ambiguity.

This module treats probabilities of future topology-closure scenarios as
unknown within a finite ambiguity set. It is a small exact reference
implementation for bounded hazard sets, not a scalable generic
distributionally robust planner.

Unlike dynnav.recoverability_belief, closure events need not be independent.
Marginal closure probabilities and optional pairwise joint probabilities
constrain a finite linear program over all joint closure realizations.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import isfinite

import numpy as np
from scipy.optimize import linprog

from dynnav.planners.grid_map import GridCell, GridMap
from dynnav.recoverability_belief import _can_reach_safe_region


@dataclass(frozen=True)
class ProbabilityInterval:
    lower: float
    upper: float

    def validate(self, *, name: str = "probability interval") -> None:
        if not isfinite(self.lower) or not isfinite(self.upper):
            raise ValueError(f"{name} bounds must be finite")
        if not 0.0 <= self.lower <= self.upper <= 1.0:
            raise ValueError(f"{name} must satisfy 0 <= lower <= upper <= 1")


@dataclass(frozen=True)
class PairwiseClosureConstraint:
    first: GridCell
    second: GridCell
    probability: ProbabilityInterval

    def validate(self) -> None:
        if self.first == self.second:
            raise ValueError("pairwise constraint requires two distinct cells")
        self.probability.validate(name="pairwise probability interval")


@dataclass(frozen=True)
class TopologyAmbiguitySet:
    """Finite ambiguity set over joint closure distributions."""

    marginals: dict[GridCell, ProbabilityInterval]
    pairwise: tuple[PairwiseClosureConstraint, ...] = ()

    def validate(self, grid: GridMap, *, max_hazard_cells: int = 12) -> None:
        grid.validate()
        if max_hazard_cells < 0:
            raise ValueError("max_hazard_cells must be non-negative")
        if len(self.marginals) > max_hazard_cells:
            raise ValueError(
                f"distributionally robust enumeration limited to {max_hazard_cells} "
                f"hazard cells; got {len(self.marginals)}"
            )
        for cell, interval in self.marginals.items():
            if not grid.in_bounds(cell):
                raise ValueError(f"hazard cell outside grid: {cell}")
            if not grid.passable(cell):
                raise ValueError(f"hazard cell is already blocked: {cell}")
            interval.validate(name=f"marginal interval for {cell}")
        seen_pairs: set[frozenset[GridCell]] = set()
        for constraint in self.pairwise:
            constraint.validate()
            if (
                constraint.first not in self.marginals
                or constraint.second not in self.marginals
            ):
                raise ValueError("pairwise cells must also appear in marginals")
            key = frozenset((constraint.first, constraint.second))
            if key in seen_pairs:
                raise ValueError("duplicate pairwise closure constraint")
            seen_pairs.add(key)


@dataclass(frozen=True)
class RobustReturnBounds:
    lower: float
    upper: float
    minimizing_distribution: tuple[float, ...]
    maximizing_distribution: tuple[float, ...]
    scenarios: tuple[frozenset[GridCell], ...]


def _enumerate_scenarios(cells: tuple[GridCell, ...]) -> tuple[frozenset[GridCell], ...]:
    return tuple(
        frozenset(cell for cell, closed in zip(cells, flags, strict=True) if closed)
        for flags in product((False, True), repeat=len(cells))
    )


def _connectivity_indicator(
    grid: GridMap,
    start: GridCell,
    safe_cells: set[GridCell],
    closed_cells: frozenset[GridCell],
) -> float:
    obstacles = set(grid.obstacles)
    obstacles.update(cell for cell in closed_cells if cell != start)
    realized = GridMap.from_obstacles(
        grid.width,
        grid.height,
        obstacles=obstacles,
        risk=grid.risk,
        uncertainty=grid.uncertainty,
    )
    return float(_can_reach_safe_region(realized, start, safe_cells))


def _constraint_rows(
    cells: tuple[GridCell, ...],
    scenarios: tuple[frozenset[GridCell], ...],
    ambiguity: TopologyAmbiguitySet,
) -> tuple[np.ndarray, np.ndarray]:
    rows: list[list[float]] = []
    bounds: list[float] = []

    def append_interval(coefficients: list[float], interval: ProbabilityInterval) -> None:
        rows.append(coefficients)
        bounds.append(interval.upper)
        rows.append([-value for value in coefficients])
        bounds.append(-interval.lower)

    for cell in cells:
        append_interval(
            [float(cell in scenario) for scenario in scenarios],
            ambiguity.marginals[cell],
        )
    for constraint in ambiguity.pairwise:
        append_interval(
            [
                float(constraint.first in scenario and constraint.second in scenario)
                for scenario in scenarios
            ],
            constraint.probability,
        )

    if not rows:
        return np.zeros((0, len(scenarios))), np.zeros(0)
    return np.asarray(rows, dtype=float), np.asarray(bounds, dtype=float)


def robust_safe_return_bounds(
    grid: GridMap,
    start: GridCell,
    safe_cells: set[GridCell],
    ambiguity: TopologyAmbiguitySet,
    *,
    max_hazard_cells: int = 12,
) -> RobustReturnBounds:
    """Return worst/best safe-return reliability over the ambiguity set."""

    ambiguity.validate(grid, max_hazard_cells=max_hazard_cells)
    cells = tuple(sorted(ambiguity.marginals))
    scenarios = _enumerate_scenarios(cells)
    if not scenarios:
        scenarios = (frozenset(),)

    indicators = np.asarray(
        [_connectivity_indicator(grid, start, safe_cells, scenario) for scenario in scenarios],
        dtype=float,
    )
    a_ub, b_ub = _constraint_rows(cells, scenarios, ambiguity)
    a_eq = np.ones((1, len(scenarios)), dtype=float)
    b_eq = np.ones(1, dtype=float)
    variable_bounds = [(0.0, 1.0)] * len(scenarios)

    minimum = linprog(
        indicators,
        A_ub=a_ub if len(a_ub) else None,
        b_ub=b_ub if len(b_ub) else None,
        A_eq=a_eq,
        b_eq=b_eq,
        bounds=variable_bounds,
        method="highs",
    )
    if not minimum.success:
        raise ValueError(f"infeasible topology ambiguity set: {minimum.message}")

    maximum = linprog(
        -indicators,
        A_ub=a_ub if len(a_ub) else None,
        b_ub=b_ub if len(b_ub) else None,
        A_eq=a_eq,
        b_eq=b_eq,
        bounds=variable_bounds,
        method="highs",
    )
    if not maximum.success:
        raise ValueError(f"infeasible topology ambiguity set: {maximum.message}")

    lower = float(np.dot(indicators, minimum.x))
    upper = float(np.dot(indicators, maximum.x))
    return RobustReturnBounds(
        lower=min(1.0, max(0.0, lower)),
        upper=min(1.0, max(0.0, upper)),
        minimizing_distribution=tuple(float(value) for value in minimum.x),
        maximizing_distribution=tuple(float(value) for value in maximum.x),
        scenarios=scenarios,
    )


def robust_safe_return_probability(
    grid: GridMap,
    start: GridCell,
    safe_cells: set[GridCell],
    ambiguity: TopologyAmbiguitySet,
    *,
    max_hazard_cells: int = 12,
) -> float:
    """Return the worst-case safe-return probability."""

    return robust_safe_return_bounds(
        grid,
        start,
        safe_cells,
        ambiguity,
        max_hazard_cells=max_hazard_cells,
    ).lower
