"""C16 actual offline Dingo motion-data pseudo-federation vs centralized training.

ONE recorded physical Dingo run is split into contiguous temporal pseudo-clients.
This DOES NOT represent multiple robots, actual private sites, DDS transport,
secure aggregation, differential privacy, or deployed robot control.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

MODULE=Path(__file__).resolve().parents[1]
REPO=MODULE.parents[1]
C13=REPO/"contributions"/"13_latent_world_model"/"experiments"
for folder in (MODULE,C13):
    if str(folder) not in sys.path:
        sys.path.insert(0,str(folder))
from train_real_dingo_action_dynamics import read_original_bag,aligned_steps
from federated_nav import FederatedServer,FedNavConfig,NavModel

def temporal_partition(sequence,n_clients=6):
    """Chronological 65/15/20 splits with disjoint temporal train shards."""
    values=np.asarray(sequence,dtype=float)
    if values.ndim!=2 or values.shape[1]!=6 or not np.isfinite(values).all():
        raise ValueError("Expected 6 finite original motion/command features")
    if n_clients<2 or len(values)<10*n_clients:
        raise ValueError("Not enough data for pseudo-client evaluation")
    n=len(values);nt=int(.65*n);nv=int(.80*n)
    training=np.arange(nt)
    client_indices=np.array_split(training,n_clients)
    if any(len(ix)<10 for ix in client_indices):
        raise ValueError("Each pseudo-client needs >=10 real recorded examples")
    assert set(np.concatenate(client_indices))==set(training)
    return client_indices,np.arange(nt,nv),np.arange(nv,n)

def features_and_targets(seq):
    v,w,dt=seq[:,3],seq[:,4],seq[:,5]
    X=np.column_stack((v*dt,w*dt,dt))
    Y=seq[:,:3].astype(float)
    if not np.isfinite(X).all() or not np.isfinite(Y).all():
        raise ValueError("Nonfinite movement features")
    return X,Y

def standardize_training_only(X,Y,training):
    mean_x=X[training].mean(axis=0)
    std_x=np.maximum(X[training].std(axis=0),1e-6)
    mean_y=Y[training].mean(axis=0)
    std_y=np.maximum(Y[training].std(axis=0),1e-6)
    return (X-mean_x)/std_x,(Y-mean_y)/std_y,(mean_x,std_x,mean_y,std_y)

def local_linear_fit(start,X,Y,indices,epochs=3,lr=.025):
    W=start["W"].copy()
    bias=start["b"].copy()
    for _ in range(epochs):
        error=X[indices]@W.T+bias-Y[indices]
        gradW=(2./len(indices))*error.T@X[indices]
        gradb=2.*error.mean(axis=0)
        W-=lr*gradW
        bias-=lr*gradb
        if not np.isfinite(W).all() or not np.isfinite(bias).all():
            raise ValueError("Divergent local fitting")
    return {"W":W,"b":bias}

def centralized_fit(X,Y,indices,rounds=60,local_epochs=3,lr=.025):
    model={"W":np.zeros((3,3)), "b":np.zeros(3)}
    for _ in range(rounds):
        model=local_linear_fit(model,X,Y,indices,epochs=local_epochs,lr=lr)
    return model

def offline_fedavg(X,Y,clients,rounds=60,local_epochs=3,lr=.025,aggregation="weighted"):
    cfg=FedNavConfig(n_robots=len(clients),input_dim=3,output_dim=3,aggregation=aggregation)
    server=FederatedServer(NavModel(W=np.zeros((3,3)),b=np.zeros(3)),cfg)
    for _ in range(rounds):
        current=server.global_model.get_params()
        updates=[(local_linear_fit(current,X,Y,idx,epochs=local_epochs,lr=lr),len(idx))
                 for idx in clients]
        server.global_model.set_params(server.aggregate(updates))
    return server.global_model.get_params()

def metric(pred,true):
    difference=pred-true
    return {
        "translation_rmse_m":float(np.sqrt(np.mean(np.sum(difference[:,:2]**2,axis=1)))),
        "heading_rmse_rad":float(np.sqrt(np.mean(difference[:,2]**2))),
    }

def run(path,outdir,rounds=60,seed=2026,n_clients=6):
    if rounds<1 or rounds>300:
        raise ValueError("Rounds must be 1..300")
    odom,cmd=read_original_bag(path)
    seq=aligned_steps(odom,cmd)
    clients,val,test=temporal_partition(seq,n_clients)
    train=np.concatenate(clients)
    X,Y=features_and_targets(seq)
    Xn,Yn,norm=standardize_training_only(X,Y,train)
    fed=offline_fedavg(Xn,Yn,clients,rounds=rounds,aggregation="weighted")
    centralized=centralized_fit(Xn,Yn,train,rounds=rounds)
    uniform=offline_fedavg(Xn,Yn,clients,rounds=rounds,aggregation="uniform")
    target_mean,target_std=norm[2],norm[3]
    def infer(model,indices):
        return (Xn[indices]@model["W"].T+model["b"])*target_std+target_mean
    output={"federated_weighted":metric(infer(fed,test),Y[test]),
            "federated_uniform":metric(infer(uniform,test),Y[test]),
            "centralized_same_update_count":metric(infer(centralized,test),Y[test]),
            "stationary":metric(np.zeros_like(Y[test]),Y[test]),
            "command_kinematics":metric(np.column_stack(
                (X[test,0],np.zeros(len(test)),X[test,1])),Y[test])}
    validation={name:metric(infer(model,val),Y[val]) for name,model in
                (("federated_weighted",fed),("federated_uniform",uniform),
                 ("centralized",centralized))}
    def source_hash(p):
        h=hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda:f.read(1024*1024),b""):
                h.update(chunk)
        return h.hexdigest()
    provenance={"original_ros1_bag_sha256":source_hash(path),
                "actual_odom_messages":len(odom),
                "actual_historical_commands":len(cmd),
                "valid_aligned_steps":len(seq),
                "pseudo_client_ranges":[[int(c[0]),int(c[-1])+1] for c in clients],
                "validation_range":[int(val[0]),int(val[-1])+1],
                "test_range":[int(test[0]),int(test[-1])+1],
                "train_only_normalization":True,
                "pseudo_clients_all_from_one_original_Dingo_recording":True,
                "actual_robots_in_federation":0,
                "dp_epsilon_claimed":False,
                "secure_aggregation_performed":False,
                "dds_communication_performed":False,
                "physical_robot_trials":0}
    report={"evidence_type":"real_Dingo_recording_offline_PSEUDO_federated_supervised_motion_regression",
            "rounds":rounds,"seed":seed,"pseudo_clients":len(clients),
            "provenance":provenance,"validation_metrics":validation,
            "chronological_test_metrics":output,
            "caution":"One physically recorded Dingo trajectory, partitioned into artificial temporal shards. This is an offline algorithmic FedAvg exercise, NOT a multi-robot federation or differential privacy guarantee."}
    outdir.mkdir(parents=True,exist_ok=True)
    (outdir/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    np.savez(outdir/"model_params.npz",federated_W=fed["W"],federated_b=fed["b"],
             centralized_W=centralized["W"],centralized_b=centralized["b"],
             train_x_mean=norm[0],train_x_std=norm[1],
             train_y_mean=norm[2],train_y_std=norm[3])
    print(json.dumps(report,indent=2,sort_keys=True))
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("original_dingo_bag",type=Path)
    p.add_argument("--output-dir",required=True,type=Path)
    p.add_argument("--rounds",type=int,default=60)
    p.add_argument("--pseudo-clients",type=int,default=6)
    args=p.parse_args()
    run(args.original_dingo_bag.resolve(),args.output_dir.resolve(),
        rounds=args.rounds,n_clients=args.pseudo_clients)

if __name__=="__main__":
    main()
