"""C08 controlled sensitivity sweep on genuine recorded odometry, synthetic biases.

Reuses the SAME archived real Dingo source with fixed chronological no-leak
training split. Any fake speed perturbation is injected only into in-memory
heldout streams; NEVER sent to actual ROS2 TF, robot or communications.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path
from eval_real_dingo_odometry_synthetic_attack import read_recorded_odometry,evaluate_odometry

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("bag",type=Path)
    p.add_argument("--output-dir",required=True,type=Path)
    p.add_argument("--biases",nargs="+",type=float,default=[0.1,0.2,0.35,0.5,1.0])
    a=p.parse_args()
    bag=a.bag.resolve()
    topic,odom=read_recorded_odometry(bag)
    sha=hashlib.sha256(bag.read_bytes()).hexdigest()
    rows=[]
    for bias in a.biases:
        trial=evaluate_odometry(odom,attack_speed_m_s=bias)
        record=dict(artificial_bias_m_per_s=bias,
                    real_unmodified_heldout_alarm_samples=trial["unmodified_recording_heldout_alarm_samples"],
                    pre_onset_alarm_samples=trial["injected_recording_pre_attack_alarm_samples"],
                    first_detected_post_onset=trial["injected_detected_post_onset"],
                    detection_delay_samples=trial["injected_detection_delay_samples"],
                    heldout_samples=trial["heldout_test_samples"],
                    onset_index=trial["injected_attack_start_index"],
                    threshold=trial["cusum_threshold"])
        rows.append(record)
    outdir=a.output_dir
    outdir.mkdir(parents=True,exist_ok=True)
    with (outdir/"sensitivity.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary={"source_bag_sha256":sha,"source_topic":topic,
             "observed_odometry_samples":int(len(odom)),
             "evidence":"genuine_historical_dingo_odometry_plus_synthetic_counterfactual_in_memory_bias",
             "biases_tested":a.biases,
             "trials":rows,
             "original_attack_truth_labeled":False,
             "ros2_live_detector_deployed":False,
             "physical_robot_trials":0,
             "warning":"CUSUM threshold is fit on one original early segment; an alarm on later recorded data has no independent confirmed cyber-attack label. Detection delays are in samples, not physical intervention times."}
    (outdir/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print(json.dumps(summary,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
