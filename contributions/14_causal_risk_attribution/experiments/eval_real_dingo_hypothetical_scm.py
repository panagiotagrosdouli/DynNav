"""C14 inspect actual Dingo odometry changes with an explicitly assumed SCM.

A real odometry change in a historic bag is NOT a known sensor failure or
action-triggered hazard. Map physically observed speed-change magnitudes onto
one synthetic SCM exogenous proxy and compute model-based interventions.
NO causal identification, physical intervention, collision-probability
calibration, onboard C14 motion or controller action is claimed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from causal_risk import NavigationSCM

ODOM_TOPIC="/dingo_velocity_controller/odom"

def valid_motion_samples(path):
    from rosbags.highlevel import AnyReader
    samples=[]
    with AnyReader([path]) as reader:
        connections=[c for c in reader.connections if c.topic==ODOM_TOPIC and "Odometry" in c.msgtype]
        if len(connections)!=1:
            raise ValueError("Expected exactly one original physical Dingo odometry stream")
        for conn,stamp,raw in reader.messages(connections=connections):
            msg=reader.deserialize(raw,conn.msgtype)
            p=msg.pose.pose.position
            value=(stamp*1e-9,float(p.x),float(p.y))
            if all(math.isfinite(x) for x in value):
                samples.append(value)
    if len(samples)<300:
        raise ValueError("Insufficient genuinely recorded odometry")
    rates=[]
    for first,second in zip(samples,samples[1:]):
        dt=second[0]-first[0]
        if not .01<=dt<=.5:
            continue
        distance=math.hypot(second[1]-first[1],second[2]-first[2])
        if distance>.3:
            continue
        rates.append((second[0],distance/dt))
    if len(rates)<200:
        raise ValueError("Insufficient finite speed samples")
    return np.asarray(rates,dtype=np.float64),len(samples)

def diagnostic(path,output,n_examples=24):
    if n_examples<2:
        raise ValueError("At least two events required")
    rates,n_odom=valid_motion_samples(path)
    dv=np.diff(rates[:,1])
    times=rates[1:,0]
    split=len(dv)//2
    first=dv[:split]
    # Calibration of a descriptive magnitude on the FIRST half only;
    # absolute speed changes include intentional acceleration, NOT pure sensor noise.
    center=float(np.median(first))
    scale=max(1e-4,float(1.4826*np.median(np.abs(first-center))))
    observed=dv[split:]
    timestamps=times[split:]
    idx=np.argsort(np.abs(observed-center))[::-1][:n_examples]
    scm=NavigationSCM()
    records=[]
    for event in idx:
        t=float(timestamps[event])
        score=float(np.clip((observed[event]-center)/scale,-2.,2.))
        noise={"sensor_noise":score}
        baseline=scm.observational_query(noise)
        counter=scm.counterfactual_query(noise,{"sensor_noise":0.})
        ranked=scm.root_cause_ranking(noise,n_samples=30)
        records.append({"recorded_time_s":t,"observed_speed_change_m_per_s":float(observed[event]),
                        "normalized_speed_change_proxy":score,
                        "assumed_scm_factual_collision_index":float(baseline["collision"]),
                        "assumed_scm_do_sensor_noise_zero_collision_index":float(counter["collision"]),
                        "assumed_scm_counterfactual_difference":float(baseline["collision"]-counter["collision"]),
                        "top_scm_candidate":ranked[0][0]})
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""):
            h.update(chunk)
    report={
        "evidence":"ACTUAL_RECORDED_DINGO_ODOMETRY_WITH_HAND_SPECIFIED_SCM_COUNTERFACTUAL_PROXY",
        "source_bag_sha256":h.hexdigest(),
        "source_odometry_topic":ODOM_TOPIC,
        "observed_odometry_messages":n_odom,
        "finite_speed_steps":len(rates),
        "calibration_steps":split,
        "diagnostic_steps":len(observed),
        "selected_events":len(records),
        "measured_change_is_known_sensor_fault":False,
        "measured_change_is_known_causal_action_hazard":False,
        "collision_index_is_physical_probability":False,
        "scm_structure_learned_from_dingo":False,
        "genuine_physical_intervention_performed":False,
        "physical_robot_controlled_by_c14":False,
        "physical_robot_trials":0,
        "claim_boundary":"Real physical odometry source; synthetic causal equations and hypothetical intervention outputs. Observed acceleration is not identified localization error or actual collision.",
        "cases":records,
    }
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="cases"},indent=2))
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("real_dingo_ros1_bag",type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--examples",type=int,default=24)
    a=p.parse_args()
    diagnostic(a.real_dingo_ros1_bag.resolve(),a.out.resolve(),a.examples)
if __name__=="__main__":
    main()
