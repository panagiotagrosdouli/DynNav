from ros2_ws.src.dynnav_nav2.dynnav_nav2.path_conversion import (
    grid_cell_to_world,
    grid_path_to_world,
)


def test_grid_cell_to_world_uses_cell_center():
    assert grid_cell_to_world((0, 0), 1.0) == (0.5, 0.5)
    assert grid_cell_to_world((2, 3), 0.5) == (1.25, 1.75)


def test_grid_cell_to_world_rejects_nonpositive_resolution():
    try:
        grid_cell_to_world((0, 0), 0.0)
    except ValueError as exc:
        assert "resolution" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_grid_path_to_world_converts_all_cells():
    assert grid_path_to_world([(0, 0), (1, 0)], 1.0) == [(0.5, 0.5), (1.5, 0.5)]
