"""Dynamic replanning wrapper for SelfAwareAStar.

The runner executes one step of the current plan, observes map changes, and
replans when the remaining path becomes blocked or too risky. It is a small
algorithmic prototype intended for synthetic benchmarks before simulator or ROS
integration.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Callable, Iterable

from dynnav.core.information_gain import expected_information_gain
from dynnav.planners.grid_map import GridCell, GridMap
from dynnav.planners.self_aware_astar import SelfAwareAStarWeights, self_aware_astar

MapUpdateFn = Callable[[int, GridMap, GridCell], GridMap]


@dataclass(frozen=True)
class DynamicReplanningResult:
    path: list[GridCell]
    success: bool
    replans: int
    blocked_replans: int
    risk_replans: int
    steps: int
    total_nodes_expanded: int
    total_planning_time_ms: float
    mean_risk: float
    max_risk: float
    information_gain: float
    recoverability: float
    failure_reason: str = ""


@dataclass(frozen=True)
class DynamicSelfAwareAStarConfig:
    weights: SelfAwareAStarWeights = field(default_factory=SelfAwareAStarWeights)
    max_steps: int = 256
    risk_replan_threshold: float = 0.75
    sensor_radius: int = 1


def apply_grid_updates(
    grid: GridMap,
    obstacles_to_add: Iterable[GridCell] = (),
    risk_updates: dict[GridCell, float] | None = None,
    uncertainty_updates: dict[GridCell, float] | None = None,
) -> GridMap:
    """Return a new GridMap with dynamic obstacle/risk/uncertainty updates."""
    obstacles = set(grid.obstacles)
    obstacles.update(cell for cell in obstacles_to_add if grid.in_bounds(cell))
    risk = dict(grid.risk)
    risk.update({cell: value for cell, value in (risk_updates or {}).items() if grid.in_bounds(cell)})
    uncertainty = dict(grid.uncertainty)
    uncertainty.update({cell: value for cell, value in (uncertainty_updates or {}).items() if grid.in_bounds(cell)})
    return GridMap.from_obstacles(
        width=grid.width,
        height=grid.height,
        obstacles=obstacles,
        risk=risk,
        uncertainty=uncertainty,
    )


def _remaining_path_blocked(grid: GridMap, remaining_path: list[GridCell]) -> bool:
    return any((not grid.in_bounds(cell)) or (not grid.passable(cell)) for cell in remaining_path)


def _remaining_path_risky(grid: GridMap, remaining_path: list[GridCell], threshold: float) -> bool:
    return any(grid.cell_risk(cell) >= threshold for cell in remaining_path)


def _metrics(grid: GridMap, path: list[GridCell], sensor_radius: int) -> tuple[float, float, float, float]:
    if not path:
        return 0.0, 0.0, 0.0, 0.0
    risks = [grid.cell_risk(cell) for cell in path]
    mean_risk = sum(risks) / len(risks)
    max_risk = max(risks)
    information_gain = expected_information_gain(path, grid.occupancy_belief(), sensor_radius=sensor_radius)
    recoverability = 1.0 - max_risk
    return mean_risk, max_risk, information_gain, recoverability


def dynamic_self_aware_astar(
    initial_grid: GridMap,
    start: GridCell,
    goal: GridCell,
    map_update_fn: MapUpdateFn,
    config: DynamicSelfAwareAStarConfig | None = None,
) -> DynamicReplanningResult:
    """Execute dynamic self-aware replanning until goal or failure.

    Args:
        initial_grid: Initial known grid.
        start: Start cell.
        goal: Goal cell.
        map_update_fn: Function called after each step to update the grid.
        config: Dynamic replanning configuration.
    """
    config = config or DynamicSelfAwareAStarConfig()
    current = start
    grid = initial_grid
    executed_path = [start]
    replans = 0
    blocked_replans = 0
    risk_replans = 0
    total_nodes_expanded = 0
    total_planning_time_ms = 0.0

    plan = self_aware_astar(grid, current, goal, config.weights)
    total_nodes_expanded += plan.nodes_expanded
    total_planning_time_ms += plan.planning_time_ms
    if not plan.success:
        mean_risk, max_risk, information_gain, recoverability = _metrics(grid, executed_path, config.sensor_radius)
        return DynamicReplanningResult(
            path=executed_path,
            success=False,
            replans=0,
            blocked_replans=0,
            risk_replans=0,
            steps=0,
            total_nodes_expanded=total_nodes_expanded,
            total_planning_time_ms=total_planning_time_ms,
            mean_risk=mean_risk,
            max_risk=max_risk,
            information_gain=information_gain,
            recoverability=recoverability,
            failure_reason="initial_plan_failed",
        )

    remaining = plan.path[1:]

    for step in range(config.max_steps):
        if current == goal:
            mean_risk, max_risk, information_gain, recoverability = _metrics(grid, executed_path, config.sensor_radius)
            return DynamicReplanningResult(
                path=executed_path,
                success=True,
                replans=replans,
                blocked_replans=blocked_replans,
                risk_replans=risk_replans,
                steps=step,
                total_nodes_expanded=total_nodes_expanded,
                total_planning_time_ms=total_planning_time_ms,
                mean_risk=mean_risk,
                max_risk=max_risk,
                information_gain=information_gain,
                recoverability=recoverability,
            )

        grid = map_update_fn(step, grid, current)
        blocked = _remaining_path_blocked(grid, remaining)
        risky = _remaining_path_risky(grid, remaining, config.risk_replan_threshold)
        if blocked or risky or not remaining:
            replans += 1
            blocked_replans += int(blocked)
            risk_replans += int(risky)
            plan = self_aware_astar(grid, current, goal, config.weights)
            total_nodes_expanded += plan.nodes_expanded
            total_planning_time_ms += plan.planning_time_ms
            if not plan.success:
                mean_risk, max_risk, information_gain, recoverability = _metrics(grid, executed_path, config.sensor_radius)
                return DynamicReplanningResult(
                    path=executed_path,
                    success=False,
                    replans=replans,
                    blocked_replans=blocked_replans,
                    risk_replans=risk_replans,
                    steps=step,
                    total_nodes_expanded=total_nodes_expanded,
                    total_planning_time_ms=total_planning_time_ms,
                    mean_risk=mean_risk,
                    max_risk=max_risk,
                    information_gain=information_gain,
                    recoverability=recoverability,
                    failure_reason="replan_failed",
                )
            remaining = plan.path[1:]

        next_cell = remaining.pop(0)
        if not grid.passable(next_cell):
            mean_risk, max_risk, information_gain, recoverability = _metrics(grid, executed_path, config.sensor_radius)
            return DynamicReplanningResult(
                path=executed_path,
                success=False,
                replans=replans,
                blocked_replans=blocked_replans,
                risk_replans=risk_replans,
                steps=step,
                total_nodes_expanded=total_nodes_expanded,
                total_planning_time_ms=total_planning_time_ms,
                mean_risk=mean_risk,
                max_risk=max_risk,
                information_gain=information_gain,
                recoverability=recoverability,
                failure_reason="executed_into_blocked_cell",
            )
        current = next_cell
        executed_path.append(current)

    mean_risk, max_risk, information_gain, recoverability = _metrics(grid, executed_path, config.sensor_radius)
    return DynamicReplanningResult(
        path=executed_path,
        success=current == goal,
        replans=replans,
        blocked_replans=blocked_replans,
        risk_replans=risk_replans,
        steps=config.max_steps,
        total_nodes_expanded=total_nodes_expanded,
        total_planning_time_ms=total_planning_time_ms,
        mean_risk=mean_risk,
        max_risk=max_risk,
        information_gain=information_gain,
        recoverability=recoverability,
        failure_reason="max_steps_exceeded" if current != goal else "",
    )
