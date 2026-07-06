from ros2_ws.src.dynnav_nav2.dynnav_nav2.dynnav_planner_bridge import (
    PlannerBridgeConfig,
    format_path,
    parse_cells,
    plan_grid_path,
)


def test_parse_cells_parses_comma_separated_grid_cells():
    assert parse_cells("1:2,3:4") == ((1, 2), (3, 4))


def test_format_path_uses_arrow_notation():
    assert format_path([(0, 0), (1, 0), (1, 1)]) == "(0,0) -> (1,0) -> (1,1)"


def test_plan_grid_path_returns_path_for_simple_config():
    config = PlannerBridgeConfig(
        width=4,
        height=4,
        start=(0, 0),
        goal=(3, 0),
        obstacles=(),
    )

    path = plan_grid_path(config)

    assert path[0] == (0, 0)
    assert path[-1] == (3, 0)
