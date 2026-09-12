"""Online estimators for belief-conditioned safe-return reliability.

These estimators use only the robot's current topology belief. They are distinct
from the exact enumeration oracle in ``dynnav.recoverability_belief`` and are
intended to provide computational baselines for online planning.
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass

from dynnav.planners.grid_map import GridCell, GridMap
from dynnav.recoverability_belief import TopologyBelief


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
    belief: TopologyBelief,
    *,
    forbidden_uncertain_cells: set[GridCell] | None = None,
) -> ReturnReliabilityEstimate:
    forbidden = set(forbidden_uncertain_cells or ())
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
            p_blocked = float(belief.blocked_probability.get(neighbor, 0.0))
            if p_blocked >= 1.0:
                continue
            survival = 1.0 - p_blocked
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
    belief: TopologyBelief,
) -> set[GridCell] | ReturnReliabilityEstimate:
    grid.validate()
    belief.validate(grid)
    if not grid.in_bounds(start) or not grid.passable(start):
        return ReturnReliabilityEstimate(0.0, ())
    if start in belief.blocked_probability:
        raise ValueError("start cell is physically occupied by the robot and must be conditioned free")
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
    belief: TopologyBelief,
) -> ReturnReliabilityEstimate:
    """Estimate safe-return probability using the single most reliable path.

    Independent cell survival probabilities are converted to additive
    ``-log(1-p_blocked)`` costs. Dijkstra search therefore maximizes the product
    of survival probabilities along one return path. This estimate is a lower
    bound on full network reliability because it deliberately ignores the value
    of redundant alternative paths.
    """

    validated = _validated_problem(grid, start, safe_cells, belief)
    if isinstance(validated, ReturnReliabilityEstimate):
        return validated
    return _most_reliable_path(grid, start, validated, belief)


def two_uncertain_disjoint_return_paths(
    grid: GridMap,
    start: GridCell,
    safe_cells: set[GridCell],
    belief: TopologyBelief,
) -> RedundantReturnReliabilityEstimate:
    """Lower-bound return reliability using up to two uncertainty-disjoint paths.

    The first path is the most reliable return route. A second route is searched
    while forbidding every unresolved cell used by the first route. Because the
    two path-success events then depend on disjoint independent Bernoulli cells,
    their union probability is ``1 - (1-r1)(1-r2)``. Deterministic cells may be
    shared safely. Other possible routes are ignored, so the result remains a
    conservative lower bound on full network reliability.
    """

    validated = _validated_problem(grid, start, safe_cells, belief)
    if isinstance(validated, ReturnReliabilityEstimate):
        paths = (validated.path,) if validated.path else ()
        return RedundantReturnReliabilityEstimate(validated.probability, paths)

    first = _most_reliable_path(grid, start, validated, belief)
    if not first.path or first.probability <= 0.0:
        return RedundantReturnReliabilityEstimate(0.0, ())
    if first.probability >= 1.0:
        return RedundantReturnReliabilityEstimate(1.0, (first.path,))

    first_uncertain = {
        cell for cell in first.path if cell in belief.blocked_probability
    }
    second = _most_reliable_path(
        grid,
        start,
        validated,
        belief,
        forbidden_uncertain_cells=first_uncertain,
    )
    if not second.path or second.probability <= 0.0:
        return RedundantReturnReliabilityEstimate(first.probability, (first.path,))

    combined = 1.0 - (1.0 - first.probability) * (1.0 - second.probability)
    return RedundantReturnReliabilityEstimate(
        min(1.0, max(0.0, combined)),
        (first.path, second.path),
    )
