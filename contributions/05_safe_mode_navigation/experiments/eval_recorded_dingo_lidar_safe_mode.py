"""C05 on ACTUAL prerecorded Dingo LaserScan observations (ROS1 bag).

Extract a transparent lower-decile valid beam range (meters) and map it to
an explicit scalar proximity proxy. Feed the *real observed sequence* through
C05 safe-mode logic. No physical robot was controlled by C05 and no collision
risk probabilities are calibrated or measured.

This experiment must never be described as a real physical C05 trial.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,sys
from pathlib import Path
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"code"))
from safe_mode_controller import SafeModeController,summarize_outputs

def proximity_proxy(ranges,range_min,range_max):
    valid=np.asarray(ranges,dtype=float)
    valid=valid[np.isfinite(valid) & (valid>=range_min) & (valid<=range_max)]
    if not len(valid):
        return 1.0,None
    q10=float(np.quantile(valid,.1))
    risk=float(np.clip((2.-q10)/1.5,0.,1.))
    return risk,q10

def evaluate(path,max_scans=500,stride=10):
    from rosbags.highlevel import AnyReader
    if max_scans<1 or stride<1:
        raise ValueError("max_scans/stride must be positive")
    if not path.is_file():
        raise FileNotFoundError(path)
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):
            h.update(block)
    controller=SafeModeController()
    rows=[];output=[];topics=set();all_scans=0;first=None;last=None
    with AnyReader([path]) as reader:
        connections=[conn for conn in reader.connections if "LaserScan" in conn.msgtype]
        if not connections:
            raise ValueError("No real LaserScan source in original bag")
        for conn,stamp,raw in reader.messages(connections=connections):
            all_scans+=1
            if (all_scans-1)%stride:
                continue
            msg=reader.deserialize(raw,conn.msgtype)
            risk,q10=proximity_proxy(msg.ranges,float(msg.range_min),float(msg.range_max))
            result=controller.update(risk)
            time_s=stamp*1e-9
            first=time_s if first is None else first
            last=time_s
            topics.add(conn.topic)
            rows.append(dict(scan_index=all_scans,recorded_time_s=time_s,topic=conn.topic,
                             lidar_p10_valid_m=q10,risk_proxy=risk,state=result.state.value,
                             speed_scale=result.speed_scale,should_replan=result.should_replan,
                             transition=result.transition,emergency_stop=result.emergency_stop))
            output.append(result)
            if len(rows)>=max_scans:
                break
    if not output:
        raise ValueError("No valid recorded scan decoded")
    return rows,dict(
        evidence="PRERECORDED_PHYSICAL_ROBOT_LIDAR_OFFLINE_C05_ALGORITHM_REPLAY",
        bag_sha256=h.hexdigest(),source_bag_size_bytes=path.stat().st_size,
        topic_names=sorted(topics),scans_read=all_scans,scans_evaluated=len(rows),
        recorded_time_first_s=first,recorded_time_last_s=last,
        risk_definition="clip((2.0m - 10th_percentile_valid_scan_range_m) / 1.5m, 0,1); empty valid scans => critical",
        proxy_not_probability=True,
        baseline_speed_scale=1.0,
        c05_safety_statistics=summarize_outputs(output),
        invalid_laser_frames=sum(v["lidar_p10_valid_m"] is None for v in rows),
        physical_robot_executed_c05=False,physical_robot_trials=0,
        ros2_actuation_executed=False,
        claim_boundary="Genuine physical Dingo recordings consumed offline. No original robot action was affected, no independent obstacle/collision ground truth and no physical C05 controller trial.",
    )

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("bag",type=Path)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--max-scans",type=int,default=500)
    p.add_argument("--stride",type=int,default=10)
    a=p.parse_args()
    rows,report=evaluate(a.bag.resolve(),a.max_scans,a.stride)
    a.output_dir.mkdir(parents=True,exist_ok=True)
    with (a.output_dir/"recorded_lidar_state_transitions.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    (a.output_dir/"summary.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,sort_keys=True))
if __name__=="__main__":
    main()
