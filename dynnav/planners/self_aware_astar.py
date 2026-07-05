"""Self-aware A* planner.

This planner keeps the baseline A* structure but changes the transition cost so
that path search is influenced by risk, uncertainty, recoverability, and a small
information-gain reward. It is intended as the first research prototype, not a
claim of optimality.
"""

from __future__ import annotations

import heapq
import time
from dataclasses import dataclass

from dynnav.core.information_gain import expected_information_gain
from dynnav.planners.astar import AStarResult, _reconstruct_path
from dynnav.planners.grid_map import GridCell, GridMap, manhattan


@dataclass(frozen=True)
class SelfAwareAStarWeights:
    step_cost: float = 1.0
    risk_cost: float = 6.0
    uncertainty_cost: float = 2.0
    low_recoverability_cost: float = 3.0
    information_gain_reward: float = 1.5
    heuristic_cost: float = 1.0

    def validate(self) -> None:
        for name, value in self.__dict__.items():
            if value < 0.0:
                raise ValueError(f"{name} must be non-negative, got {value!r}")


def _transition_cost(
    grid: GridMap,
    partial_path: list[GridCell],
    neighbor: GridCell,
    weights: SelfAwareAStarWeights,
) -> float:
    risk = grid.cell_risk(neighbor)
    uncertainty = grid.cell_uncertainty(neighbor)
    recoverability = 1.0 - risk
    candidate_path = [*partial_path, neighbor]
    information_gain = expected_information_gain(candidate_path, grid.occupancy_belief(), sensor_radius=1)

    return max(
        0.01,
        weights.step_cost
        + weights.risk_cost * risk
        + weights.uncertainty_cost * uncertainty
        + weights.low_recoverability_cost * (1.0 - recoverability)
        - weights.information_gain_reward * information_gain,
    )


def self_aware_astar(
    grid: GridMap,
    start: GridCell,
    goal: GridCell,
    weights: SelfAwareAStarWeights | None = None,
) -> AStarResult:
    """Run self-aware A* on a grid map.

    Lower-risk, lower-uncertainty, and higher-information paths become more
    attractive than shortest paths when the trade-off weights justify it.
    """
    grid.validate()
    weights = weights or SelfAwareAStarWeights()
    weights.validate()

    if not grid.in_bounds(start) or not grid.in_bounds(goal):
        raise ValueError("start and goal must be inside the grid")
    if not grid.passable(start) or not grid.passable(goal):
        return AStarResult(path=[], success=False, cost=float("inf"), nodes_expanded=0, planning_time_ms=0.0)

    t0 = time.perf_counter()
    frontier: list[tuple[float, int, GridCell]] = []
    counter = 0
    heapq.heappush(frontier, (0.0, counter, start))

    came_from: dict[GridCell, GridCell] = {}
    cost_so_far: dict[GridCell, float] = {start: 0.0}
    best_partial_path: dict[GridCell, list[GridCell]] = {start: [start]}
    nodes_expanded = 0

    while frontier:
        _, _, current = heapq.heappop(frontier)
        nodes_expanded += 1

        if current == goal:
            path = _reconstruct_path(came_from, current)
            return AStarResult(
                path=path,
                success=True,
                cost=cost_so_far[current],
                nodes_expanded=nodes_expanded,
                planning_time_ms=(time.perf_counter() - t0) * 1000.0,
            )

        partial_path = best_partial_path[current]
        for neighbor in grid.neighbors4(current):
            new_cost = cost_so_far[current] + _transition_cost(grid, partial_path, neighbor, weights)
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                came_from[neighbor] = current
                best_partial_path[neighbor] = [*partial_path, neighbor]
                counter += 1
                priority = new_cost + weights.heuristic_cost * manhattan(neighbor, goal)
                heapq.heappush(frontier, (priority, counter, neighbor))

    return AStarResult(
        path=[],
        success=False,
        cost=float("inf"),
        nodes_expanded=nodes_expanded,
        planning_time_ms=(time.perf_counter() - t0) * 1000.0,
    )
