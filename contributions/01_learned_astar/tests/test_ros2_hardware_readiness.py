"""Read-only C01 hardware readiness policy tests; no live robot needed."""
import importlib.util
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "experiments" / "ros2_hardware_readiness.py"
spec = importlib.util.spec_from_file_location("c01_ros_readiness", SCRIPT)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def test_complete_ros_topics_never_claim_hardware_efficacy():
    detected = dict(mod.REQUIRED)
    result = mod.summarize_topics({k: [v] for k, v in detected.items()}, {k: True for k in detected})
    assert result["status"] == "TOPIC_OBSERVATION_ONLY"
    assert result["physical_motion_validated"] is False
    assert result["c01_planner_execution_validated"] is False
    assert result["emergency_stop_validated"] is False


def test_missing_scan_rejected():
    result = mod.summarize_topics({"/odom": ["nav_msgs/msg/Odometry"], "/tf": ["tf2_msgs/msg/TFMessage"]}, {"/odom": True, "/tf": True})
    assert result["status"] == "ROBOT_TOPICS_INCOMPLETE"
    assert "/scan" in result["missing_topics"]


def test_no_received_frames_rejected_even_when_advertised():
    result = mod.summarize_topics({k: [v] for k,v in mod.REQUIRED.items()}, {k: False for k in mod.REQUIRED})
    assert result["status"] == "ROBOT_TOPICS_INCOMPLETE"
    assert "/odom" in result["not_observed_during_window"]


def test_optional_topics_do_not_imply_c01_controller():
    observed = {k: [v] for k,v in (mod.REQUIRED | mod.OPTIONAL).items()}
    result = mod.summarize_topics(observed, {k: True for k in mod.REQUIRED})
    assert all(result["optional_topics_present"].values())
    assert result["c01_planner_execution_validated"] is False
