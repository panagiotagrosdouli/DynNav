"""C06 observed real Dingo odometry distance and strictly unverified resources.

The input is genuine physically recorded ROS1 nav_msgs/Odometry, but the
original physical Dingo was NEVER controlled by C06. No genuine battery
current, battery voltage or radio RSSI is inferred from odometry.
"""
from __future__ import annotations
import argparse,hashlib,json,math
from pathlib import Path

def integrate_deltas(samples,max_step_m=2.0):
    if not math.isfinite(max_step_m) or max_step_m<=0:
        raise ValueError("max_step_m must be finite and positive")
    accepted=0;rejected=0;distance=0.;prev=None;first_t=None;last_t=None
    for t,x,y in samples:
        if not all(map(math.isfinite,(t,x,y))):
            rejected+=1;continue
        if first_t is None:first_t=t
        last_t=t
        if prev is None:
            prev=(t,x,y);continue
        dt=t-prev[0]
        step=math.hypot(x-prev[1],y-prev[2])
        if dt<=0 or step>max_step_m:
            rejected+=1
            prev=(t,x,y)
            continue
        distance+=step
        accepted+=1
        prev=(t,x,y)
    if accepted==0:
        raise ValueError("No valid consecutive odometry translations")
    return dict(accepted_steps=accepted,rejected_steps=rejected,
                observed_planar_odometry_distance_m=float(distance),
                recorded_first_time_s=first_t,recorded_last_time_s=last_t,
                recorded_span_s=float(last_t-first_t))

def analyze(path,max_step_m=2.0,energy_per_meter_j=20.,battery_budget_j=1000.,reserve_j=150.):
    from rosbags.highlevel import AnyReader
    if not path.is_file():
        raise FileNotFoundError(path)
    values=(energy_per_meter_j,battery_budget_j,reserve_j)
    if not all(math.isfinite(v) and v>=0 for v in values) or battery_budget_j<reserve_j:
        raise ValueError("Energy proxy parameters must be finite, nonnegative with budget >= reserve")
    sha=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            sha.update(block)
    with AnyReader([path]) as reader:
        connections=[c for c in reader.connections if "Odometry" in c.msgtype]
        if not connections:
            raise ValueError("Actual Dingo recording has no Odometry messages")
        # Audit one unambiguous stream. Do not mix distinct frame origins.
        chosen=sorted(connections,key=lambda c:c.topic)[0]
        def records():
            for conn,stamp,raw in reader.messages(connections=[chosen]):
                msg=reader.deserialize(raw,conn.msgtype)
                pose=msg.pose.pose.position
                yield stamp*1e-9,float(pose.x),float(pose.y)
        metrics=integrate_deltas(records(),max_step_m)
    estimated_j=metrics["observed_planar_odometry_distance_m"]*energy_per_meter_j
    proxy_margin=battery_budget_j-reserve_j-estimated_j
    return dict(
        evidence="PHYSICAL_DINGO_RECORDED_ODOMETRY_OFFLINE_RESOURCE_PROXY",
        bag_sha256=sha.hexdigest(),bag_bytes=path.stat().st_size,
        odometry_topic=chosen.topic,**metrics,
        assumed_energy_per_meter_j=energy_per_meter_j,
        assumed_battery_budget_j=battery_budget_j,
        assumed_reserve_j=reserve_j,
        modeled_energy_j=estimated_j,
        modeled_reserve_margin_j=proxy_margin,
        energy_measurement_real=False,
        no_battery_voltage_or_current_ground_truth=True,
        real_link_quality_observed=False,
        real_radio_RSSI_observed=False,
        mission_decision="BLOCKED_NO_PHYSICAL_BATTERY_OR_LINK_MEASUREMENT",
        c06_controlled_original_robot=False,
        physical_robot_trials=0,
        warning="Real odometry traveled path; modeled Joules are UNCALIBRATED. No connectivity estimate can be recovered from missing RSSI/SNR. No physical C06 safety/energy claim."
    )

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("bag",type=Path)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--max-step-m",type=float,default=2.0)
    p.add_argument("--joules-per-meter",type=float,default=20.)
    p.add_argument("--battery-budget-j",type=float,default=1000.)
    p.add_argument("--reserve-j",type=float,default=150.)
    a=p.parse_args()
    report=analyze(a.bag.resolve(),a.max_step_m,a.joules_per_meter,a.battery_budget_j,a.reserve_j)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2,sort_keys=True))
if __name__=="__main__":
    main()
