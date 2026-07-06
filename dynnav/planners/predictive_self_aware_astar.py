"""Predictive SelfAwareAStar planner.

This planner extends SelfAwareAStar with a time-indexed predictive risk map.
The transition cost uses risk at the time the robot is expected to arrive at a
cell, not only the current risk estimate.
"""

from __future__ import annotations

import heapq
import time
from dataclasses import dataclass

from dynnav.core.information_gain import expected_information_gain
from dynnav.planners.astar import AStarResult, _reconstruct_path
from dynnav.planners.grid_map import GridCell, GridMap, manhattan
from dynnav.prediction.predictive_risk_map import PredictiveRiskMap


@dataclass(frozen=True)
class PredictiveSelfAwareAStarWeights:
    step_cost: float = 1.0
    current_risk_cost: float = 4.0
    predicted_risk_cost: float = 8.0
    uncertainty_cost: float = 1.0
    information_gain_reward: float = 0.8
    heuristic_cost: float = 1.0

    def validate(self) -> None:
        for name, value in self.__dict__.items():
            if value < 0.0:
                raise ValueError(f"{name} must be non-negative, got {value!r}")


def _predictive_transition_cost(
    grid: GridMap,
    predictive_risk: PredictiveRiskMap,
    partial_path: list[GridCell],
    neighbor: GridCell,
    arrival_time: int,
    weights: PredictiveSelfAwareAStarWeights,
) -> float:
    current_risk = grid.cell_risk(neighbor)
    future_risk = predictive_risk.risk_at(neighbor, arrival_time)
    uncertainty = grid.cell_uncertainty(neighbor)
    candidate_path = [*partial_path, neighbor]
    information_gain = expected_information_gain(candidate_path, grid.occupancy_belief(), sensor_radius=1)

    return max(
        0.01,
        weights.step_cost
        + weights.current_risk_cost * current_risk
        + weights.predicted_risk_cost * future_risk
        + weights.uncertainty_cost * uncertainty
        - weights.information_gain_reward * information_gain,
    )


def predictive_self_aware_astar(
    grid: GridMap,
    predictive_risk: PredictiveRiskMap,
    start: GridCell,
    goal: GridCell,
    weights: PredictiveSelfAwareAStarWeights | None = None,
) -> AStarResult:
    """Run predictive risk-aware A* on a grid map."""
    grid.validate()
    predictive_risk.validate()
    weights = weights or PredictiveSelfAwareAStarWeights()
    weights.validate()

    if grid.width != predictive_risk.width or grid.height != predictive_risk.height:
        raise ValueError("grid and predictive risk map dimensions must match")
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
    arrival_time: dict[GridCell, int] = {start: 0}
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
            next_time = arrival_time[current] + 1
            transition = _predictive_transition_cost(
                grid,
                predictive_risk,
                partial_path,
                neighbor,
                next_time,
                weights,
            )
            new_cost = cost_so_far[current] + transition
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                came_from[neighbor] = current
                arrival_time[neighbor] = next_time
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
