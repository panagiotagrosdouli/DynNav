"""C01 ROS OccupancyGrid geometry and path sanity tests (no robot attached)."""
import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import pytest

FILE = Path(__file__).resolve().parents[1] / "experiments" / "ros2_grid_geometry.py"
spec = importlib.util.spec_from_file_location("c01_geometry", FILE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def test_ros_occupancy_grid_row_major_and_unknown_blocks():
    grid = mod.grid_from_occupancy([0, -1, 0, 100, 49, 50], 3, 2)
    assert grid.tolist() == [[0, 1, 0], [1, 0, 1]]


def test_obstacle_inflation_preserves_bounds_and_center():
    raw = [0] * 25
    raw[2*5 + 2] = 100
    grid = mod.grid_from_occupancy(raw, 5, 5, inflation_cells=1)
    assert int(grid.sum()) == 5
    assert grid[2, 2] == grid[2, 1] == grid[1, 2] == 1
    assert grid[1, 1] == 0


def test_origin_rotation_roundtrip_and_floor():
    geo = mod.GridGeometry(0.25, 4.0, -2.0, math.pi/2, "map")
    for cell in [(0, 0), (7, 4), (2, 9)]:
        x,y = geo.cell_to_world(*cell)
        assert geo.world_to_cell(x,y) == cell
    assert mod.GridGeometry(1, 0, 0, 0, "map").world_to_cell(-0.01, 0) == (-1, 0)


def test_bad_quaternion_and_nonplanar_rejected():
    with pytest.raises(ValueError):
        mod.quaternion_yaw(0, 0, 0, 0)
    with pytest.raises(ValueError):
        mod.quaternion_yaw(math.sin(.1), 0, 0, math.cos(.1))
    assert mod.quaternion_yaw(0, 0, math.sin(.4), math.cos(.4)) == pytest.approx(.8)


def test_invalid_grids_rejected():
    with pytest.raises(ValueError):
        mod.grid_from_occupancy([0], 2, 2)
    with pytest.raises(ValueError):
        mod.grid_from_occupancy([101, 0, 0, 0], 2, 2)
    with pytest.raises(ValueError):
        mod.grid_from_occupancy([0], 1, 1, inflation_cells=21)


def test_validated_path_checks_blocked_and_wrong_endpoints():
    grid = np.zeros((4, 4), dtype=np.uint8)
    grid[1, 1] = 1
    astar = lambda g,s,t: ([(0,0),(1,0),(2,0)], 3)
    assert mod.validated_plan(grid, (0,0), (2,0), astar)[1] == 3
    with pytest.raises(ValueError):
        mod.validated_plan(grid, (1,1), (2,0), astar)
    with pytest.raises(AssertionError):
        mod.validated_plan(grid, (0,0), (3,0), astar)
    with pytest.raises(AssertionError):
        mod.validated_plan(grid, (0,0), (2,0), lambda *_: ([(0,0),(2,0)],2))
