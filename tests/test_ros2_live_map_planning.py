from dynnav.planners import GridMap
from ros2_ws.src.dynnav_nav2.dynnav_nav2.live_map_planning import (
    LiveMapPlanningConfig,
    plan_with_optional_live_grid,
    select_active_grid,
)


def test_select_active_grid_uses_live_grid_when_enabled():
    config = LiveMapPlanningConfig(start=(0, 0), goal=(2, 0), fallback_width=3, fallback_height=1)
    live = GridMap.from_obstacles(width=4, height=2)

    assert select_active_grid(config, live) is live


def test_select_active_grid_uses_fallback_when_live_disabled():
    config = LiveMapPlanningConfig(
        start=(0, 0),
        goal=(2, 0),
        fallback_width=3,
        fallback_height=1,
        use_live_map=False,
    )
    live = GridMap.from_obstacles(width=4, height=2)

    selected = select_active_grid(config, live)

    assert selected.width == 3
    assert selected.height == 1


def test_plan_with_optional_live_grid_returns_path():
    config = LiveMapPlanningConfig(start=(0, 0), goal=(2, 0), fallback_width=3, fallback_height=1)
    path = plan_with_optional_live_grid(config)

    assert path == [(0, 0), (1, 0), (2, 0)]
