from dynnav.planners.dynamic_self_aware_astar import (
    DynamicSelfAwareAStarConfig,
    apply_grid_updates,
    dynamic_self_aware_astar,
)
from dynnav.planners.grid_map import GridCell, GridMap
from dynnav.planners.self_aware_astar import SelfAwareAStarWeights


def test_apply_grid_updates_adds_obstacle_and_risk():
    grid = GridMap.from_obstacles(width=4, height=3)
    updated = apply_grid_updates(grid, obstacles_to_add={(1, 1)}, risk_updates={(2, 1): 0.8})

    assert (1, 1) in updated.obstacles
    assert updated.cell_risk((2, 1)) == 0.8
    assert grid.passable((1, 1))


def test_dynamic_self_aware_astar_replans_when_path_blocked():
    grid = GridMap.from_obstacles(width=6, height=3)

    def update(step: int, current_grid: GridMap, current: GridCell) -> GridMap:
        if step == 1:
            return apply_grid_updates(current_grid, obstacles_to_add={(2, 1), (3, 1)})
        return current_grid

    result = dynamic_self_aware_astar(
        initial_grid=grid,
        start=(0, 1),
        goal=(5, 1),
        map_update_fn=update,
        config=DynamicSelfAwareAStarConfig(
            weights=SelfAwareAStarWeights(risk_cost=5.0),
            max_steps=32,
        ),
    )

    assert result.success
    assert result.replans >= 1
    assert result.blocked_replans >= 1
    assert (2, 1) not in result.path
    assert result.path[0] == (0, 1)
    assert result.path[-1] == (5, 1)


def test_dynamic_self_aware_astar_reports_initial_failure():
    grid = GridMap.from_obstacles(width=3, height=3, obstacles={(1, 0), (1, 1), (1, 2)})

    result = dynamic_self_aware_astar(
        initial_grid=grid,
        start=(0, 1),
        goal=(2, 1),
        map_update_fn=lambda step, current_grid, current: current_grid,
    )

    assert not result.success
    assert result.failure_reason == "initial_plan_failed"
