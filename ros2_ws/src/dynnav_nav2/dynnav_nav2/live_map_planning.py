"""Planning helpers for live OccupancyGrid-derived maps."""

from __future__ import annotations

from dataclasses import dataclass

from dynnav.planners import GridMap, self_aware_astar
from dynnav_nav2.occupancy_grid_conversion import occupancy_grid_spec_to_grid_map, OccupancyGridSpec


@dataclass(frozen=True)
class LiveMapPlanningConfig:
    start: tuple[int, int]
    goal: tuple[int, int]
    fallback_width: int
    fallback_height: int
    fallback_obstacles: tuple[tuple[int, int], ...] = ()
    use_live_map: bool = True


def fallback_grid(config: LiveMapPlanningConfig) -> GridMap:
    return GridMap.from_obstacles(
        width=config.fallback_width,
        height=config.fallback_height,
        obstacles=config.fallback_obstacles,
    )


def grid_from_occupancy_spec(spec: OccupancyGridSpec) -> GridMap:
    return occupancy_grid_spec_to_grid_map(spec)


def select_active_grid(config: LiveMapPlanningConfig, live_grid: GridMap | None) -> GridMap:
    if config.use_live_map and live_grid is not None:
        return live_grid
    return fallback_grid(config)


def plan_with_optional_live_grid(config: LiveMapPlanningConfig, live_grid: GridMap | None = None) -> list[tuple[int, int]]:
    grid = select_active_grid(config, live_grid)
    result = self_aware_astar(grid, config.start, config.goal)
    return result.path if result.success else []
