"""Actual ROS 2 C05 live-message finite state machine roundtrip.

Produces only synthetic scalar risk observations and checks separately
subscribed C05 mode diagnostics. This is not physical robot operation.
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
    args=parser.parse_args()
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import Float64,String
    sequence=[.2,.75,.75,.98,.2,.2,.2,.2,.2,.2,float("nan")]
    expected=[
        "NORMAL","NORMAL","SAFE_MODE","EMERGENCY_STOP",
        "EMERGENCY_STOP","EMERGENCY_STOP","SAFE_MODE",
        "SAFE_MODE","SAFE_MODE","NORMAL","EMERGENCY_STOP",
    ]
    rclpy.init()
    node=Node("c05_actual_ros2_mode_test")
    pub=node.create_publisher(Float64,"/c05/risk_proxy",10)
    responses=[]
    sub=node.create_subscription(String,"/c05/mode_diagnostics",
                                 lambda m:responses.append(json.loads(m.data)),10)
    try:
        deadline=time.monotonic()+15
        while (pub.get_subscription_count()==0 or node.count_publishers("/c05/mode_diagnostics")==0) and time.monotonic()<deadline:
            rclpy.spin_once(node,timeout_sec=.1)
        if pub.get_subscription_count()==0:
            raise RuntimeError("C05 ROS2 supervisor is not receiving risk")
        for index,risk in enumerate(sequence):
            m=Float64();m.data=risk
            pub.publish(m)
            deadline=time.monotonic()+7
            while len(responses)<=index and time.monotonic()<deadline:
                rclpy.spin_once(node,timeout_sec=.05)
            if len(responses)<=index:
                raise RuntimeError(f"C05 mode response missing for input index {index}")
            state=responses[index]["state"]
            if state!=expected[index]:
                raise AssertionError(f"Incorrect C05 state step={index}: got {state}, expected {expected[index]}")
        assert all(not x["actuation_commanded"] and x["physical_robot_trials"]==0 for x in responses)
        result=dict(evidence="actual_ros2_pubsub_with_synthetic_scalar_risk_sequence",
                    messages_sent=len(sequence),messages_received=len(responses),
                    expected_states=expected,actual_states=[x["state"] for x in responses],
                    final_speed_scale=responses[-1]["speed_scale"],
                    emergency_stop_on_nan=responses[-1]["emergency_stop"],
                    physical_robot_trials=0,robot_movement=False)
        assert result["emergency_stop_on_nan"] and result["final_speed_scale"]==0
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        print(json.dumps(result,indent=2,sort_keys=True))
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__=="__main__":
    main()
