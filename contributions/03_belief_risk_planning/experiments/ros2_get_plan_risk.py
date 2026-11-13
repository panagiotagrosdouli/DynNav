"""C03 actual ROS 2 GetPlan for additive proximity-risk A* (NO actuation).

Real ROS2 middleware and C03 implementation, but the obstacle-proximity
metric is a numerical risk proxy; not calibrated accident probability,
not CVaR-optimized stochastic navigation and not a Nav2 plugin.
"""
from __future__ import annotations
import json
import math
import sys
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
C01=HERE.parents[1]/"01_learned_astar"/"experiments"
for path in (HERE,C01):
    if str(path) not in sys.path:
        sys.path.insert(0,str(path))
from ros2_grid_geometry import GridGeometry, grid_from_occupancy, quaternion_yaw
from eval_real_map_proximity_risk import proximity_field,search,validate_path

def main():
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import QoSProfile,ReliabilityPolicy
    from nav_msgs.msg import OccupancyGrid,Path as RosPath
    from nav_msgs.srv import GetPlan
    from geometry_msgs.msg import PoseStamped
    from std_msgs.msg import String

    class RiskPlanService(Node):
        def __init__(self):
            super().__init__("c03_additive_risk_plan_service")
            self.declare_parameter("map_topic","/c03/map")
            self.declare_parameter("risk_weight",8.0)
            self.declare_parameter("decay_cells",5.0)
            self.declare_parameter("lethal_threshold",50)
            self.risk_weight=float(self.get_parameter("risk_weight").value)
            self.decay_cells=float(self.get_parameter("decay_cells").value)
            if not math.isfinite(self.risk_weight) or self.risk_weight<0:
                raise ValueError("Invalid C03 risk weight")
            if not math.isfinite(self.decay_cells) or self.decay_cells<=0:
                raise ValueError("Invalid C03 risk decay")
            self.latest_map=None
            self.risk_cache=None
            self.map_subscription=self.create_subscription(
                OccupancyGrid,str(self.get_parameter("map_topic").value),
                self.on_map,QoSProfile(depth=1,reliability=ReliabilityPolicy.RELIABLE))
            self.service=self.create_service(GetPlan,"/c03/get_plan",self.on_request)
            self.plan_pub=self.create_publisher(RosPath,"/c03/plan",10)
            self.diagnostics_pub=self.create_publisher(String,"/c03/diagnostics",10)

        def on_map(self,msg):
            try:
                grid=grid_from_occupancy(msg.data,int(msg.info.width),int(msg.info.height),
                                         lethal_threshold=int(self.get_parameter("lethal_threshold").value),
                                         inflation_cells=0)
                risk=proximity_field(grid,self.decay_cells)
            except (ValueError,AssertionError) as e:
                self.get_logger().error("Refused invalid occupancy grid: "+str(e))
                self.latest_map=None
                return
            self.latest_map=(msg,grid,risk)

        def on_request(self,request,response):
            if self.latest_map is None:
                self.get_logger().error("C03 map unavailable")
                return response
            msg,grid,risk=self.latest_map
            if request.start.header.frame_id!=msg.header.frame_id or request.goal.header.frame_id!=msg.header.frame_id:
                self.get_logger().error("C03 requires matched map frames, no implicit TF")
                return response
            origin=msg.info.origin
            yaw=quaternion_yaw(origin.orientation.x,origin.orientation.y,origin.orientation.z,origin.orientation.w)
            geo=GridGeometry(float(msg.info.resolution),float(origin.position.x),float(origin.position.y),yaw,msg.header.frame_id)
            start=geo.world_to_cell(request.start.pose.position.x,request.start.pose.position.y)
            goal=geo.world_to_cell(request.goal.pose.position.x,request.goal.pose.position.y)
            begin=time.perf_counter()
            try:
                path,expanded,objective=search(grid,start,goal,risk,self.risk_weight)
                if path is not None and not validate_path(grid,path,start,goal):
                    raise RuntimeError("C03 invalid grid path")
            except (ValueError,AssertionError,RuntimeError) as e:
                self.get_logger().error(str(e))
                return response
            elapsed=(time.perf_counter()-begin)*1000
            plan=RosPath()
            plan.header=msg.header
            if path:
                for point in path:
                    world=geo.cell_to_world(*point)
                    pose=PoseStamped()
                    pose.header=msg.header
                    pose.pose.position.x=float(world[0])
                    pose.pose.position.y=float(world[1])
                    pose.pose.orientation.w=1.
                    plan.poses.append(pose)
            response.plan=plan
            self.plan_pub.publish(plan)
            diag=dict(planner="C03_additive_proximity_risk_Astar",risk_weight=self.risk_weight,
                      expanded_nodes=expanded,objective=objective if math.isfinite(objective) else None,
                      path_found=bool(path),path_steps=len(path)-1 if path else None,
                      elapsed_ms=elapsed,
                      cvar_is_optimization_objective=False,
                      physical_robot_movement=False,
                      physical_robot_trials=0)
            diagnostic=String()
            diagnostic.data=json.dumps(diag,sort_keys=True)
            self.diagnostics_pub.publish(diagnostic)
            return response

    rclpy.init()
    node=None
    try:
        node=RiskPlanService()
        rclpy.spin(node)
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()

if __name__=="__main__":
    main()
