"""C01 isolated ROS2 closed-loop helper contracts (no hardware required)."""
import importlib.util
import math
import sys
from pathlib import Path

import pytest

FILE=Path(__file__).resolve().parents[1] / "experiments" / "ros2_isolated_closed_loop.py"
spec=importlib.util.spec_from_file_location("c01_simulated_loop",FILE)
mod=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=mod
spec.loader.exec_module(mod)


def test_motion_limits_and_wrap():
    assert mod.clamp(5,0.5)==0.5
    assert mod.clamp(-9,0.5)==-0.5
    assert mod.normalize(3*math.pi)==pytest.approx(math.pi)


def test_isolated_grid_gap_and_barrier():
    grid=mod.make_map()
    assert mod.collision_free(6.5*.25,6.5*.25,grid,.25)
    assert not mod.collision_free(6.5*.25,4.5*.25,grid,.25)
    assert not mod.collision_free(-.01,.5,grid,.25)
    assert not mod.collision_free(3.1,.5,grid,.25)


def test_obstacle_world_coordinates_and_geometry():
    grid=mod.make_map()
    assert sum(v==100 for v in grid)==11
    for y in range(12):
        assert mod.collision_free(.375, (y+.5)*.25,grid,.25)
