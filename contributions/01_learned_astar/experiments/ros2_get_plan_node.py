"""Planning-only ROS 2 GetPlan service exposing the *actual* C01 A* algorithms.

Run inside a ROS 2 Jazzy environment with rclpy, nav_msgs and geometry_msgs.
This node NEVER publishes /cmd_vel or sends navigation goals. It is NOT a
Nav2 GlobalPlanner plugin; integrating with a robot controller requires a
separate, reviewed Nav2 adapter and human-supervised safety commissioning.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

THIS = Path(__file__).resolve().parent
CODE = THIS.parent / "code"
for folder in (THIS, CODE):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

from ros2_grid_geometry import (  # noqa: E402
    GridGeometry, grid_from_occupancy, quaternion_yaw, validated_plan,
)
from astar_learned_heuristic import (  # noqa: E402
    LearnedHeuristicWrapper, astar_classic, astar_learned,
)


def main() -> None:
    try:
        import rclpy
        from rclpy.node import Node
        from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
        from nav_msgs.msg import OccupancyGrid, Path as RosPath
        from nav_msgs.srv import GetPlan
        from geometry_msgs.msg import PoseStamped
        from std_msgs.msg import String
    except ImportError as exc:
        raise SystemExit(
            "ROS 2 Jazzy runtime packages required: source /opt/ros/jazzy/setup.bash"
        ) from exc

    class C01PlanService(Node):
        def __init__(self) -> None:
            super().__init__("c01_learned_astar_planning_only")
            self.declare_parameter("map_topic", "/global_costmap/costmap")
            self.declare_parameter("mode", "astar_manhattan")
            self.declare_parameter("checkpoint", "")
            self.declare_parameter("lethal_threshold", 50)
            self.declare_parameter("inflation_cells", 0)
            self.mode = str(self.get_parameter("mode").value)
            if self.mode not in {"astar_manhattan", "learned_raw", "learned_manhattan_clipped"}:
                raise ValueError("unsupported C01 planner mode")
            self.checkpoint = str(self.get_parameter("checkpoint").value)
            self.model_sha256 = None
            self.learned = None
            if self.mode != "astar_manhattan":
                model_path = Path(self.checkpoint).expanduser().resolve()
                if not model_path.is_file():
                    raise FileNotFoundError("C01 checkpoint is required; fallback is prohibited")
                self.model_sha256 = hashlib.sha256(model_path.read_bytes()).hexdigest()
                self.learned = LearnedHeuristicWrapper(
                    model_path=model_path, mode=self.mode.replace("learned_", ""),
                    allow_missing_model=False,
                )
                # Explicit mapping: learned_raw => raw; learned_manhattan_clipped => manhattan_clipped.
                if self.learned.model is None:
                    raise RuntimeError("C01 checkpoint was not loaded")
            self.latest_map = None
            self.map_sub = self.create_subscription(
                OccupancyGrid, str(self.get_parameter("map_topic").value),
                self.on_map, QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE, durability=DurabilityPolicy.VOLATILE),
            )
            self.plan_pub = self.create_publisher(RosPath, "c01/plan", 10)
            self.diag_pub = self.create_publisher(String, "c01/diagnostics", 10)
            self.srv = self.create_service(GetPlan, "c01/get_plan", self.on_plan)
            self.get_logger().info(
                f"C01 planning ONLY: mode={self.mode}; model_sha256={self.model_sha256}; "
                f"map_topic={self.get_parameter('map_topic').value}; NO motion commands"
            )

        def on_map(self, msg) -> None:
            self.latest_map = msg

        def on_plan(self, request, response):
            if self.latest_map is None:
                self.get_logger().error("No costmap available; returning empty plan")
                return response
            msg = self.latest_map
            frame = msg.header.frame_id
            if request.start.header.frame_id != frame or request.goal.header.frame_id != frame:
                self.get_logger().error("Frame mismatch: requests must be transformed by caller")
                return response
            try:
                origin = msg.info.origin
                yaw = quaternion_yaw(
                    origin.orientation.x, origin.orientation.y,
                    origin.orientation.z, origin.orientation.w,
                )
                geom = GridGeometry(
                    float(msg.info.resolution), float(origin.position.x),
                    float(origin.position.y), yaw, frame,
                )
                grid = grid_from_occupancy(
                    msg.data, int(msg.info.width), int(msg.info.height),
                    lethal_threshold=int(self.get_parameter("lethal_threshold").value),
                    inflation_cells=int(self.get_parameter("inflation_cells").value),
                )
                start = geom.world_to_cell(
                    request.start.pose.position.x, request.start.pose.position.y,
                )
                goal = geom.world_to_cell(
                    request.goal.pose.position.x, request.goal.pose.position.y,
                )
                planner = astar_classic if self.learned is None else (
                    lambda g,s,t: astar_learned(g,s,t,self.learned)
                )
                t0 = time.perf_counter()
                path, expansions = validated_plan(grid, start, goal, planner)
                elapsed_ms = (time.perf_counter()-t0)*1000.0
                plan = RosPath()
                plan.header = msg.header
                if path is not None:
                    for cx, cy in path:
                        x, y = geom.cell_to_world(cx, cy)
                        pose = PoseStamped()
                        pose.header = plan.header
                        pose.pose.position.x = float(x)
                        pose.pose.position.y = float(y)
                        pose.pose.orientation.w = 1.0
                        plan.poses.append(pose)
                response.plan = plan
                self.plan_pub.publish(plan)
                diagnostics = {
                    "mode": self.mode,
                    "checkpoint_sha256": self.model_sha256,
                    "map_frame": frame,
                    "start_cell": start,
                    "goal_cell": goal,
                    "path_cost_cells": len(path)-1 if path else None,
                    "expansions": expansions,
                    "planning_latency_ms": elapsed_ms,
                    "path_found": path is not None,
                    "evidence": "planning_only_not_robot_motion",
                }
                diag = String()
                diag.data = json.dumps(diagnostics, sort_keys=True)
                self.diag_pub.publish(diag)
            except (ValueError, AssertionError, RuntimeError) as exc:
                self.get_logger().error(f"C01 planning rejected: {exc}")
                return response
            return response

    rclpy.init()
    node = None
    try:
        node = C01PlanService()
        rclpy.spin(node)
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
