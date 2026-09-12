"""Risk- and recoverability-aware A* with explicit ablation modes."""

from __future__ import annotations

import heapq
import time
from dataclasses import dataclass
from enum import Enum

from dynnav.planners.astar import AStarResult, _reconstruct_path
from dynnav.planners.grid_map import GridCell, GridMap, manhattan
from dynnav.recoverability import RecoverabilityState, RecoverabilityWeights, recoverability_map


class PlannerMode(str, Enum):
    SHORTEST = "shortest"
    RISK_AWARE = "risk_aware"
    RECOVERABILITY_AWARE = "recoverability_aware"
    PROPOSED = "proposed"


@dataclass(frozen=True)
class RecoverabilityAStarConfig:
    step_cost: float = 1.0
    risk_weight: float = 4.0
    irreversibility_weight: float = 4.0
    heuristic_weight: float = 1.0
    recoverability_weights: RecoverabilityWeights = RecoverabilityWeights()

    def validate(self) -> None:
        for name in ("step_cost", "risk_weight", "irreversibility_weight", "heuristic_weight"):
            if getattr(self, name) < 0.0:
                raise ValueError(f"{name} must be non-negative")
        if self.step_cost <= 0.0:
            raise ValueError("step_cost must be positive")
        self.recoverability_weights.validate()


@dataclass(frozen=True)
class RecoverabilityAStarResult(AStarResult):
    mode: PlannerMode
    geometric_length: int
    cumulative_risk: float
    cumulative_irreversibility: float
    minimum_escape_options: int


def _mode_weights(mode: PlannerMode, config: RecoverabilityAStarConfig) -> tuple[float, float]:
    if mode is PlannerMode.SHORTEST:
        return 0.0, 0.0
    if mode is PlannerMode.RISK_AWARE:
        return config.risk_weight, 0.0
    if mode is PlannerMode.RECOVERABILITY_AWARE:
        return 0.0, config.irreversibility_weight
    return config.risk_weight, config.irreversibility_weight


def _result(
    path: list[GridCell],
    success: bool,
    cost: float,
    nodes_expanded: int,
    planning_time_ms: float,
    mode: PlannerMode,
    grid: GridMap,
    states: dict[GridCell, RecoverabilityState],
) -> RecoverabilityAStarResult:
    if not success:
        return RecoverabilityAStarResult(
            path=[], success=False, cost=float("inf"), nodes_expanded=nodes_expanded,
            planning_time_ms=planning_time_ms, mode=mode, geometric_length=0,
            cumulative_risk=float("inf"), cumulative_irreversibility=float("inf"),
            minimum_escape_options=0,
        )

    return RecoverabilityAStarResult(
        path=path,
        success=True,
        cost=cost,
        nodes_expanded=nodes_expanded,
        planning_time_ms=planning_time_ms,
        mode=mode,
        geometric_length=max(0, len(path) - 1),
        cumulative_risk=sum(grid.cell_risk(cell) for cell in path[1:]),
        cumulative_irreversibility=sum(states[cell].irreversibility for cell in path[1:]),
        minimum_escape_options=min((states[cell].escape_options for cell in path), default=0),
    )


def recoverability_astar(
    grid: GridMap,
    start: GridCell,
    goal: GridCell,
    *,
    safe_cells: set[GridCell] | None = None,
    mode: PlannerMode = PlannerMode.PROPOSED,
    config: RecoverabilityAStarConfig | None = None,
) -> RecoverabilityAStarResult:
    """Plan with one of the four canonical ablation objectives.

    Transition costs are dimensionless after normalization: risk and
    irreversibility are both constrained to ``[0, 1]`` and multiplied by
    explicit weights. Setting either weight to zero exactly recovers the
    corresponding ablation.
    """

    grid.validate()
    config = config or RecoverabilityAStarConfig()
    config.validate()
    safe_cells = set(safe_cells or {start})

    if not grid.in_bounds(start) or not grid.in_bounds(goal):
        raise ValueError("start and goal must be inside the grid")
    if not grid.passable(start) or not grid.passable(goal):
        return _result([], False, float("inf"), 0, 0.0, mode, grid, {})

    # The reported planner latency must include construction of the
    # recoverability field; otherwise J2/J3 overhead is systematically
    # under-reported relative to the actual work performed by the planner.
    t0 = time.perf_counter()
    states = recoverability_map(grid, safe_cells, config.recoverability_weights)
    risk_weight, irreversibility_weight = _mode_weights(mode, config)

    frontier: list[tuple[float, int, GridCell]] = []
    heapq.heappush(frontier, (0.0, 0, start))
    came_from: dict[GridCell, GridCell] = {}
    cost_so_far: dict[GridCell, float] = {start: 0.0}
    counter = 0
    nodes_expanded = 0

    while frontier:
        _, _, current = heapq.heappop(frontier)
        nodes_expanded += 1
        if current == goal:
            path = _reconstruct_path(came_from, current)
            return _result(
                path, True, cost_so_far[current], nodes_expanded,
                (time.perf_counter() - t0) * 1000.0, mode, grid, states,
            )

        for neighbor in grid.neighbors4(current):
            transition = (
                config.step_cost
                + risk_weight * grid.cell_risk(neighbor)
                + irreversibility_weight * states[neighbor].irreversibility
            )
            new_cost = cost_so_far[current] + transition
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                came_from[neighbor] = current
                counter += 1
                priority = new_cost + config.heuristic_weight * config.step_cost * manhattan(neighbor, goal)
                heapq.heappush(frontier, (priority, counter, neighbor))

    return _result(
        [], False, float("inf"), nodes_expanded,
        (time.perf_counter() - t0) * 1000.0, mode, grid, states,
    )
