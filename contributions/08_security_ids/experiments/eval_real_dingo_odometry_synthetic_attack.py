"""C08 IDS on authentic recorded Dingo odometry + OFFLINE injected spoofing.

Source odometry is genuine physically recorded ROS1 bag evidence.
The spoofed case is synthetic and created only in memory: NO robot, ROS2 TF,
real cybersecurity incident or network was attacked. No alarm is labeled
a true original attack without independent ground truth.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
import numpy as np

CODE=Path(__file__).resolve().parents[1]/"code"
if str(CODE) not in sys.path:
    sys.path.insert(0,str(CODE))
from cusum_detector import CUSUMConfig,CUSUMDetector

def read_recorded_odometry(bag):
    from rosbags.highlevel import AnyReader
    with AnyReader([bag]) as reader:
        conns=sorted([c for c in reader.connections if "Odometry" in c.msgtype],key=lambda c:c.topic)
        if not conns:
            raise ValueError("No genuine nav_msgs/Odometry in source bag")
        chosen=conns[0]
        data=[]
        for conn,stamp,raw in reader.messages(connections=[chosen]):
            msg=reader.deserialize(raw,conn.msgtype)
            point=msg.pose.pose.position
            t=stamp*1e-9
            if not all(math.isfinite(v) for v in (t,point.x,point.y)):
                continue
            data.append((t,float(point.x),float(point.y)))
    if len(data)<120:
        raise ValueError("Insufficient genuine physical odometry observations")
    a=np.asarray(data,dtype=float)
    return chosen.topic,a

def velocity_samples(odom,max_dt=2.0,max_step=2.0):
    if odom.ndim!=2 or odom.shape[1]!=3:
        raise ValueError("Expected time,x,y")
    dt=np.diff(odom[:,0])
    steps=np.linalg.norm(np.diff(odom[:,1:3],axis=0),axis=1)
    valid=np.isfinite(dt)&np.isfinite(steps)&(dt>0)&(dt<=max_dt)&(steps<=max_step)
    if np.sum(valid)<100:
        raise ValueError("Insufficient finite, monotonic valid odometry increments")
    return odom[1:,0][valid],steps[valid]/dt[valid],int((~valid).sum())

def fit_config(train,sensitivity=8.0):
    if len(train)<30 or sensitivity<=0:
        raise ValueError("Need independent baseline train sample and positive sensitivity")
    midpoint=float(np.median(train))
    scale=float(1.4826*np.median(np.abs(train-midpoint)))
    scale=max(scale,0.03)
    z=(train-midpoint)/scale
    # Positive speed deviations only; training baseline CUSUM threshold
    # is based exclusively on predeclared no-attack fit, never on the test.
    k=max(0.5,float(np.median(np.abs(z))))
    probe=CUSUMDetector(CUSUMConfig(k=k,h=1.0))
    max_stat=0.
    for v in z:
        probe.update(float(v))
        max_stat=max(max_stat,probe.state.S_pos,probe.state.S_neg)
    threshold=max(6.0,float(max_stat)*sensitivity)
    return midpoint,scale,CUSUMConfig(k=k,h=threshold)

def alarm_indices(samples,mid,scale,config):
    d=CUSUMDetector(config)
    indices=[]
    for i,value in enumerate(samples):
        alarm=d.update(float((value-mid)/scale))
        if alarm:
            indices.append(i)
    return indices,d.state.n_alarms

def evaluate_odometry(odom,seed=13,attack_speed_m_s=.35,attack_fraction=.5):
    if not 0<attack_fraction<1 or not math.isfinite(attack_speed_m_s) or attack_speed_m_s<=0:
        raise ValueError("Need positive artificial attack and a valid after-baseline onset")
    t,speed,rejected=velocity_samples(odom)
    if len(speed)<150:
        raise ValueError("Too few independent observations")
    # Time partition: fit on FIRST 45%; evaluate on disjoint final 55%.
    nfit=int(.45*len(speed))
    train,test=speed[:nfit],speed[nfit:]
    midpoint,scale,cfg=fit_config(train)
    onset=int(len(test)*attack_fraction)
    no_attack_alarm,_=alarm_indices(test,midpoint,scale,cfg)
    # Inject only into a COPY of heldout speed observations. Synthetic
    # positive velocity bias is not a real attack on a physical robot.
    injected=np.array(test,copy=True)
    injected[onset:]+=attack_speed_m_s
    modified_alarm,_=alarm_indices(injected,midpoint,scale,cfg)
    first_post=next((idx for idx in modified_alarm if idx>=onset),None)
    return {
        "actual_dingo_odom_samples":int(len(odom)),
        "valid_velocity_observations":int(len(speed)),
        "rejected_velocity_steps":rejected,
        "baseline_fit_samples":int(len(train)),
        "heldout_test_samples":int(len(test)),
        "injected_attack_start_index":onset,
        "artificial_speed_bias_m_per_s":attack_speed_m_s,
        "baseline_median_speed_m_per_s":midpoint,
        "baseline_robust_speed_scale_m_per_s":scale,
        "cusum_k":cfg.k,"cusum_threshold":cfg.h,
        "unmodified_recording_heldout_alarm_samples":len(no_attack_alarm),
        "injected_recording_pre_attack_alarm_samples":sum(i<onset for i in modified_alarm),
        "injected_first_alarm_post_onset_index":first_post,
        "injected_detection_delay_samples":None if first_post is None else first_post-onset,
        "injected_detected_post_onset":first_post is not None,
        "no_attack_ground_truth_assumed":False,
        "anomalies_in_original_recording_have_unknown_cause":True,
        "real_telemetry_base":True,
        "attack_is_synthetic_in_memory":True,
        "physical_robot_c08_control":False,
        "physical_robot_trials":0,
        "claim_boundary":"Real recorded Dingo odometry is an offline signal; artificial speed-bias injection is a counterfactual. No verified real attack, sensor ground truth, ROS2 IDS deployment or physical safety response."
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("bag",type=Path)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--attack-speed",type=float,default=.35)
    a=p.parse_args()
    source=a.bag.resolve()
    topic,data=read_recorded_odometry(source)
    result=evaluate_odometry(data,attack_speed_m_s=a.attack_speed)
    result.update(source_bag_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  source_bag_bytes=source.stat().st_size,
                  source_odometry_topic=topic,
                  evidence_type="RECORDED_DINGO_ODOMETRY_OFFLINE_WITH_SYNTHETIC_INJECTION")
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=="__main__":
    main()
