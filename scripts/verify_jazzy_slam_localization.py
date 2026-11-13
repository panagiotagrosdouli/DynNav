#!/usr/bin/env python3
"""Execute live Gazebo -> SLAM -> saved map -> AMCL -> navigation integration.

Run only in a sourced Ubuntu 24.04/Jazzy environment with Harmonic/Nav2.
Artifacts and failures are retained. This is not a physical-robot trial or a
localization accuracy experiment against independent simulator ground truth.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import signal
import subprocess
import time
from pathlib import Path

import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped, Twist, TwistStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from nav_msgs.msg import OccupancyGrid, Odometry
from rclpy.parameter import Parameter
from rclpy.qos import DurabilityPolicy, QoSProfile, qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from tf2_ros import Buffer, TransformListener


class Probe:
    def __init__(self):
        self.node = rclpy.create_node("dynnav_live_slam_probe")
        self.node.set_parameters([Parameter("use_sim_time", value=True)])
        self.counts = dict(scan=0, odom=0, map=0, amcl=0)
        self.map = None
        self.yaws = []
        self.scan_frames = set()
        self.last_scan_stamp = None
        self.node.create_subscription(LaserScan, "/scan", self.scan, qos_profile_sensor_data)
        self.node.create_subscription(Odometry, "/odom", self.odom, qos_profile_sensor_data)
        qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.node.create_subscription(OccupancyGrid, "/map", self.mapping, qos)
        self.node.create_subscription(PoseWithCovarianceStamped, "/amcl_pose", self.amcl, qos_profile_sensor_data)
        self.buffer = Buffer()
        self.listener = TransformListener(self.buffer, self.node)

    def scan(self, msg):
        finite = sum(math.isfinite(v) and msg.range_min <= v <= msg.range_max for v in msg.ranges)
        if finite and msg.header.frame_id:
            stamp = msg.header.stamp.sec * 1_000_000_000 + msg.header.stamp.nanosec
            now = self.node.get_clock().now().nanoseconds
            if 0 < stamp <= now + 50_000_000 and now - stamp < 2_000_000_000:
                self.counts["scan"] += 1
                self.scan_frames.add(msg.header.frame_id)
                self.last_scan_stamp = stamp

    def odom(self, msg):
        if msg.header.frame_id and msg.child_frame_id:
            self.counts["odom"] += 1
            q = msg.pose.pose.orientation
            self.yaws.append(math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y**2 + q.z**2)))

    def mapping(self, msg):
        if msg.header.frame_id == "map" and msg.info.resolution > 0:
            self.counts["map"] += 1
            self.map = msg

    def amcl(self, msg):
        if msg.header.frame_id == "map" and all(math.isfinite(v) for v in msg.pose.covariance):
            self.counts["amcl"] += 1

    def wait(self, predicate, seconds, label):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            rclpy.spin_once(self.node, timeout_sec=0.1)
            if predicate():
                return
        raise RuntimeError("Timed out: " + label + "; counts=" + repr(self.counts))

    def transform(self, target, source):
        return self.buffer.lookup_transform(target, source, rclpy.time.Time())

    def snapshot(self):
        return dict(counts=self.counts, scan_frames=sorted(self.scan_frames), last_scan_stamp=self.last_scan_stamp)


def stop(process):
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGINT)
        try:
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=10)


def launch(slam, directory, map_file=None):
    command = [
        "ros2",
        "launch",
        "nav2_bringup",
        "tb3_simulation_launch.py",
        "slam:=" + str(slam),
        "headless:=True",
        "use_rviz:=False",
        "use_composition:=False",
        "use_sim_time:=True",
        "autostart:=True",
    ]
    if map_file:
        command.append("map:=" + str(map_file))
    log = (directory / ("slam-launch.log" if slam else "amcl-launch.log")).open("w")
    return subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True), log, command


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    directory = args.output.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    result = {
        "status": "failed",
        "evidence": "live_simulated_sensor_integration",
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "physical_robot_tested": False,
        "independent_ground_truth_accuracy_measured": False,
        "protocol": "live_slam_amcl_v1: rotate in place, save newly observed map, restart, localize, navigate 0.5m",
    }
    process = None
    probe = None
    rclpy.init()
    try:
        process, log, result["slam_command"] = launch(True, directory)
        probe = Probe()
        probe.wait(
            lambda: probe.map is not None and probe.counts["scan"] >= 10 and probe.counts["odom"] >= 10,
            150,
            "live scan, odometry and newly generated SLAM map",
        )
        initial_map_pose = probe.transform("map", "base_link").transform
        # Resolve the simulator's actual command type instead of assuming a ROS version default.
        types = dict(probe.node.get_topic_names_and_types()).get("/cmd_vel", [])
        stamped = "geometry_msgs/msg/TwistStamped" in types
        command_type = TwistStamped if stamped else Twist
        publisher = probe.node.create_publisher(command_type, "/cmd_vel", 10)
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            message = command_type()
            velocity = message.twist if stamped else message
            velocity.angular.z = 0.25
            if stamped:
                message.header.stamp = probe.node.get_clock().now().to_msg()
                message.header.frame_id = "base_link"
            publisher.publish(message)
            rclpy.spin_once(probe.node, timeout_sec=0.1)
        publisher.publish(command_type())
        if max(probe.yaws) - min(probe.yaws) < 0.2:
            raise RuntimeError("Odometry did not observe commanded robot rotation")
        known = sum(cell >= 0 for cell in probe.map.data)
        occupied = sum(cell > 50 for cell in probe.map.data)
        if known < 100 or occupied < 1:
            raise RuntimeError("Live SLAM map has insufficient observed structure")
        probe.transform("map", "odom")
        probe.transform("odom", "base_link")
        result["slam"] = dict(
            probe.snapshot(),
            known_cells=known,
            occupied_cells=occupied,
            map_width=probe.map.info.width,
            map_height=probe.map.info.height,
        )
        map_base = directory / "live_observed_map"
        subprocess.run(
            [
                "ros2",
                "run",
                "nav2_map_server",
                "map_saver_cli",
                "-f",
                str(map_base),
                "--ros-args",
                "-p",
                "use_sim_time:=true",
                "-p",
                "save_map_timeout:=10.0",
            ],
            check=True,
            timeout=30,
            stdout=(directory / "map-save.log").open("w"),
            stderr=subprocess.STDOUT,
        )
        map_file = map_base.with_suffix(".yaml")
        if not map_file.is_file() or not list(directory.glob("live_observed_map.p*")):
            raise RuntimeError("Map saving did not retain a map image and YAML")
        stop(process)
        log.close()
        probe.node.destroy_node()
        probe = None
        process, log, result["amcl_command"] = launch(False, directory, map_file)
        probe = Probe()
        navigator = BasicNavigator()
        navigator.set_parameters([Parameter("use_sim_time", value=True)])
        from geometry_msgs.msg import PoseStamped

        pose = PoseStamped()
        pose.header.frame_id = "map"
        pose.header.stamp = navigator.get_clock().now().to_msg()
        # SLAM's map origin need not equal Gazebo's world origin. The fresh robot
        # respawns at the same simulator pose; use its initial SLAM-frame pose.
        pose.pose.position.x = initial_map_pose.translation.x
        pose.pose.position.y = initial_map_pose.translation.y
        pose.pose.orientation = initial_map_pose.rotation
        deadline = time.monotonic() + 150
        while time.monotonic() < deadline and not probe.counts["amcl"]:
            navigator.setInitialPose(pose)
            rclpy.spin_once(probe.node, timeout_sec=0.2)
            rclpy.spin_once(navigator, timeout_sec=0.1)
        if not probe.counts["amcl"]:
            raise RuntimeError("AMCL did not publish a finite map-frame pose on the newly generated map")
        probe.transform("map", "base_link")
        pose.header.stamp = navigator.get_clock().now().to_msg()
        pose.pose.position.x += 0.5
        if not navigator.goToPose(pose):
            raise RuntimeError("Nav2 rejected the mapped/localized goal")
        deadline = time.monotonic() + 120
        while not navigator.isTaskComplete() and time.monotonic() < deadline:
            rclpy.spin_once(probe.node, timeout_sec=0.1)
        if navigator.getResult() != TaskResult.SUCCEEDED:
            navigator.cancelTask()
            raise RuntimeError("Navigation on the newly observed and reloaded map did not succeed")
        result["amcl_navigation"] = probe.snapshot()
        result["map_yaml_sha256"] = hashlib.sha256(map_file.read_bytes()).hexdigest()
        result["status"] = "passed"
        navigator.destroy_node()
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        if process is not None:
            stop(process)
        if probe is not None:
            probe.node.destroy_node()
        rclpy.shutdown()
        (directory / "result.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
