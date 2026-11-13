"""C18 *actual ROS2 DDS* isolated point-velocity gate.

Twist.linear.x/y are two planar point-model velocity coordinates. This is NOT
a differential-drive robot command or actuator interface. Only under
/c18/isolated_sim/*, no /cmd_vel publisher, no physical robot motion.
"""
from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

C18=Path(__file__).resolve().parents[1]
if str(C18) not in sys.path:
    sys.path.insert(0,str(C18))
from formal_safety_shields import CBFConfig,CBFSafetyFilter

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scenario",choices=("feasible","infeasible"),required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()

    import rclpy
    from rclpy.node import Node
    from geometry_msgs.msg import Twist
    from std_msgs.msg import String

    rclpy.init()
    producer=Node("c18_isolated_point_velocity_test_producer")
    gate=Node("c18_isolated_cbf_velocity_gate")
    receiver=Node("c18_isolated_point_velocity_test_subscriber")
    request_topic="/c18/isolated_sim/requested_point_velocity"
    filtered_topic="/c18/isolated_sim/filtered_point_velocity"
    diag_topic="/c18/isolated_sim/constraint_diagnostics"
    request_pub=producer.create_publisher(Twist,request_topic,10)
    filtered_pub=gate.create_publisher(Twist,filtered_topic,10)
    diag_pub=gate.create_publisher(String,diag_topic,10)
    results=[]
    diagnostics=[]
    filter=CBFSafetyFilter(CBFConfig(safety_radius=.4,alpha=1.5))
    pos=np.zeros(2)
    obstacles=([np.array([1.,0.])] if a.scenario=="feasible" else
               [np.array([.1,0.]),np.array([-.1,0.])])
    def handle(message):
        desired=np.array([message.linear.x,message.linear.y],dtype=float)
        command,report=filter.batch_filter(desired,pos,obstacles)
        outgoing=Twist()
        outgoing.linear.x=float(command[0])
        outgoing.linear.y=float(command[1])
        filtered_pub.publish(outgoing)
        d=String()
        d.data=json.dumps(report,sort_keys=True)
        diag_pub.publish(d)
    req_sub=gate.create_subscription(Twist,request_topic,handle,10)
    result_sub=receiver.create_subscription(
        Twist,filtered_topic,lambda v:results.append((float(v.linear.x),float(v.linear.y))),10)
    diag_sub=receiver.create_subscription(
        String,diag_topic,lambda v:diagnostics.append(json.loads(v.data)),10)
    executor=rclpy.executors.SingleThreadedExecutor()
    for node in (producer,gate,receiver):
        executor.add_node(node)
    try:
        started=time.monotonic()
        last=0
        while time.monotonic()-started<12 and (not results or not diagnostics):
            now=time.monotonic()
            if (now-last)>.15 and request_pub.get_subscription_count()>0:
                req=Twist();req.linear.x=2.0;req.linear.y=0.0
                request_pub.publish(req)
                last=now
            executor.spin_once(timeout_sec=.04)
        if not results or not diagnostics:
            raise RuntimeError("C18 true ROS2 DDS request/filtered command/diagnostic roundtrip timed out")
        command=np.asarray(results[-1])
        status=diagnostics[-1]
        expected_feasible=a.scenario=="feasible"
        if bool(status["constraint_feasible"])!=expected_feasible:
            raise AssertionError("ROS2 CBF feasibility result inconsistent with ground-truth fixture")
        if expected_feasible:
            if abs(command[0]-.9)>1e-5 or status["minimum_cbf_margin"]<-1e-7:
                raise AssertionError("Actual ROS2 filtered point velocity violates CBF")
        elif not np.array_equal(command,np.zeros(2)):
            raise AssertionError("Infeasible CBF must emit zero with explicit NOT CERTIFIED status")
        report={
            "evidence":"GENUINE_ROS2_JAZZY_DDS_ISOLATED_SYNTHETIC_POINT_VELOCITY",
            "scenario":a.scenario,
            "request_topic":request_topic,
            "output_topic":filtered_topic,
            "actual_ros2_filtered_velocity":command.tolist(),
            "cbf_diagnostics":status,
            "physical_robot_commands":0,
            "actual_navigation_or_actuator_test":False,
            "physical_safety_certified":False,
        }
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print(json.dumps(report,indent=2,sort_keys=True))
        return 0
    finally:
        for node in (producer,gate,receiver):
            executor.remove_node(node)
            node.destroy_node()
        executor.shutdown()
        rclpy.shutdown()

if __name__=="__main__":
    raise SystemExit(main())
