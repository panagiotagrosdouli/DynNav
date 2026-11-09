"""Actual ROS2 C04 GetPlan software service roundtrip; no motor commands."""
from __future__ import annotations
import argparse,json,time
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--tau",type=float,required=True)
    p.add_argument("--expect-mode",choices=["NORMAL","SAFE_RELAX_TAU","SAFE_STOP"],required=True)
    args=p.parse_args()
    import rclpy
    from rclpy.node import Node
    from nav_msgs.msg import OccupancyGrid
    from nav_msgs.srv import GetPlan
    from std_msgs.msg import String
    rclpy.init()
    node=Node("c04_returnability_ros2_client")
    pub=node.create_publisher(OccupancyGrid,"/c04/test_grid",10)
    client=node.create_client(GetPlan,"/c04/get_plan")
    received=[]
    sub=node.create_subscription(String,"/c04/diagnostics",lambda m:received.append(json.loads(m.data)),10)
    try:
        deadline=time.monotonic()+15
        while not client.wait_for_service(timeout_sec=.25):
            if time.monotonic()>deadline:
                raise RuntimeError("C04 real ROS2 service is unavailable")
        mapmsg=OccupancyGrid()
        mapmsg.header.frame_id="map"
        mapmsg.info.width=12
        mapmsg.info.height=12
        mapmsg.info.resolution=.25
        mapmsg.info.origin.orientation.w=1.
        values=[0]*144
        for y in range(12):
            if y!=6: values[y*12+6]=100
        mapmsg.data=values
        req=GetPlan.Request()
        req.start.header.frame_id="map";req.goal.header.frame_id="map"
        req.start.pose.position.x=.375;req.start.pose.position.y=.375
        req.goal.pose.position.x=2.625;req.goal.pose.position.y=2.625
        req.start.pose.orientation.w=1.;req.goal.pose.orientation.w=1.
        for _ in range(6):
            pub.publish(mapmsg)
            rclpy.spin_once(node,timeout_sec=.08)
        fut=client.call_async(req)
        deadline=time.monotonic()+25
        while not fut.done() and time.monotonic()<deadline:
            pub.publish(mapmsg)
            rclpy.spin_once(node,timeout_sec=.05)
        if not fut.done() or fut.result() is None:
            raise RuntimeError("C04 ROS2 service failed to respond")
        for _ in range(15):
            if received: break
            rclpy.spin_once(node,timeout_sec=.08)
        if not received:
            raise RuntimeError("C04 missing diagnostics")
        diag=received[-1]
        if diag["mode"]!=args.expect_mode or abs(diag["tau_requested"]-args.tau)>1e-9:
            raise AssertionError(diag)
        if diag["physical_robot_trials"] or diag["physical_robot_movement"]:
            raise AssertionError("Untrue C04 hardware evidence")
        result=fut.result()
        valid=args.expect_mode!="SAFE_STOP"
        assert (len(result.plan.poses)>1)==valid
        report=dict(evidence="actual_ros2_getplan_with_synthetic_grid_and_c04_returnability",
                    message_delivery=True,diagnostics=diag,
                    path_poses=len(result.plan.poses),
                    physical_robot_trials=0)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        print(json.dumps(report,indent=2,sort_keys=True))
    finally:
        node.destroy_node()
        rclpy.shutdown()
if __name__=="__main__":
    main()
