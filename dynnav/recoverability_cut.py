"""Scalable critical-cut approximation for future safe-return connectivity."""
from __future__ import annotations

from dataclasses import dataclass

from dynnav.planners.grid_map import GridCell, GridMap
from dynnav.recoverability_belief import TopologyHazardBelief


@dataclass(frozen=True)
class CriticalCutEstimate:
    probability_upper_bound: float
    critical_hazard_cells: tuple[GridCell, ...]
    inspected_hazard_cells: int


def _safe_reachable_without(
    grid: GridMap,
    start: GridCell,
    safe_cells: set[GridCell],
    removed: GridCell | None,
) -> bool:
    if start == removed:
        return False
    if start in safe_cells:
        return True
    frontier = [start]
    seen = {start}
    while frontier:
        current = frontier.pop()
        for neighbor in grid.neighbors4(current):
            if neighbor == removed or neighbor in seen:
                continue
            if neighbor in safe_cells:
                return True
            seen.add(neighbor)
            frontier.append(neighbor)
    return False


def critical_return_cut_upper_bound(
    grid: GridMap,
    cell: GridCell,
    safe_cells: set[GridCell],
    hazard: TopologyHazardBelief,
) -> CriticalCutEstimate:
    """Upper-bound return reliability using individually critical hazard cells.

    A hazard cell is individually critical when removing that one cell alone
    disconnects ``cell`` from every designated safe cell. Under independent
    future closures, all individually critical cells must remain open; their
    joint survival probability is therefore a necessary condition for return.

    Non-critical hazards can still disconnect the robot jointly (multi-cell
    cutsets), so this estimate can be optimistic. It is intentionally exposed as
    an upper bound and is evaluated against the exact small-world oracle.
    """
    grid.validate()
    hazard.validate(grid)
    if not grid.in_bounds(cell) or not grid.passable(cell):
        raise ValueError("cell must be a traversable grid cell")
    if not safe_cells:
        raise ValueError("safe_cells cannot be empty")
    if not _safe_reachable_without(grid, cell, safe_cells, None):
        return CriticalCutEstimate(0.0, (), len(hazard.closure_probability))

    critical: list[GridCell] = []
    probability = 1.0
    for hazard_cell, closure_probability in sorted(hazard.closure_probability.items()):
        if hazard_cell == cell:
            # Current occupancy conditions this cell usable at the evaluation instant.
            continue
        if not _safe_reachable_without(grid, cell, safe_cells, hazard_cell):
            critical.append(hazard_cell)
            probability *= 1.0 - closure_probability

    return CriticalCutEstimate(
        probability_upper_bound=probability,
        critical_hazard_cells=tuple(critical),
        inspected_hazard_cells=len(hazard.closure_probability),
    )
