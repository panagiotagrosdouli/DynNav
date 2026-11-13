"""C13 actual action-conditioned one-step dynamics training from REAL Dingo rosbag.

Physically recorded odometry + historical cmd_vel are used as offline
supervision. This is a trained small GRU latent state predictor; it is NOT the
historical untrained NumPy RSSM/Dreamer, NOT an imagined multi-step controller,
and the C13 model never issued commands to the recorded Dingo.

Actions are aligned with the preceding timestamp only (no future message
leakage). Train/validation/test are strictly chronological nonoverlapping
blocks with a full history-gap; normalization uses train-only statistics.
"""
from __future__ import annotations
import argparse
import bisect
import hashlib
import json
import math
from pathlib import Path
import numpy as np

DEFAULT_ODOM="/dingo_velocity_controller/odom"
DEFAULT_CMD="/dingo_velocity_controller/cmd_vel"

def quaternion_yaw(q):
    return math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))

def normalize_angle(a):
    return math.atan2(math.sin(a),math.cos(a))

def read_original_bag(path:Path):
    from rosbags.highlevel import AnyReader
    from rosbags.typesys import Stores
    if not path.is_file():
        raise FileNotFoundError(path)
    with AnyReader([path]) as reader:
        odom_connections=[c for c in reader.connections if c.topic==DEFAULT_ODOM and "Odometry" in c.msgtype]
        cmd_connections=[c for c in reader.connections if c.topic==DEFAULT_CMD and "Twist" in c.msgtype]
        if len(odom_connections)!=1 or len(cmd_connections)!=1:
            raise ValueError("C13 requires exactly one authentic odom and commanded Twist stream")
        odom=[]
        for conn,ns,raw in reader.messages(connections=odom_connections):
            message=reader.deserialize(raw,conn.msgtype)
            p=message.pose.pose.position
            yaw=quaternion_yaw(message.pose.pose.orientation)
            t=ns*1e-9
            if all(math.isfinite(v) for v in (t,p.x,p.y,yaw)):
                odom.append((t,float(p.x),float(p.y),yaw))
        commands=[]
        for conn,ns,raw in reader.messages(connections=cmd_connections):
            message=reader.deserialize(raw,conn.msgtype)
            t=ns*1e-9
            if all(math.isfinite(v) for v in (t,message.linear.x,message.angular.z)):
                commands.append((t,float(message.linear.x),float(message.angular.z)))
    if len(odom)<200 or len(commands)<200:
        raise ValueError("Too few genuine recorded odometry/commands")
    if any(b[0]<=a[0] for a,b in zip(odom,odom[1:])):
        raise ValueError("Original odometry has nonmonotonic timestamps")
    if any(b[0]<a[0] for a,b in zip(commands,commands[1:])):
        raise ValueError("Original commands have nonmonotonic timestamps")
    return odom,commands

def body_step(a,b):
    """Robot-body-frame motion from successive world odometry positions."""
    t,x,y,yaw=a
    dt=b[0]-t
    dx,dy=b[1]-x,b[2]-y
    return (dx*math.cos(yaw)+dy*math.sin(yaw),
           -dx*math.sin(yaw)+dy*math.cos(yaw),
           normalize_angle(b[3]-yaw),dt)

def aligned_steps(odom,commands):
    times=[v[0] for v in commands]
    seq=[]
    for a,b in zip(odom,odom[1:]):
        dx,dy,dyaw,dt=body_step(a,b)
        if not (.015<=dt<=.4 and math.hypot(dx,dy)<=.40 and abs(dyaw)<=.7):
            continue
        i=bisect.bisect_right(times,a[0])-1
        if i<0 or a[0]-times[i]>.6:
            continue
        _,v,w=commands[i]
        seq.append([dx,dy,dyaw,v,w,dt])
    out=np.asarray(seq,dtype=np.float32)
    if len(out)<200 or not np.isfinite(out).all():
        raise ValueError("Insufficient validated odom/command alignment")
    return out

def strict_block_windows(sequence,window=8):
    """Input all in block; first output never consumes previous block history."""
    if window<2 or len(sequence)<5*window:
        raise ValueError("Sequence too short for independent blocks")
    n=len(sequence)
    train_end=int(.65*n)
    val_end=int(.80*n)
    pieces={"train":(0,train_end),"validation":(train_end,val_end),"test":(val_end,n)}
    records={}
    for name,(start,end) in pieces.items():
        X=[];A=[];Y=[]
        for i in range(start+window,end):
            X.append(sequence[i-window:i])
            A.append(sequence[i,3:6])
            Y.append(sequence[i,:3])
        if not X:
            raise ValueError("Empty strict chronological split: "+name)
        records[name]=(np.asarray(X,dtype=np.float32),
                       np.asarray(A,dtype=np.float32),
                       np.asarray(Y,dtype=np.float32))
    return records,pieces

def fit_statistics(records):
    X,A,Y=records["train"]
    xm=X.reshape(-1,X.shape[-1]).mean(axis=0)
    xs=np.maximum(X.reshape(-1,X.shape[-1]).std(axis=0),1e-6)
    am=A.mean(axis=0);astd=np.maximum(A.std(axis=0),1e-6)
    ym=Y.mean(axis=0);ys=np.maximum(Y.std(axis=0),1e-6)
    return (xm,xs,am,astd,ym,ys)

def run(bag_path,outdir,epochs=8,seed=2026,window=8):
    import torch
    from torch import nn
    if epochs<1 or epochs>200:
        raise ValueError("epochs out of range")
    torch.manual_seed(seed)
    torch.set_num_threads(min(2,torch.get_num_threads()))
    odom,cmd=read_original_bag(bag_path)
    seq=aligned_steps(odom,cmd)
    records,splits=strict_block_windows(seq,window)
    xm,xs,am,astd,ym,ys=fit_statistics(records)
    def tensorize(split):
        X,A,Y=records[split]
        return (torch.tensor((X-xm)/xs,dtype=torch.float32),
                torch.tensor((A-am)/astd,dtype=torch.float32),
                torch.tensor((Y-ym)/ys,dtype=torch.float32))
    train=tensorize("train");val=tensorize("validation");test=tensorize("test")
    class Dynamics(nn.Module):
        def __init__(self):
            super().__init__()
            self.gru=nn.GRU(6,24,batch_first=True)
            self.head=nn.Sequential(nn.Linear(27,32),nn.Tanh(),nn.Linear(32,3))
        def forward(self,X,A):
            _,h=self.gru(X)
            return self.head(torch.cat([h[-1],A],dim=-1))
    model=Dynamics()
    optim=torch.optim.Adam(model.parameters(),lr=.004)
    losses=[];best_val=float("inf");best=None
    g=np.random.default_rng(seed)
    for epoch in range(epochs):
        order=g.permutation(len(train[0]))
        mse=[]
        model.train()
        for start in range(0,len(order),64):
            ix=order[start:start+64]
            yhat=model(train[0][ix],train[1][ix])
            loss=((yhat-train[2][ix])**2).mean()
            optim.zero_grad();loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(),2.)
            optim.step()
            mse.append(float(loss.item()))
        model.eval()
        with torch.no_grad():
            val_loss=float(((model(val[0],val[1])-val[2])**2).mean().item())
        losses.append({"epoch":epoch+1,"training_normalized_mse":float(np.mean(mse)),
                       "validation_normalized_mse":val_loss})
        if val_loss<best_val:
            best_val=val_loss
            best={k:v.detach().clone() for k,v in model.state_dict().items()}
    assert best is not None
    model.load_state_dict(best)
    model.eval()
    with torch.no_grad():
        predicted=model(test[0],test[1]).numpy()*ys+ym
    X,A,actual=records["test"]
    persistence=X[:,-1,:3]
    command=np.stack([A[:,0]*A[:,2],np.zeros(len(A)),A[:,1]*A[:,2]],axis=1)
    stationary=np.zeros_like(actual)
    def metrics(values):
        delta=values-actual
        return {"translational_rmse_m":float(np.sqrt(np.mean(np.sum(delta[:,:2]**2,axis=1)))),
                "heading_rmse_rad":float(np.sqrt(np.mean(delta[:,2]**2))),
                "translational_mae_m":float(np.mean(np.linalg.norm(delta[:,:2],axis=1))),
                "heading_mae_rad":float(np.mean(np.abs(delta[:,2])))}
    result={"trained_gru":metrics(predicted),"last_step_persistence":metrics(persistence),
            "commanded_kinematic":metrics(command),"stationary":metrics(stationary)}
    def digest(path):
        h=hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda:stream.read(2**20),b""):
                h.update(chunk)
        return h.hexdigest()
    provenance={"recorded_ros1_bag_sha256":digest(bag_path),
                "observed_odom_messages":len(odom),"observed_twist_messages":len(cmd),
                "valid_aligned_steps":len(seq),
                "split_indices":{k:list(v) for k,v in splits.items()},
                "window":window,"seed":seed,"epochs":epochs,
                "train_windows":len(records["train"][0]),
                "validation_windows":len(records["validation"][0]),
                "test_windows":len(records["test"][0]),
                "original_commands_generated_by_c13":False,
                "action_conditioned_one_step_model":True,
                "historical_untrained_rssm_used":False,
                "physical_robot_trials":0}
    outdir.mkdir(parents=True,exist_ok=True)
    torch.save({"state_dict":best,"training_only_normalization":{
        "history_mean":xm.tolist(),"history_std":xs.tolist(),
        "command_mean":am.tolist(),"command_std":astd.tolist(),
        "target_mean":ym.tolist(),"target_std":ys.tolist()},
        "provenance":provenance},outdir/"c13_trained_real_dingo_dynamics.pt")
    report={"evidence_type":"ACTUAL_PHYSICALLY_RECORDED_DINGO_ODOM_AND_COMMAND_OFFLINE_SUPERVISED_ONE_STEP_DYNAMICS",
            "provenance":provenance,"training_history":losses,
            "heldout_metrics":result,
            "not_proven":"Full learned RSSM / Dreamer latent world model, reliable multi-step future rollouts, C13 command of the original Dingo, physical navigation success or safety."}
    (outdir/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2,sort_keys=True))
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("original_dingo_bag",type=Path)
    p.add_argument("--output-dir",required=True,type=Path)
    p.add_argument("--epochs",type=int,default=8)
    p.add_argument("--seed",type=int,default=2026)
    p.add_argument("--history",type=int,default=8)
    a=p.parse_args()
    run(a.original_dingo_bag.resolve(),a.output_dir.resolve(),a.epochs,a.seed,a.history)

if __name__=="__main__":
    main()
