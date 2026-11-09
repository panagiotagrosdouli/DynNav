"""C01 ROS2 *simulated* closed-loop navigation, not physical robot operation.

Actual rclpy GetPlan service -> Waypoint controller -> isolated Twist topic
-> kinematic differential-drive plant -> Odometry -> controller feedback.

Only publishes to /c01/isolated_sim/cmd_vel, never to robot /cmd_vel.
The environment is a synthetic grid / kinematic simulator, NOT Gazebo
and NOT a real robot. A passed result proves software control-loop wiring.
"""
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path


def clamp(v, limit):
    return max(-limit, min(limit, v))


def normalize(a):
    return math.atan2(math.sin(a), math.cos(a))


def make_map():
    # 12x12 synthetic grid with one 2.75m-long wall; gap at row 6.
    values = [0] * 144
    for y in range(12):
        if y != 6:
            values[y * 12 + 6] = 100
    return values


def collision_free(x, y, cells, resolution):
    col, row = math.floor(x / resolution), math.floor(y / resolution)
    return 0 <= col < 12 and 0 <= row < 12 and cells[row*12+col] == 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("astar_manhattan","learned_raw","learned_manhattan_clipped"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-steps", type=int, default=1800)
    args = parser.parse_args()

    import rclpy
    from rclpy.node import Node
    from nav_msgs.msg import OccupancyGrid, Odometry
    from nav_msgs.srv import GetPlan
    from geometry_msgs.msg import Twist
    from std_msgs.msg import String

    class SimTrial(Node):
        def __init__(self):
            super().__init__("c01_isolated_kinematic_ros2_trial")
            self.grid_values = make_map()
            self.resolution = 0.25
            self.x = 0.375
            self.y = 0.375
            self.yaw = 0.0
            self.last_cmd = Twist()
            self.cmd_count = 0
            self.odom_count = 0
            self.drive_commands = []
            self.trace = []
            self.collisions = 0
            self.path = []
            self.waypoint = 1
            self.diag = []
            self.status = "waiting"
            self.sim_dt = 0.1
            self.steps = 0
            self.map_pub = self.create_publisher(OccupancyGrid, "/c01/isolated_sim/map", 10)
            self.cmd_pub = self.create_publisher(Twist, "/c01/isolated_sim/cmd_vel", 10)
            self.odom_pub = self.create_publisher(Odometry, "/c01/isolated_sim/odom", 10)
            self.cmd_sub = self.create_subscription(
                Twist, "/c01/isolated_sim/cmd_vel", self.receive_cmd, 10
            )
            self.odom_sub = self.create_subscription(
                Odometry, "/c01/isolated_sim/odom", self.receive_odom, 10
            )
            self.diag_sub = self.create_subscription(
                String, "/c01/diagnostics", lambda m: self.diag.append(json.loads(m.data)), 10
            )
            self.client = self.create_client(GetPlan, "/c01/get_plan")
            self.timer = self.create_timer(0.02, self.tick)
            self.last_odom = None

        def make_occupancy(self):
            msg = OccupancyGrid()
            msg.header.frame_id = "map"
            msg.info.width = 12
            msg.info.height = 12
            msg.info.resolution = self.resolution
            msg.info.origin.orientation.w = 1.0
            msg.data = list(self.grid_values)
            return msg

        def receive_cmd(self, msg):
            self.last_cmd = msg
            self.cmd_count += 1
            self.drive_commands.append((float(msg.linear.x), float(msg.angular.z)))

        def receive_odom(self, msg):
            self.last_odom = msg
            self.odom_count += 1

        def start_request(self):
            from geometry_msgs.msg import PoseStamped
            req = GetPlan.Request()
            req.start.header.frame_id = "map"
            req.goal.header.frame_id = "map"
            req.start.pose.position.x = self.x
            req.start.pose.position.y = self.y
            req.start.pose.orientation.w = 1.0
            req.goal.pose.position.x = (10.5)*self.resolution
            req.goal.pose.position.y = (10.5)*self.resolution
            req.goal.pose.orientation.w = 1.0
            self.future = self.client.call_async(req)
            self.status = "planning"

        def tick(self):
            if self.status in {"finished","failed"}:
                return
            self.map_pub.publish(self.make_occupancy())
            if self.status == "waiting":
                if self.client.service_is_ready():
                    self.start_request()
                return
            if self.status == "planning":
                if not self.future.done():
                    return
                outcome = self.future.result()
                if not outcome or len(outcome.plan.poses) < 2:
                    self.status = "failed"
                    return
                self.path = [
                    (float(p.pose.position.x), float(p.pose.position.y))
                    for p in outcome.plan.poses
                ]
                self.status = "driving"
                return
            # Integrate the latest Twist delivered through ROS2 topic transport.
            # This is a kinematic model, not a physical or Gazebo robot.
            old_x, old_y = self.x, self.y
            linear = clamp(float(self.last_cmd.linear.x), 0.65)
            angular = clamp(float(self.last_cmd.angular.z), 2.5)
            self.x += linear * math.cos(self.yaw) * self.sim_dt
            self.y += linear * math.sin(self.yaw) * self.sim_dt
            self.yaw = normalize(self.yaw + angular * self.sim_dt)
            self.steps += 1
            if not collision_free(self.x,self.y,self.grid_values,self.resolution):
                self.collisions += 1
                self.status = "failed"
                self.publish_stop()
                return
            odom = Odometry()
            odom.header.frame_id = "map"
            odom.child_frame_id = "base_link_simulated"
            odom.pose.pose.position.x = self.x
            odom.pose.pose.position.y = self.y
            odom.pose.pose.orientation.z = math.sin(self.yaw / 2)
            odom.pose.pose.orientation.w = math.cos(self.yaw / 2)
            self.odom_pub.publish(odom)
            self.trace.append({"step":self.steps,"x":self.x,"y":self.y,"yaw":self.yaw,
                               "v":linear,"w":angular})
            if self.last_odom is None:
                return
            # Waypoint controller consumes the subscribed odom, not merely
            # an internal estimated pose. Never send this Twist to /cmd_vel.
            px = float(self.last_odom.pose.pose.position.x)
            py = float(self.last_odom.pose.pose.position.y)
            while self.waypoint < len(self.path):
                tx,ty = self.path[self.waypoint]
                if math.hypot(tx-px,ty-py) < 0.10:
                    self.waypoint += 1
                else:
                    break
            if self.waypoint >= len(self.path):
                self.status = "finished"
                self.publish_stop()
                return
            tx,ty = self.path[self.waypoint]
            heading = math.atan2(ty-py,tx-px)
            error = normalize(heading-self.yaw)
            cmd = Twist()
            cmd.angular.z = float(clamp(3.0*error,2.0))
            cmd.linear.x = float(min(0.48, max(0.0, math.hypot(tx-px,ty-py)*2.0))) if abs(error)<0.35 else 0.0
            self.cmd_pub.publish(cmd)
            if self.steps >= args.max_steps:
                self.status = "failed"
                self.publish_stop()

        def publish_stop(self):
            self.cmd_pub.publish(Twist())

    rclpy.init()
    node = SimTrial()
    started = time.monotonic()
    try:
        wall_deadline = started + 100.0
        while rclpy.ok() and time.monotonic() < wall_deadline:
            rclpy.spin_once(node,timeout_sec=0.03)
            if node.status in {"finished","failed"}:
                for _ in range(8):
                    rclpy.spin_once(node,timeout_sec=0.02)
                break
        else:
            node.status = "failed"
        final_distance = math.hypot(node.x-2.625,node.y-2.625)
        executed_length = sum(
            math.hypot(b["x"]-a["x"],b["y"]-a["y"])
            for a,b in zip(node.trace,node.trace[1:])
        )
        diagnostics = [x for x in node.diag if x.get("mode")==args.mode]
        report={
            "evidence_type":"real_ros2_closed_loop_ISOLATED_KINEMATIC_SIMULATION",
            "ros2_closed_loop_completed":node.status=="finished" and final_distance<0.12 and node.collisions==0,
            "mode":args.mode,
            "ros2_getplan_received":len(node.path)>1,
            "planner_diagnostics":diagnostics[-1] if diagnostics else None,
            "path_poses":len(node.path),
            "ros2_twist_messages_received":node.cmd_count,
            "ros2_odometry_messages_received":node.odom_count,
            "simulator_steps":node.steps,
            "simulated_duration_seconds":node.steps*node.sim_dt,
            "measured_wall_seconds":time.monotonic()-started,
            "executed_distance_m":executed_length,
            "distance_from_goal_m":final_distance,
            "grid_collision_count":node.collisions,
            "max_requested_linear_m_s":max((abs(x) for x,_ in node.drive_commands),default=0.0),
            "trajectory":node.trace,
            "simulator_type":"deterministic 2D kinematic differential-drive; NOT Gazebo, not physics, not a physical Dingo",
            "hardware_motion_commanded":False,
            "actual_dingo_navigation":False,
            "physical_robot_trial":False,
            "safety_boundary":"all synthetic commands confined to /c01/isolated_sim/cmd_vel",
        }
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
        print(json.dumps({k:v for k,v in report.items() if k!="trajectory"},indent=2))
        return 0 if report["ros2_closed_loop_completed"] and node.cmd_count>0 and node.odom_count>0 and diagnostics else 2
    finally:
        node.publish_stop()
        node.destroy_node()
        rclpy.shutdown()


if __name__=="__main__":
    raise SystemExit(main())
