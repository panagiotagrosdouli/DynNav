"""Read-only ROS 2 topic observation for onsite C01 hardware commissioning.

Never publishes cmd_vel or triggers NavigateToPose. A passed topic observation
does NOT prove an emergency stop was tested or that C01 controlled the robot.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


REQUIRED = {
    "/scan": "sensor_msgs/msg/LaserScan",
    "/odom": "nav_msgs/msg/Odometry",
    "/tf": "tf2_msgs/msg/TFMessage",
}
OPTIONAL = {
    "/tf_static": "tf2_msgs/msg/TFMessage",
    "/amcl_pose": "geometry_msgs/msg/PoseWithCovarianceStamped",
    "/global_costmap/costmap": "nav_msgs/msg/OccupancyGrid",
    "/cmd_vel": "geometry_msgs/msg/Twist",
}


def summarize_topics(observed: dict[str, list[str]], fresh: dict[str, bool]) -> dict:
    """Assess limited ROS message readiness, never human safety approval."""
    missing = [topic for topic, typ in REQUIRED.items() if typ not in observed.get(topic, [])]
    stale = [topic for topic in REQUIRED if topic not in missing and not fresh.get(topic, False)]
    return {
        "status": "TOPIC_OBSERVATION_ONLY" if not missing and not stale else "ROBOT_TOPICS_INCOMPLETE",
        "missing_topics": missing,
        "not_observed_during_window": stale,
        "optional_topics_present": {
            topic: typ in observed.get(topic, [])
            for topic, typ in OPTIONAL.items()
        },
        "physical_motion_validated": False,
        "c01_planner_execution_validated": False,
        "emergency_stop_validated": False,
        "note": "Onsite hardware operator must separately verify TF, calibration, physical stop, footprint, Nav2 planner identity, and actual trial logs.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=10.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not (1 <= args.seconds <= 120):
        parser.error("--seconds must be between 1 and 120")

    try:
        import rclpy
        from rclpy.node import Node
        from rclpy.qos import qos_profile_sensor_data, QoSProfile, DurabilityPolicy
        from sensor_msgs.msg import LaserScan
        from nav_msgs.msg import Odometry
        from tf2_msgs.msg import TFMessage
    except ImportError as exc:
        raise SystemExit("ROS 2 environment missing; source /opt/ros/jazzy/setup.bash") from exc

    rclpy.init()
    node = Node("c01_readonly_hardware_readiness")
    last_seen: dict[str, float] = {}
    subscriptions = []
    def capture(name):
        def on_msg(message):
            last_seen[name] = time.monotonic()
        return on_msg

    subscriptions.append(node.create_subscription(LaserScan, "/scan", capture("/scan"), qos_profile_sensor_data))
    subscriptions.append(node.create_subscription(Odometry, "/odom", capture("/odom"), 10))
    subscriptions.append(node.create_subscription(TFMessage, "/tf", capture("/tf"), 10))
    started = time.monotonic()
    try:
        while rclpy.ok() and time.monotonic() - started < args.seconds:
            rclpy.spin_once(node, timeout_sec=0.25)
        seen_types = {name: types for name, types in node.get_topic_names_and_types()}
        result = summarize_topics(seen_types, {topic: topic in last_seen for topic in REQUIRED})
        result.update({
            "observation_window_s": args.seconds,
            "observed_required_topics": sorted(last_seen),
            "observed_topic_types": {k: seen_types.get(k, []) for k in sorted(REQUIRED | OPTIONAL)},
            "scope": "readonly_live_ros_graph; never movement evidence",
        })
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["status"] == "TOPIC_OBSERVATION_ONLY" else 2
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
