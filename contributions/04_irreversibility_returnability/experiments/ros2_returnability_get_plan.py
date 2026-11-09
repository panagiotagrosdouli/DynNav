"""C04 actual ROS2 GetPlan with geometric returnability guardrail.

The trusted base is the REQUEST START coordinate. This implements a
STATIC, 4-connected geometric base-reachability / fragility proxy, NOT a
kinodynamic safety shield, dynamic return-home guarantee or Nav2 plugin.
The service never actuates /cmd_vel.
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

from ros2_grid_geometry import GridGeometry,grid_from_occupancy,quaternion_yaw
from eval_real_office_returnability import return_distances,geometric_fragility,minimum_feasible_tau,validate_path
from irreversibility_planner import astar_irreversibility_constrained

def main():
    import rclpy
    from rclpy.node import Node
    from nav_msgs.msg import OccupancyGrid, Path as RosPath
    from nav_msgs.srv import GetPlan
    from geometry_msgs.msg import PoseStamped
    from std_msgs.msg import String

    class ReturnabilityPlanService(Node):
        def __init__(self):
            super().__init__("c04_returnability_planning_only")
            self.declare_parameter("map_topic","/c04/map")
            self.declare_parameter("tau_requested",.08)
            self.declare_parameter("maximum_relaxation",1.0)
            self.declare_parameter("lethal_threshold",50)
            self.tau=float(self.get_parameter("tau_requested").value)
            self.max_gap=float(self.get_parameter("maximum_relaxation").value)
            if not (0<=self.tau<=1 and 0<=self.max_gap<=1):
                raise ValueError("C04 thresholds must lie in [0,1]")
            self.latest_map=None
            self.map_sub=self.create_subscription(OccupancyGrid,str(self.get_parameter("map_topic").value),self.on_map,10)
            self.server=self.create_service(GetPlan,"/c04/get_plan",self.on_plan)
            self.plan_pub=self.create_publisher(RosPath,"/c04/plan",10)
            self.diag_pub=self.create_publisher(String,"/c04/diagnostics",10)

        def on_map(self,msg):
            try:
                raw=grid_from_occupancy(msg.data,int(msg.info.width),int(msg.info.height),
                                        lethal_threshold=int(self.get_parameter("lethal_threshold").value))
            except (ValueError,AssertionError) as e:
                self.get_logger().error("Invalid C04 map: "+str(e))
                self.latest_map=None
                return
            self.latest_map=(msg,raw)

        def on_plan(self,request,response):
            if self.latest_map is None:
                self.get_logger().error("C04 map unavailable")
                return response
            msg,grid=self.latest_map
            if request.start.header.frame_id!=msg.header.frame_id or request.goal.header.frame_id!=msg.header.frame_id:
                self.get_logger().error("Frames differ; no implicit TF")
                return response
            origin=msg.info.origin
            try:
                yaw=quaternion_yaw(origin.orientation.x,origin.orientation.y,origin.orientation.z,origin.orientation.w)
                geom=GridGeometry(float(msg.info.resolution),float(origin.position.x),float(origin.position.y),yaw,msg.header.frame_id)
                base=geom.world_to_cell(request.start.pose.position.x,request.start.pose.position.y)
                goal=geom.world_to_cell(request.goal.pose.position.x,request.goal.pose.position.y)
                t0=time.perf_counter()
                dist=return_distances(grid==0,base)
                I,reach=geometric_fragility(grid,dist)
                minimal=minimum_feasible_tau(reach,I,base,goal)
                used=min(1.,minimal+1e-9)
                accepted=math.isfinite(minimal) and used-self.tau<=self.max_gap
                # Never silently relax over the caller-specified maximum.
                if accepted:
                    used=max(used,self.tau)
                    res=astar_irreversibility_constrained(reach,I,(base[1],base[0]),(goal[1],goal[0]),tau=used)
                    if not res.success:
                        raise RuntimeError("C04 returned infeasible path despite minimax threshold")
                    path=[(x,y) for y,x in res.path]
                    if not validate_path(grid,path,base,goal):
                        raise RuntimeError("C04 path failed geometric validation")
                else:
                    path=[]
                    res=None
            except (ValueError,AssertionError,RuntimeError) as exc:
                self.get_logger().error("C04 planning rejected: "+str(exc))
                return response

            plan=RosPath()
            plan.header=msg.header
            for x,y in path:
                wx,wy=geom.cell_to_world(x,y)
                pose=PoseStamped()
                pose.header=msg.header
                pose.pose.position.x=float(wx)
                pose.pose.position.y=float(wy)
                pose.pose.orientation.w=1.
                plan.poses.append(pose)
            response.plan=plan
            self.plan_pub.publish(plan)
            diag=dict(method="C04_static_base_returnability_minimax",
                      tau_requested=self.tau,
                      tau_minimum=float(minimal) if math.isfinite(minimal) else None,
                      tau_used=float(used) if accepted else None,
                      max_relaxation=self.max_gap,
                      mode=("NORMAL" if accepted and minimal<=self.tau else "SAFE_RELAX_TAU" if accepted else "SAFE_STOP"),
                      path_found=bool(path),path_steps=len(path)-1 if path else None,
                      expanded_nodes=res.expansions if res else 0,
                      elapsed_ms=(time.perf_counter()-t0)*1000,
                      physical_robot_movement=False,physical_robot_trials=0,
                      calibrated_risk_probability=False)
            d=String();d.data=json.dumps(diag,sort_keys=True)
            self.diag_pub.publish(d)
            return response

    rclpy.init()
    node=None
    try:
        node=ReturnabilityPlanService()
        rclpy.spin(node)
    finally:
        if node is not None: node.destroy_node()
        rclpy.shutdown()

if __name__=="__main__":
    main()
