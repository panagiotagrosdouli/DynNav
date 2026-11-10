"""C15 time-aligned DVS simulator versus frame baseline without clock bias.

Both detectors receive the SAME generated input frames on the SAME timestamp
grid. The DVS simulator reconstructs pseudo-events from these frames; this
cannot establish the latency of a physical event camera, a trained SNN, or
real robot obstacle sensing.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
HERE=Path(__file__).resolve().parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0,str(HERE))
from neuromorphic_benchmark import (
    moving_obstacle_frames,evaluate_event_detector,evaluate_frame_baseline
)

def paired_scenario(speed,dt_us,n_frames):
    if dt_us<=0 or n_frames<3 or speed<1:
        raise ValueError("Invalid time grid or speed")
    frames=moving_obstacle_frames(n_frames=n_frames,speed_px_per_frame=speed)
    measured=[]
    for method,output in (
        ("frame_baseline",evaluate_frame_baseline(frames,dt_us=dt_us)),
        ("simulated_DVS_SNN",evaluate_event_detector(frames,dt_us=dt_us)),
    ):
        row=dict(method=method,obstacle_speed_px_per_frame=speed,
                 physical_camera=False,physical_robot=False,
                 n_frames=n_frames,frame_period_us=dt_us,
                 first_detection_time_us=output.detection_time_us,
                 observation_horizon_us=n_frames*dt_us,
                 detected=output.detected,
                 false_negative=output.false_negative,
                 generated_events=output.n_events,
                 max_score=output.max_score,
                 claim_scope="simulated_events_from_same_frames")
        measured.append(row)
    return measured

def run(output,intervals=(10000,33333),speeds=(3,6,10),n_frames=8):
    rows=[]
    for dt in intervals:
        for speed in speeds:
            rows.extend(paired_scenario(speed,dt,n_frames))
    output.mkdir(parents=True,exist_ok=True)
    with (output/"paired_trials.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    pairs=[]
    for i in range(0,len(rows),2):
        a,b=rows[i:i+2]
        assert a["method"]=="frame_baseline" and b["method"]=="simulated_DVS_SNN"
        assert a["frame_period_us"]==b["frame_period_us"]
        pairs.append(dict(speed=a["obstacle_speed_px_per_frame"],period_us=a["frame_period_us"],
                          frame_detected=a["detected"],event_detected=b["detected"],
                          both_detected=a["detected"] and b["detected"],
                          event_minus_frame_detection_us=(b["first_detection_time_us"]-a["first_detection_time_us"] if a["detected"] and b["detected"] else None)))
    report=dict(experiment="C15 time-matched simulated-event vs frame-threshold baseline",
                generated_frames=True,actual_event_camera=False,
                actual_neuromorphic_hardware=False,real_robot_trials=0,
                n_paired_scenarios=len(pairs),pairs=pairs,
                scientific_limitations=[
                    "Both methods share identical finite-rate frame input, not independently timed asynchronous camera events",
                    "The event detector uses an untrained randomly initialized SNN-style weight matrix",
                    "Frame baseline checks bright occupancy and sees an obstacle on the initial input frame",
                    "Input-cadence equality removes an artificial benchmark timing advantage; detector inference time and physical sensing latency remain unmeasured",
                    "No physical robot actuation, event-camera ground truth or real obstacle detection claim"
                ])
    (output/"summary.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2,sort_keys=True))
    return report

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir",type=Path,required=True)
    args=parser.parse_args()
    run(args.output_dir)
if __name__=="__main__":
    main()
