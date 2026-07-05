"""Baseline A* planner for grid maps."""

from __future__ import annotations

import heapq
import time
from dataclasses import dataclass

from dynnav.planners.grid_map import GridCell, GridMap, manhattan


@dataclass(frozen=True)
class AStarResult:
    path: list[GridCell]
    success: bool
    cost: float
    nodes_expanded: int
    planning_time_ms: float


def _reconstruct_path(came_from: dict[GridCell, GridCell], current: GridCell) -> list[GridCell]:
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def astar(grid: GridMap, start: GridCell, goal: GridCell) -> AStarResult:
    """Run classical A* with unit step cost and Manhattan heuristic."""
    grid.validate()
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

        for neighbor in grid.neighbors4(current):
            new_cost = cost_so_far[current] + 1.0
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                counter += 1
                priority = new_cost + manhattan(neighbor, goal)
                heapq.heappush(frontier, (priority, counter, neighbor))
                came_from[neighbor] = current

    return AStarResult(
        path=[],
        success=False,
        cost=float("inf"),
        nodes_expanded=nodes_expanded,
        planning_time_ms=(time.perf_counter() - t0) * 1000.0,
    )
