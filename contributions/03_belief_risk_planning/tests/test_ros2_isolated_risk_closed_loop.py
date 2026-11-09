"""C03 isolated ROS2 kinematic test geometry and safety-contract regressions."""
import importlib.util
import sys
from pathlib import Path
import pytest

SCRIPT=Path(__file__).resolve().parents[1]/"experiments"/"ros2_isolated_risk_closed_loop.py"
spec=importlib.util.spec_from_file_location("c03_isolated_kinematic",SCRIPT)
module=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=module
spec.loader.exec_module(module)

def test_simulated_topics_and_grid_are_isolated():
    assert module.make_map().count(100)==11
    assert module.collision_free(.375,.375,module.make_map(),.25)
    assert not module.collision_free(6.5*.25,5.5*.25,module.make_map(),.25)
    assert module.collision_free(6.5*.25,6.5*.25,module.make_map(),.25)

def test_velocity_clamps_and_angles():
    assert module.clamp(3.0,.5)==.5
    assert module.clamp(-2.0,.5)==-.5
    assert module.normalize(0.0)==pytest.approx(0.0)

def test_no_physical_actuation_topic_in_source():
    text=SCRIPT.read_text(encoding="utf-8")
    assert '"/c03/isolated_sim/cmd_vel"' in text
    assert 'create_publisher(Twist, "/cmd_vel"' not in text
    assert 'physical_robot_trial":False' in text
