from ros2_ws.src.dynnav_nav2.dynnav_nav2.occupancy_grid_conversion import (
    OccupancyGridSpec,
    occupancy_grid_spec_to_grid_map,
    occupancy_index_to_cell,
    occupancy_value_to_risk,
)


def test_occupancy_index_to_cell_uses_row_major_layout():
    assert occupancy_index_to_cell(0, width=4) == (0, 0)
    assert occupancy_index_to_cell(3, width=4) == (3, 0)
    assert occupancy_index_to_cell(4, width=4) == (0, 1)


def test_occupancy_value_to_risk_maps_unknown_to_medium_risk():
    assert occupancy_value_to_risk(-1) == 0.5
    assert occupancy_value_to_risk(0) == 0.0
    assert occupancy_value_to_risk(100) == 1.0


def test_occupancy_grid_spec_to_grid_map_marks_obstacles_and_unknown_uncertainty():
    spec = OccupancyGridSpec(
        width=3,
        height=2,
        data=(0, 70, -1, 10, 100, 0),
        occupied_threshold=65,
        unknown_is_obstacle=False,
    )

    grid = occupancy_grid_spec_to_grid_map(spec)

    assert grid.width == 3
    assert grid.height == 2
    assert (1, 0) in grid.obstacles
    assert (1, 1) in grid.obstacles
    assert (2, 0) not in grid.obstacles
    assert grid.cell_uncertainty((2, 0)) == 1.0
    assert grid.cell_risk((2, 0)) == 0.5


def test_unknown_cells_can_be_treated_as_obstacles():
    spec = OccupancyGridSpec(width=2, height=1, data=(-1, 0), unknown_is_obstacle=True)
    grid = occupancy_grid_spec_to_grid_map(spec)

    assert (0, 0) in grid.obstacles
    assert (1, 0) not in grid.obstacles


def test_invalid_data_length_is_rejected():
    spec = OccupancyGridSpec(width=2, height=2, data=(0, 1, 2))
    try:
        spec.validate()
    except ValueError as exc:
        assert "data length" in str(exc)
    else:
        raise AssertionError("expected ValueError")
