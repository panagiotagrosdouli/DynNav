"""C02 predeclared group-disjoint calibration, validation and blind test.

Archived data were generated in grid-worlds, NOT recorded physical robots.
The calibration scores treat within-map states as dependent; empirical state
coverage on held-out maps is reported, NOT a distribution-free group guarantee.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path
import numpy as np

THIS=Path(__file__).resolve().parent
sys.path.insert(0,str(THIS))
from eval_archived_instance_holdout import load_archive

def grouped_partition(groups, seed):
    ids=np.unique(groups)
    if len(ids)<5:
        raise ValueError("Need >=5 separate map instances for 3-way split")
    ids=np.random.default_rng(seed).permutation(ids)
    nfit=max(1,int(len(ids)*.5))
    ncal=max(1,int(len(ids)*.25))
    if nfit+ncal>=len(ids):
        raise ValueError("At least one untouched test group required")
    a,b,c=ids[:nfit],ids[nfit:nfit+ncal],ids[nfit+ncal:]
    assert not (set(a)&set(b) or set(a)&set(c) or set(b)&set(c))
    return (np.isin(groups,a),np.isin(groups,b),np.isin(groups,c)), (a.tolist(),b.tolist(),c.tolist())

def finite_sample_quantile(scores, alpha):
    if not (0 < alpha < 1):
        raise ValueError("alpha outside (0,1)")
    v=np.sort(np.asarray(scores,dtype=float).ravel())
    if not len(v) or not np.isfinite(v).all():
        raise ValueError("Calibration scores must be finite and nonempty")
    rank=int(np.ceil((len(v)+1)*(1-alpha)))
    if rank>len(v):
        return float("inf")
    return float(v[rank-1])

def calibrate_source(groups,pred,target,sigma,seed,alpha):
    masks,group_ids=grouped_partition(groups,seed)
    fit,cal,test=masks
    abs_error=np.abs(pred-target)
    # Fit scaling by least squares of sigma to |error|; this scale is a
    # magnitude regression, NOT a Gaussian standard-deviation estimate.
    x=sigma[fit]
    scale=max(1e-10,float((x@abs_error[fit])/(x@x)))
    sigma_scaled=scale*sigma
    candidates={"raw":sigma,"magnitude_scaled":sigma_scaled}
    methods={}
    for name,base in candidates.items():
        scores=abs_error[cal]/np.maximum(base[cal],1e-12)
        q=finite_sample_quantile(scores,alpha)
        radius=q*base[test]
        residuals=abs_error[test]
        # Each map-instance is the correct block for heldout reporting.
        per_group={}
        for gid in group_ids[2]:
            local=test & (groups==gid)
            per_group[str(gid)]=float(np.mean(abs_error[local]<=q*base[local]))
        methods[name]=dict(scale_factor=(1.0 if name=="raw" else scale),
                           conformal_multiplier=q,
                           empirical_state_coverage=float(np.mean(residuals<=radius)),
                           mean_interval_halfwidth=float(np.mean(radius)),
                           per_test_map_coverage=per_group,
                           n_calibration_states=int(cal.sum()),
                           n_test_states=int(test.sum()))
    return dict(seed=seed,alpha=alpha,
                fit_map_ids=group_ids[0],calibration_map_ids=group_ids[1],test_map_ids=group_ids[2],
                methods=methods)

def evaluate(path,alpha,seeds):
    groups,pred,target,sigma=load_archive(path)
    trials=[calibrate_source(groups,pred,target,sigma,seed,alpha) for seed in seeds]
    stats={}
    for method in ("raw","magnitude_scaled"):
        values=np.array([trial["methods"][method]["empirical_state_coverage"] for trial in trials])
        widths=np.array([trial["methods"][method]["mean_interval_halfwidth"] for trial in trials])
        stats[method]={"mean_empirical_state_coverage":float(values.mean()),
                       "min_empirical_state_coverage":float(values.min()),
                       "max_empirical_state_coverage":float(values.max()),
                       "mean_interval_halfwidth":float(widths.mean()),
                       "n_seeds":len(trials)}
    return dict(dataset=str(path.resolve()),source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                evidence="archived_generated_grid_instances_NOT_physical_sensor_data",
                nominal_coverage=1-alpha,
                statistic_unit="within-map-correlated states on held-out map instances",
                warning="Sample-level split-conformal quantiles with within-map dependencies have no asserted finite-sample groupwise guarantee; actual held-out coverage is directly measured.",
                results=stats,trials=trials,
                physical_robot_trials=0)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=Path,default=THIS.parent/"results"/"uncertainty_error_data.csv")
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--alpha",type=float,default=.1)
    p.add_argument("--seeds",type=int,default=10)
    args=p.parse_args()
    if args.seeds<2 or args.seeds>1000:
        p.error("--seeds must be in [2,1000]")
    result=evaluate(args.input,args.alpha,range(args.seeds))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result["results"],indent=2,sort_keys=True))
    print("C02 evidence: archived generated grid-worlds; zero real robot trials")
if __name__=="__main__":
    main()
