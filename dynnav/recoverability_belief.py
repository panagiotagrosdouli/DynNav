"""Exact safe-return oracle under uncertain future topology closures.

This module is intentionally evaluation-only. It enumerates all realizations of
a small set of future route-closure events and computes the exact probability
that a robot state will remain connected to at least one designated safe cell
if recovery becomes necessary after those events. The oracle is useful for
ground-truth labels and validation of cheaper online estimators.

The probabilities here are *not* current occupancy probabilities. Cells in the
hazard model are currently known free and may become blocked later due to a
dynamic route-invalidation event. This distinction prevents a robot from
pretending that a cell it already traversed is still statically unobserved.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass
from itertools import product

from dynnav.planners.grid_map import GridCell, GridMap


@dataclass(frozen=True)
class TopologyHazardBelief:
    """Independent Bernoulli belief over future cell-closure events."""

    closure_probability: Mapping[GridCell, float]

    def validate(self, grid: GridMap) -> None:
        for cell, probability in self.closure_probability.items():
            if not grid.in_bounds(cell):
                raise ValueError(f"hazard cell outside grid: {cell}")
            if cell in grid.obstacles:
                raise ValueError(f"hazard cell is already a known obstacle: {cell}")
            if not 0.0 <= probability <= 1.0:
                raise ValueError(
                    f"closure probability must be in [0, 1], got {probability!r} for {cell}"
                )


def _can_reach_safe_region(grid: GridMap, start: GridCell, safe_cells: set[GridCell]) -> bool:
    if not grid.in_bounds(start) or not grid.passable(start):
        return False
    valid_safe = {cell for cell in safe_cells if grid.in_bounds(cell) and grid.passable(cell)}
    if not valid_safe:
        return False
    queue: deque[GridCell] = deque([start])
    reached = {start}
    while queue:
        current = queue.popleft()
        if current in valid_safe:
            return True
        for neighbor in grid.neighbors4(current):
            if neighbor not in reached:
                reached.add(neighbor)
                queue.append(neighbor)
    return False


def exact_safe_return_probability(
    grid: GridMap,
    start: GridCell,
    safe_cells: set[GridCell],
    hazard: TopologyHazardBelief,
    *,
    max_hazard_cells: int = 16,
) -> float:
    """Return exact post-closure safe-return probability by enumeration.

    Hazard cells are currently traversable but may independently close before a
    future recovery is attempted. If the current robot cell is itself a hazard
    location, that one cell is conditioned usable at the decision instant while
    all other future closure events remain unresolved.
    """

    grid.validate()
    hazard.validate(grid)
    if max_hazard_cells < 0:
        raise ValueError("max_hazard_cells must be non-negative")

    hazard_cells = sorted(cell for cell in hazard.closure_probability if cell != start)
    if len(hazard_cells) > max_hazard_cells:
        raise ValueError(
            f"exact enumeration limited to {max_hazard_cells} hazard cells; "
            f"got {len(hazard_cells)}"
        )

    if not hazard_cells:
        return float(_can_reach_safe_region(grid, start, safe_cells))

    probability_of_return = 0.0
    for closed_flags in product((False, True), repeat=len(hazard_cells)):
        realization_probability = 1.0
        realized_obstacles = set(grid.obstacles)
        for cell, closed in zip(hazard_cells, closed_flags, strict=True):
            p_closed = float(hazard.closure_probability[cell])
            realization_probability *= p_closed if closed else 1.0 - p_closed
            if closed:
                realized_obstacles.add(cell)

        if realization_probability == 0.0:
            continue
        realized_grid = GridMap.from_obstacles(
            width=grid.width,
            height=grid.height,
            obstacles=realized_obstacles,
            risk=grid.risk,
            uncertainty=grid.uncertainty,
        )
        if _can_reach_safe_region(realized_grid, start, safe_cells):
            probability_of_return += realization_probability

    return min(1.0, max(0.0, probability_of_return))


def exact_recoverability_degradation(
    grid: GridMap,
    current: GridCell,
    candidate: GridCell,
    safe_cells: set[GridCell],
    hazard: TopologyHazardBelief,
    *,
    max_hazard_cells: int = 16,
) -> float:
    """Return loss in post-closure safe-return probability after commitment.

    Positive values mean the candidate state preserves less safe-return
    probability than the current state under the same future closure model.
    This quantity is diagnostic: with a fixed current state it induces the same
    one-step ordering as maximizing candidate safe-return probability, so it is
    not treated as a novel objective by itself.
    """

    current_probability = exact_safe_return_probability(
        grid,
        current,
        safe_cells,
        hazard,
        max_hazard_cells=max_hazard_cells,
    )
    candidate_probability = exact_safe_return_probability(
        grid,
        candidate,
        safe_cells,
        hazard,
        max_hazard_cells=max_hazard_cells,
    )
    return current_probability - candidate_probability
