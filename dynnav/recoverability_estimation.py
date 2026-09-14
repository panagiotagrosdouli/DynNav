"""Online estimators for safe-return reliability under future topology hazards.

These estimators use only the robot's current belief over future route-closure
events. They are distinct from the exact enumeration oracle in
``dynnav.recoverability_belief`` and provide computational baselines for online
planning.
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass

from dynnav.planners.grid_map import GridCell, GridMap
from dynnav.recoverability_belief import TopologyHazardBelief


@dataclass(frozen=True)
class ReturnReliabilityEstimate:
    probability: float
    path: tuple[GridCell, ...]


@dataclass(frozen=True)
class RedundantReturnReliabilityEstimate:
    probability: float
    paths: tuple[tuple[GridCell, ...], ...]


def _reconstruct_path(
    parent: dict[GridCell, GridCell], start: GridCell, goal: GridCell
) -> tuple[GridCell, ...]:
    path = [goal]
    current = goal
    while current != start:
        current = parent[current]
        path.append(current)
    path.reverse()
    return tuple(path)


def _most_reliable_path(
    grid: GridMap,
    start: GridCell,
    valid_safe: set[GridCell],
    hazard: TopologyHazardBelief,
    *,
    forbidden_hazard_cells: set[GridCell] | None = None,
) -> ReturnReliabilityEstimate:
    forbidden = set(forbidden_hazard_cells or ())
    distances: dict[GridCell, float] = {start: 0.0}
    parents: dict[GridCell, GridCell] = {}
    frontier: list[tuple[float, GridCell]] = [(0.0, start)]

    while frontier:
        cost, current = heapq.heappop(frontier)
        if cost != distances.get(current):
            continue
        if current in valid_safe:
            probability = math.exp(-cost)
            return ReturnReliabilityEstimate(
                min(1.0, max(0.0, probability)),
                _reconstruct_path(parents, start, current),
            )

        for neighbor in grid.neighbors4(current):
            if neighbor in forbidden:
                continue
            # The starting cell is already known usable at this decision instant.
            # Any hazard assigned to it is therefore conditioned away for this
            # state-level estimate; all cells entered afterwards retain hazards.
            p_closed = 0.0 if neighbor == start else float(
                hazard.closure_probability.get(neighbor, 0.0)
            )
            if p_closed >= 1.0:
                continue
            survival = 1.0 - p_closed
            transition_cost = -math.log(survival)
            new_cost = cost + transition_cost
            if new_cost < distances.get(neighbor, float("inf")):
                distances[neighbor] = new_cost
                parents[neighbor] = current
                heapq.heappush(frontier, (new_cost, neighbor))

    return ReturnReliabilityEstimate(0.0, ())


def _validated_problem(
    grid: GridMap,
    start: GridCell,
    safe_cells: set[GridCell],
    hazard: TopologyHazardBelief,
) -> set[GridCell] | ReturnReliabilityEstimate:
    grid.validate()
    hazard.validate(grid)
    if not grid.in_bounds(start) or not grid.passable(start):
        return ReturnReliabilityEstimate(0.0, ())
    valid_safe = {
        cell for cell in safe_cells if grid.in_bounds(cell) and grid.passable(cell)
    }
    if not valid_safe:
        return ReturnReliabilityEstimate(0.0, ())
    if start in valid_safe:
        return ReturnReliabilityEstimate(1.0, (start,))
    return valid_safe


def most_reliable_return_path(
    grid: GridMap,
    start: GridCell,
    safe_cells: set[GridCell],
    hazard: TopologyHazardBelief,
) -> ReturnReliabilityEstimate:
    """Estimate post-closure safe-return probability using one return path.

    Independent route-survival probabilities are converted to additive
    ``-log(1-p_close)`` costs. Dijkstra search therefore maximizes the product
    of survival probabilities along one return path. This estimate is a lower
    bound on full network reliability because it ignores redundant alternatives.
    """

    validated = _validated_problem(grid, start, safe_cells, hazard)
    if isinstance(validated, ReturnReliabilityEstimate):
        return validated
    return _most_reliable_path(grid, start, validated, hazard)


def two_hazard_disjoint_return_paths(
    grid: GridMap,
    start: GridCell,
    safe_cells: set[GridCell],
    hazard: TopologyHazardBelief,
) -> RedundantReturnReliabilityEstimate:
    """Lower-bound return reliability using up to two hazard-disjoint paths.

    The first path is the most reliable return route. A second route is searched
    while forbidding every future-closure hazard cell used by the first route,
    except the current robot cell which is conditioned usable. Since the two
    path-success events then depend on disjoint independent closure events, their
    union probability is ``1 - (1-r1)(1-r2)``. Deterministic cells may be shared.
    """

    validated = _validated_problem(grid, start, safe_cells, hazard)
    if isinstance(validated, ReturnReliabilityEstimate):
        paths = (validated.path,) if validated.path else ()
        return RedundantReturnReliabilityEstimate(validated.probability, paths)

    first = _most_reliable_path(grid, start, validated, hazard)
    if not first.path or first.probability <= 0.0:
        return RedundantReturnReliabilityEstimate(0.0, ())
    if first.probability >= 1.0:
        return RedundantReturnReliabilityEstimate(1.0, (first.path,))

    first_hazards = {
        cell
        for cell in first.path
        if cell != start and cell in hazard.closure_probability
    }
    second = _most_reliable_path(
        grid,
        start,
        validated,
        hazard,
        forbidden_hazard_cells=first_hazards,
    )
    if not second.path or second.probability <= 0.0:
        return RedundantReturnReliabilityEstimate(first.probability, (first.path,))

    combined = 1.0 - (1.0 - first.probability) * (1.0 - second.probability)
    return RedundantReturnReliabilityEstimate(
        min(1.0, max(0.0, combined)),
        (first.path, second.path),
    )
