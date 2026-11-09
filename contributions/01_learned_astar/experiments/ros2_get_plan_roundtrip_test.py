"""Live ROS 2 Jazzy GetPlan service roundtrip for C01, with a non-actuating fixture.

This proves ROS message transport / service integration, NOT physical robot
control. The independent official ROS bag replay validates real sensor traffic.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--ros-map-yaml", type=Path, default=None, help="official real ROS map.yaml with image next to it")
    parser.add_argument("--expected-mode", choices=["astar_manhattan", "learned_raw", "learned_manhattan_clipped"], default="astar_manhattan")
    args = parser.parse_args()

    import rclpy
    from rclpy.node import Node
    from nav_msgs.msg import OccupancyGrid
    from nav_msgs.srv import GetPlan
    from std_msgs.msg import String

    rclpy.init()
    node = Node("c01_get_plan_actual_ros2_roundtrip_test")
    pub = node.create_publisher(OccupancyGrid, "/c01/test_grid", 10)
    client = node.create_client(GetPlan, "/c01/get_plan")
    received_diagnostics = []
    diag_sub = node.create_subscription(String, "/c01/diagnostics", lambda msg: received_diagnostics.append(json.loads(msg.data)), 10)
    try:
        start_wait = time.monotonic()
        while not client.wait_for_service(timeout_sec=0.25):
            if time.monotonic() - start_wait > 20:
                raise RuntimeError("C01 ROS2 GetPlan service unavailable")
        grid = OccupancyGrid()
        grid.header.frame_id = "map"
        if args.ros_map_yaml:
            import math
            import sys
            repo_root = Path(__file__).resolve().parents[3]
            experiments = Path(__file__).resolve().parent
            for root in (str(repo_root), str(experiments)):
                if root not in sys.path:
                    sys.path.insert(0, root)
            from dynnav.mapping.ros_map import load_ros_map
            from eval_real_ros_map import map_to_array, free_components, sample_tasks
            real_map = load_ros_map(args.ros_map_yaml, unknown_as_obstacle=True)
            numpy_grid = map_to_array(real_map)
            start_cell, goal_cell = sample_tasks(free_components(numpy_grid), 1, 8, 17)[0]
            grid.info.width = int(real_map.grid.width)
            grid.info.height = int(real_map.grid.height)
            grid.info.resolution = float(real_map.resolution)
            grid.info.origin.position.x = float(real_map.origin_x)
            grid.info.origin.position.y = float(real_map.origin_y)
            grid.info.origin.orientation.z = math.sin(real_map.origin_yaw/2)
            grid.info.origin.orientation.w = math.cos(real_map.origin_yaw/2)
            grid.data = (numpy_grid.astype("int16") * 100).ravel().tolist()
            start_x, start_y = real_map.cell_center(start_cell)
            goal_x, goal_y = real_map.cell_center(goal_cell)
            evidence_label = "actual_ros2_getplan_real_office_map_offline_generated_query"
        else:
            grid.info.width = 12
            grid.info.height = 12
            grid.info.resolution = 0.25
            grid.info.origin.orientation.w = 1.0
            matrix = [0]*144
            for y in range(12):
                if y != 6:
                    matrix[y*12 + 6] = 100
            grid.data = matrix
            start_x, start_y = (1+.5)*.25, (1+.5)*.25
            goal_x, goal_y = (10+.5)*.25, (10+.5)*.25
            evidence_label = "actual_ros2_jazzy_getplan_message_roundtrip_synthetic_map"
        req = GetPlan.Request()
        req.start.header.frame_id = "map"
        req.start.pose.position.x = start_x
        req.start.pose.position.y = start_y
        req.start.pose.orientation.w = 1.0
        req.goal.header.frame_id = "map"
        req.goal.pose.position.x = goal_x
        req.goal.pose.position.y = goal_y
        req.goal.pose.orientation.w = 1.0

        # ROS message delivery is asynchronous; publish the actual grid
        # repeatedly before and while waiting for the service reply.
        for _ in range(5):
            pub.publish(grid)
            rclpy.spin_once(node, timeout_sec=0.15)
        fut = client.call_async(req)
        deadline = time.monotonic()+(120 if args.ros_map_yaml else 25)
        while rclpy.ok() and not fut.done() and time.monotonic() < deadline:
            pub.publish(grid)
            rclpy.spin_once(node, timeout_sec=0.1)
        if not fut.done():
            raise RuntimeError("C01 GetPlan timed out")
        response = fut.result()
        if response is None or len(response.plan.poses) < 2:
            raise RuntimeError("C01 returned no route")
        first, last = response.plan.poses[0], response.plan.poses[-1]
        if (abs(first.pose.position.x-req.start.pose.position.x) > .13 or
            abs(last.pose.position.x-req.goal.pose.position.x) > .13):
            raise AssertionError("C01 grid-to-world endpoints wrong")
        for _ in range(20):
            if received_diagnostics:
                break
            rclpy.spin_once(node, timeout_sec=0.1)
        if not received_diagnostics:
            raise RuntimeError("C01 ROS2 diagnostics were not received")
        diagnostic = received_diagnostics[-1]
        if diagnostic.get("mode") != args.expected_mode:
            raise AssertionError(f"Expected {args.expected_mode}, got {diagnostic}")
        if args.expected_mode.startswith("learned_"):
            if not diagnostic.get("checkpoint_sha256"):
                raise AssertionError("Learned ROS2 planner did not report a loaded checkpoint")
        if diagnostic.get("evidence") != "planning_only_not_robot_motion":
            raise AssertionError("ROS2 diagnostics evidence type missing or misleading")
        out = {
            "evidence_type": evidence_label,
            "official_map_yaml": str(args.ros_map_yaml) if args.ros_map_yaml else None,
            "ros2_get_plan_success": True,
            "number_path_poses": len(response.plan.poses),
            "frame_id": response.plan.header.frame_id,
            "selected_mode": args.expected_mode,
            "diagnostics": diagnostic,
            "recorded_sensor_bag_input_to_this_test": False,
            "robot_motion_commanded": False,
            "physical_robot_trial": False,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print(json.dumps(out,indent=2,sort_keys=True))
        return 0
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
