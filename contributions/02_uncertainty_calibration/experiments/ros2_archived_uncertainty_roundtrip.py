"""ROS2 Jazzy C02 held-out calibration stream roundtrip (non-actuating).

Actual serialized /c02/archived_grid_calibration Float64MultiArray ROS2
messages from generated grid-world records; NOT real robot sensor messages,
not physical localization ground truth, and NOT a robot control experiment.
"""
from __future__ import annotations
import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

DIR=Path(__file__).resolve().parent
sys.path.insert(0,str(DIR))
from eval_archived_instance_holdout import load_archive
from eval_three_way_group_coverage import grouped_partition,finite_sample_quantile

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,default=DIR.parent/"results"/"uncertainty_error_data.csv")
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--observations",type=int,default=120)
    args=parser.parse_args()
    if not 10<=args.observations<=2000:
        parser.error("--observations must be between 10 and 2000")

    import rclpy
    from rclpy.node import Node
    from rclpy.executors import SingleThreadedExecutor
    from std_msgs.msg import Float64MultiArray

    groups,pred,target,sigma=load_archive(args.input)
    (fit_mask,cal_mask,test_mask),group_ids=grouped_partition(groups,2026)
    score=np.abs(pred[cal_mask]-target[cal_mask])/sigma[cal_mask]
    q=finite_sample_quantile(score,.1)
    indices=np.flatnonzero(test_mask)[:args.observations]
    if len(indices)!=args.observations or not math.isfinite(q):
        raise RuntimeError("Insufficient heldout data or finite calibration threshold")
    records=[(float(pred[k]),float(target[k]),float(sigma[k]),float(q*sigma[k])) for k in indices]

    rclpy.init()
    producer=Node("c02_archived_uncertainty_producer")
    consumer=Node("c02_archived_uncertainty_subscriber")
    sent=[0]
    received=[]
    pub=producer.create_publisher(Float64MultiArray,"/c02/archived_grid_calibration",10)

    def callback(message):
        if len(message.data)!=4 or not all(math.isfinite(v) for v in message.data):
            raise ValueError("Unexpected uncertainty observation")
        received.append([float(x) for x in message.data])
    subscription=consumer.create_subscription(Float64MultiArray,"/c02/archived_grid_calibration",callback,10)

    def tick():
        if sent[0]<len(records):
            msg=Float64MultiArray()
            msg.data=list(records[sent[0]])
            pub.publish(msg)
            sent[0]+=1
    timer=producer.create_timer(.025,tick)
    executor=SingleThreadedExecutor()
    executor.add_node(consumer)
    executor.add_node(producer)
    start=time.monotonic()
    try:
        while len(received)<len(records) and time.monotonic()-start<35:
            executor.spin_once(timeout_sec=.05)
        if len(received)!=len(records):
            raise RuntimeError(f"ROS2 DDS delivery incomplete: {len(received)}/{len(records)}")
        if not np.allclose(np.array(records),np.array(received),atol=1e-12,rtol=0):
            raise AssertionError("Serialized received ROS2 values differ from source")
        arr=np.asarray(received)
        actual=float(np.mean(np.abs(arr[:,0]-arr[:,1])<=arr[:,3]))
        report=dict(
            evidence_type="REAL_ROS2_MIDDLEWARE_WITH_ARCHIVED_GENERATED_GRID_DATA",
            ros2_subscription_success=True,
            ros2_messages_sent=sent[0],
            ros2_messages_received=len(received),
            dataset="generated_gridworld_archive_not_physical_dingo",
            heldout_map_ids=group_ids[2],
            calibration_threshold=q,
            heldout_replayed_state_coverage=actual,
            physical_sensor_ground_truth=False,
            physical_robot_movement=False,
            physical_robot_trials=0,
            actuation_topic_published=False,
            time_seconds=time.monotonic()-start)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        print(json.dumps(report,indent=2,sort_keys=True))
        return 0
    finally:
        executor.remove_node(producer)
        executor.remove_node(consumer)
        producer.destroy_node()
        consumer.destroy_node()
        executor.shutdown()
        rclpy.shutdown()

if __name__=="__main__":
    raise SystemExit(main())
