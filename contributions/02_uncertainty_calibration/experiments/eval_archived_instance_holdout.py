"""Held-out instance calibration of the archived C02 uncertainty-error dataset.

The dataset is generated from random grid-world planning instances with a
retained neural checkpoint; it is NOT physical sensor/robot evidence. Group
splitting prevents rows from the same planning instance entering fit and test.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
CODE=ROOT/"code"
if str(CODE) not in sys.path:
    sys.path.insert(0,str(CODE))

from uncertainty_calibrator import (
    GlobalScaleCalibrator, QuantileBinCalibrator, absolute_error, evaluate_calibration
)

DEFAULT_INPUT=ROOT/"results"/"uncertainty_error_data.csv"

def load_archive(path: Path):
    groups=[]; prediction=[]; target=[]; sigmas=[]
    with path.open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        required={"instance_id","mu","h_star","sigma"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"Missing columns: {required-set(reader.fieldnames or [])}")
        for row in reader:
            groups.append(int(row["instance_id"]))
            prediction.append(float(row["mu"]))
            target.append(float(row["h_star"]))
            sigmas.append(float(row["sigma"]))
    if len(groups)<20 or len(set(groups))<2:
        raise ValueError("Need multiple map instances with at least 20 data points")
    arrays=(np.array(groups,dtype=int),np.array(prediction),np.array(target),np.array(sigmas))
    if not all(np.isfinite(a).all() for a in arrays) or np.any(arrays[3]<=0):
        raise ValueError("All prediction, target and sigma values must be finite; sigma positive")
    return arrays

def separate_instances(groups: np.ndarray, train_fraction: float, seed: int):
    if not 0<train_fraction<1:
        raise ValueError("train_fraction must be in (0,1)")
    ids=np.unique(groups)
    rng=np.random.default_rng(seed)
    ids=rng.permutation(ids)
    n=max(1,min(len(ids)-1,round(len(ids)*train_fraction)))
    train_ids=set(int(x) for x in ids[:n])
    mask=np.isin(groups,list(train_ids))
    if not mask.any() or mask.all():
        raise ValueError("Train and test instance sets must be nonempty")
    assert set(groups[mask]).isdisjoint(set(groups[~mask]))
    return mask,sorted(train_ids),sorted(set(int(x) for x in groups[~mask]))

def assess(path: Path, train_fraction: float, seed: int, n_bins: int):
    groups,pred,target,sigma=load_archive(path)
    training,train_ids,test_ids=separate_instances(groups,train_fraction,seed)
    err_train=absolute_error(pred[training],target[training])
    global_cal=GlobalScaleCalibrator().fit(err_train,sigma[training])
    bin_cal=QuantileBinCalibrator(n_bins=n_bins).fit(err_train,sigma[training])
    predicted={
        "raw_sigma":sigma[~training],
        "global_scale":global_cal.transform(sigma[~training]),
        "quantile_bin":bin_cal.transform(sigma[~training]),
    }
    reports={name:vars(evaluate_calibration(pred[~training],target[~training],values,n_bins=n_bins))
             for name,values in predicted.items()}
    data_hash=hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "source_file":str(path),
        "source_sha256":data_hash,
        "dataset_evidence":"archived_generated_grid_instances_not_real_robot",
        "seed":seed,
        "n_bins":n_bins,
        "train_instance_ids":train_ids,
        "heldout_instance_ids":test_ids,
        "train_samples":int(training.sum()),
        "heldout_samples":int((~training).sum()),
        "global_scale":global_cal.scale,
        "heldout_reports":reports,
        "claim_boundary":"Calibrators trained on independent grid instances; this does not prove Gaussian coverage, real sensor uncertainty, safe control or generalization to physical robots.",
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=Path,default=DEFAULT_INPUT)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--train-fraction",type=float,default=.6)
    p.add_argument("--seed",type=int,default=2026)
    p.add_argument("--bins",type=int,default=10)
    a=p.parse_args()
    report=assess(a.input.resolve(),a.train_fraction,a.seed,a.bins)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("C02 independent grid-instance calibration")
    print("train instances:",len(report["train_instance_ids"]),"heldout:",len(report["heldout_instance_ids"]))
    for key,value in report["heldout_reports"].items():
        print(key,"ECE_abs_error",round(value["ece_abs_error"],5),
              "coverage_1sigma",round(value["coverage_1sigma"],5))
    print("Physical robot trials: NONE")
if __name__=="__main__":
    main()
