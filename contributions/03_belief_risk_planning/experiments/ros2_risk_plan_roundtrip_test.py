"""Live C03 ROS2 GetPlan request-response test, SYNTHETIC fixture only.

The actual C03 planning code runs in a separate rclpy server process. This
client publishes a synthetic grid and verifies path + planner diagnostics.
It NEVER publishes /cmd_vel or simulates physical robot navigation.
"""
from __future__ import annotations
import argparse
import json
import math
import time
from pathlib import Path

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",required=True,type=Path)
    parser.add_argument("--risk-weight",required=True,type=float)
    args=parser.parse_args()

    import rclpy
    from rclpy.node import Node
    from nav_msgs.msg import OccupancyGrid
    from nav_msgs.srv import GetPlan
    from std_msgs.msg import String

    rclpy.init()
    node=Node("c03_getplan_actual_ros2_client")
    grid_pub=node.create_publisher(OccupancyGrid,"/c03/test_grid",10)
    client=node.create_client(GetPlan,"/c03/get_plan")
    diagnostics=[]
    sub=node.create_subscription(String,"/c03/diagnostics",lambda m:diagnostics.append(json.loads(m.data)),10)
    try:
        deadline=time.monotonic()+15
        while not client.wait_for_service(timeout_sec=.25):
            if time.monotonic()>deadline:
                raise RuntimeError("Actual C03 ROS2 service unavailable")
        grid=OccupancyGrid()
        grid.header.frame_id="map"
        grid.info.width=12
        grid.info.height=12
        grid.info.resolution=.25
        grid.info.origin.orientation.w=1.
        data=[0]*144
        for row in range(12):
            if row!=6:
                data[row*12+6]=100
        grid.data=data
        req=GetPlan.Request()
        req.start.header.frame_id="map"
        req.start.pose.position.x=.375
        req.start.pose.position.y=.375
        req.start.pose.orientation.w=1.
        req.goal.header.frame_id="map"
        req.goal.pose.position.x=2.625
        req.goal.pose.position.y=2.625
        req.goal.pose.orientation.w=1.
        for _ in range(7):
            grid_pub.publish(grid)
            rclpy.spin_once(node,timeout_sec=.1)
        future=client.call_async(req)
        deadline=time.monotonic()+25
        while not future.done() and time.monotonic()<deadline:
            grid_pub.publish(grid)
            rclpy.spin_once(node,timeout_sec=.08)
        if not future.done() or not future.result():
            raise RuntimeError("C03 ROS2 service request failed")
        response=future.result()
        if len(response.plan.poses)<2:
            raise RuntimeError("C03 returned empty path")
        for _ in range(20):
            if diagnostics:break
            rclpy.spin_once(node,timeout_sec=.1)
        if not diagnostics:
            raise RuntimeError("C03 diagnostic topic was not delivered")
        diag=diagnostics[-1]
        if diag["risk_weight"]!=args.risk_weight or not diag["path_found"]:
            raise AssertionError(f"Unexpected planner mode/diagnostics: {diag}")
        if diag["physical_robot_trials"]!=0 or diag["cvar_is_optimization_objective"]:
            raise AssertionError("Unsafe C03 evidence classification")
        first,last=response.plan.poses[0],response.plan.poses[-1]
        if abs(first.pose.position.x-.375)>.13 or abs(last.pose.position.x-2.625)>.13:
            raise AssertionError("C03 coordinate endpoints do not match requests")
        result=dict(evidence_type="ACTUAL_ROS2_GETPLAN_WITH_SYNTHETIC_MAP",
                    ros2_request_response_success=True,
                    path_poses=len(response.plan.poses),
                    map_fixture_synthetic=True,
                    planner_diagnostics=diag,
                    physical_robot_control=False,
                    physical_robot_trials=0)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        print(json.dumps(result,indent=2,sort_keys=True))
        return 0
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__=="__main__":
    raise SystemExit(main())
