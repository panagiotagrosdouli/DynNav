"""Observe real recorded Dingo sensors replayed as actual ROS 2 Jazzy messages.

Used with *converted official ROS 1 bag* and ros2 bag play, NOT live hardware.
Never commands robot motion or alters motor topics. An offline replay does not
prove that C01 planned or controlled the source physical robot.
"""
from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=25.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not 5 <= args.seconds <= 180:
        parser.error("--seconds must be between 5 and 180")
    try:
        import rclpy
        from rclpy.node import Node
        from rclpy.qos import QoSProfile, ReliabilityPolicy
        from sensor_msgs.msg import LaserScan
        from nav_msgs.msg import Odometry
        from tf2_msgs.msg import TFMessage
    except ImportError as e:
        raise SystemExit("Real ROS 2 environment required (source /opt/ros/jazzy/setup.bash)") from e
    topic_classes = {
        "/laser_scan_front/scan": LaserScan,
        "/laser_scan_rear/scan": LaserScan,
        "/dingo_velocity_controller/odom": Odometry,
        "/tf": TFMessage,
    }
    counts = Counter()
    stamped = Counter()
    start = time.monotonic()
    rclpy.init()
    node = Node("c01_lilocbench_real_recording_replay_observer")
    # Best effort subscriber can interoperate with both reliable and sensor-data
    # publishers. No command publishers exist in this process.
    qos = QoSProfile(depth=20, reliability=ReliabilityPolicy.BEST_EFFORT)
    subs = []
    for topic, msgclass in topic_classes.items():
        def on_data(msg, topic=topic):
            counts[topic] += 1
            if hasattr(msg, "header") and msg.header.frame_id:
                stamped[topic] += 1
        subs.append(node.create_subscription(msgclass, topic, on_data, qos))
    try:
        while rclpy.ok() and time.monotonic()-start < args.seconds:
            rclpy.spin_once(node, timeout_sec=0.1)
            if all(counts[k] >= 5 for k in topic_classes):
                break
        result = {
            "evidence_type": "actual_recorded_robot_sensor_messages_replayed_in_ros2_jazzy",
            "topic_message_counts": dict(sorted(counts.items())),
            "nonempty_frame_id_counts": dict(sorted(stamped.items())),
            "required_topics": list(topic_classes),
            "ros2_subscription_pass": all(counts[k] >= 5 for k in topic_classes),
            "c01_planner_executed": False,
            "robot_motion_commanded": False,
            "physical_robot_control_verified": False,
            "source_recording": "official LILocBench dynamics_0 Clearpath Dingo no-camera bag",
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n", encoding="utf-8")
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["ros2_subscription_pass"] else 2
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
