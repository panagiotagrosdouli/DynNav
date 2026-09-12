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

    The current robot cell is conditioned free: callers may not mark ``start``
    as unresolved occupancy.
    """

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
