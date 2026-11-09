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
    args = parser.parse_args()

    import rclpy
    from rclpy.node import Node
    from nav_msgs.msg import OccupancyGrid
    from nav_msgs.srv import GetPlan

    rclpy.init()
    node = Node("c01_get_plan_actual_ros2_roundtrip_test")
    pub = node.create_publisher(OccupancyGrid, "/c01/test_grid", 10)
    client = node.create_client(GetPlan, "/c01/get_plan")
    try:
        start_wait = time.monotonic()
        while not client.wait_for_service(timeout_sec=0.25):
            if time.monotonic() - start_wait > 20:
                raise RuntimeError("C01 ROS2 GetPlan service unavailable")
        grid = OccupancyGrid()
        grid.header.frame_id = "map"
        grid.info.width = 12
        grid.info.height = 12
        grid.info.resolution = 0.25
        grid.info.origin.orientation.w = 1.0
        matrix = [0]*144
        for y in range(12):
            if y != 6:
                matrix[y*12 + 6] = 100
        grid.data = matrix
        req = GetPlan.Request()
        req.start.header.frame_id = "map"
        req.start.pose.position.x = (1+.5)*.25
        req.start.pose.position.y = (1+.5)*.25
        req.start.pose.orientation.w = 1.0
        req.goal.header.frame_id = "map"
        req.goal.pose.position.x = (10+.5)*.25
        req.goal.pose.position.y = (10+.5)*.25
        req.goal.pose.orientation.w = 1.0

        # ROS message delivery is asynchronous; publish the actual grid
        # repeatedly before and while waiting for the service reply.
        for _ in range(5):
            pub.publish(grid)
            rclpy.spin_once(node, timeout_sec=0.15)
        fut = client.call_async(req)
        deadline = time.monotonic()+25
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
        out = {
            "evidence_type": "actual_ros2_jazzy_getplan_message_roundtrip_synthetic_map",
            "ros2_get_plan_success": True,
            "number_path_poses": len(response.plan.poses),
            "frame_id": response.plan.header.frame_id,
            "selected_mode": "astar_manhattan",
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
