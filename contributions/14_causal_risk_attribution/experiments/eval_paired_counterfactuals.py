"""C14 paired counterfactual attribution with explicitly specified SCM repairs.

This is a HAND-SPECIFIED synthetic SCM, not learned physical causality.
Intervention scores compare the SAME exogenous noise realization before
and after do(X=x_ref), unlike unpaired Monte Carlo ablations. No robot
control or hardware intervention is performed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0,str(HERE))
from causal_risk import NavigationSCM

# This is an explicit research assumption, not inferred from physical data.
NEUTRAL={"sensor_noise":0.0,"localization_error":0.0,
         "map_accuracy":1.0,"obstacle_detection":1.0,"path_risk":0.0}
CAUSES=tuple(NEUTRAL)

def validate_episode(noise, scm):
    if not isinstance(noise,dict):
        raise ValueError("Observed exogenous noise must be a dictionary")
    for k,v in noise.items():
        if k not in scm.nodes or not isinstance(v,(int,float)) or not math.isfinite(v):
            raise ValueError("Unknown or nonfinite SCM noise observation")
    return {k:float(v) for k,v in noise.items()}

def paired_effects(scm,noise,outcome="collision",neutral=NEUTRAL):
    noise=validate_episode(noise,scm)
    if outcome not in scm.nodes:
        raise ValueError("Unknown outcome")
    if outcome in neutral:
        raise ValueError("Outcome cannot be offered as a cause")
    observed=scm.observational_query(noise)
    baseline=float(observed[outcome])
    scores={}
    for cause,reference in neutral.items():
        if cause not in scm.nodes or not math.isfinite(reference):
            raise ValueError("Invalid intervention specification")
        changed=scm.counterfactual_query(noise,{cause:reference})
        scores[cause]=baseline-float(changed[outcome])
    return observed,sorted(scores.items(),key=lambda item:(-item[1],item[0]))

def factorial_ground_truth(scm,seed,n_episodes=200,root=None):
    """Controlled episodes where ONE specified root exogenous shock is injected.

    The ground truth here is injection provenance, not independent physical
    causality. Negative improvements are left negative, never rectified.
    """
    if n_episodes<10:
        raise ValueError("Need >=10 episodes")
    rng=np.random.default_rng(seed)
    rows=[]
    candidates=tuple(root for root in CAUSES if root!="collision") if root is None else (root,)
    if not set(candidates).issubset(CAUSES):
        raise ValueError("Unknown injected root")
    for n in range(n_episodes):
        cause=candidates[n % len(candidates)]
        # Fixed noise realization as baseline plus a single controlled shock.
        noise={key:float(rng.normal(0,0.04)) for key in scm.nodes}
        noise[cause]+=float(rng.uniform(.9,1.6)) * (-1.0 if cause in ("map_accuracy","obstacle_detection") else 1.0)
        observed,ranking=paired_effects(scm,noise)
        rows.append({
            "episode":n,"injected_noise_node":cause,
            "rank_of_injected_cause":1+[k for k,_ in ranking].index(cause),
            "predicted_top_effect":ranking[0][0],
            "top1_matches_injection":ranking[0][0]==cause,
            "observed_outcome":float(observed["collision"]),
            "injected_node_effect":dict(ranking)[cause],
            "ranking":json.dumps(ranking),
        })
    return rows

def run(outdir,seed,episodes):
    outdir.mkdir(parents=True,exist_ok=True)
    scm=NavigationSCM()
    rows=factorial_ground_truth(scm,seed,episodes)
    with (outdir/"counterfactual_trials.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    per_cause={}
    for cause in CAUSES:
        sample=[r for r in rows if r["injected_noise_node"]==cause]
        per_cause[cause]={"n":len(sample),
                          "top1_accuracy":sum(r["top1_matches_injection"] for r in sample)/len(sample),
                          "mean_rank":float(np.mean([r["rank_of_injected_cause"] for r in sample])),
                          "mean_model_effect":float(np.mean([r["injected_node_effect"] for r in sample]))}
    report={"model":"hand_specified_navigation_SCM",
            "evidence_level":"synthetic_injected_noise_paired_structural_counterfactuals",
            "source_scm_sha256":hashlib.sha256((HERE/"causal_risk.py").read_bytes()).hexdigest(),
            "neutral_values":NEUTRAL,"n_episodes":len(rows),"seed":seed,
            "overall_top1_accuracy":sum(r["top1_matches_injection"] for r in rows)/len(rows),
            "per_cause":per_cause,
            "limitations":["Injected noise provenance is not identified causal ground truth from real robot failures",
                           "Counterfactuals depend entirely on manually selected equations and neutral reference values",
                           "No independent physical intervention, real robot collision probability or validated causal graph",
                           "These deterministic repaired effects are not Shapley values or a causal identifiability proof"],
            "physical_robot_trials":0}
    (outdir/"summary.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,sort_keys=True))
    return report

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir",type=Path,required=True)
    parser.add_argument("--seed",type=int,default=2026)
    parser.add_argument("--episodes",type=int,default=250)
    args=parser.parse_args()
    run(args.output_dir,args.seed,args.episodes)

if __name__=="__main__":
    main()
