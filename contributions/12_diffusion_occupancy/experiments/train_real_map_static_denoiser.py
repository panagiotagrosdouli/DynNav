"""C12 real-map GEOMETRY learned conditional diffusion denoiser (not motion prediction).

Actually trains a small PyTorch noise predictor (not the repository's
historically untrained NumPy score-network stub) on non-overlapping spatial
tiles of an authentic LILocBench ROS occupancy map. Corruption and diffusion
noise are synthetic; the target is STATIC occupancy, not observed future
occupancy. Spatially held-out tiles never appear in the training split.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import random
import time
from pathlib import Path

import numpy as np

def extract_tiles(map_yaml: Path, tile_size: int = 32):
    from dynnav.mapping.ros_map import load_ros_map
    original=load_ros_map(map_yaml, unknown_as_obstacle=True)
    h,w=original.grid.height,original.grid.width
    array=np.zeros((h,w),dtype=np.float32)
    for x,y in original.grid.obstacles:
        array[y,x]=1.
    tiles=[]
    cols=(w//tile_size)
    rows=(h//tile_size)
    cutoff=int(cols*.60)
    for y in range(rows):
        for x in range(cols):
            block=array[y*tile_size:(y+1)*tile_size,x*tile_size:(x+1)*tile_size]
            if block.shape!=(tile_size,tile_size):
                continue
            # Spatially disjoint geographic columns; no overlap, gap across split.
            group="train" if x<cutoff else ("test" if x>=cutoff+1 else "gap")
            if group=="gap":
                continue
            tiles.append((group,int(x),int(y),block.copy()))
    return tiles,original

def cosine_schedule(steps: int):
    if steps<4:
        raise ValueError("At least 4 diffusion steps required")
    timeline=np.arange(steps+1,dtype=float)/steps
    ab=np.cos((timeline+.008)/(1.008)*np.pi/2)**2
    ab=ab/ab[0]
    return np.clip(ab[1:],1e-4,1.).astype(np.float32)

def run(map_yaml: Path,outdir: Path,seed:int,epochs:int,steps:int,tile_size:int):
    import torch
    from torch import nn
    if epochs<1 or epochs>100 or tile_size<8 or tile_size%8:
        raise ValueError("Bad epoch or tile-size request")
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)
    torch.set_num_threads(min(2,torch.get_num_threads()))
    tiles,world=extract_tiles(map_yaml,tile_size)
    train=np.stack([t[3] for t in tiles if t[0]=="train"]).astype(np.float32)
    test=np.stack([t[3] for t in tiles if t[0]=="test"]).astype(np.float32)
    if len(train)<10 or len(test)<10:
        raise RuntimeError("Insufficient train/test geographically disjoint tiles")
    alphas=cosine_schedule(steps)
    class Denoiser(nn.Module):
        def __init__(self):
            super().__init__()
            self.net=nn.Sequential(nn.Conv2d(3,24,3,padding=1),nn.ReLU(),
                                   nn.Conv2d(24,24,3,padding=1),nn.ReLU(),
                                   nn.Conv2d(24,1,3,padding=1))
        def forward(self,xt,observation,t):
            tmap=torch.ones_like(xt)*t
            return self.net(torch.cat([xt,observation,tmap],dim=1))
    model=Denoiser()
    optimizer=torch.optim.Adam(model.parameters(),lr=.002)
    rng=np.random.default_rng(seed)
    train_tensor=torch.from_numpy(train)[:,None,:,:]
    test_tensor=torch.from_numpy(test)[:,None,:,:]
    history=[]
    for epoch in range(epochs):
        order=rng.permutation(len(train))
        batch_losses=[]
        model.train()
        for begin in range(0,len(order),32):
            ids=order[begin:begin+32]
            clean=train_tensor[ids]
            noise=torch.randn_like(clean)
            t=int(rng.integers(1,steps))
            a=float(alphas[t])
            xt=(a**.5)*clean+((1-a)**.5)*noise
            # An independent noisy/occluded observation, not a perfect target.
            obs=clean.clone()
            flip=torch.rand_like(obs)<.12
            obs=torch.where(flip,1-obs,obs)
            # Random rectangular unknown patch represented by neutral .5.
            top=int(rng.integers(0,tile_size//2))
            left=int(rng.integers(0,tile_size//2))
            obs[:,:,top:top+tile_size//4,left:left+tile_size//4]=.5
            prediction=model(xt,obs,t/steps)
            loss=((prediction-noise)**2).mean()
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(),5.0)
            optimizer.step()
            batch_losses.append(float(loss.item()))
        history.append({"epoch":epoch+1,"noise_mse":float(np.mean(batch_losses))})
    # Same held-out corrupted observation/xt for baseline and learned model.
    model.eval()
    with torch.no_grad():
        clean=test_tensor
        noise=torch.randn_like(clean)
        t=max(1,int(steps*.55))
        a=float(alphas[t])
        xt=a**.5*clean+(1-a)**.5*noise
        obs=clean.clone()
        obs=torch.where(torch.rand_like(obs)<.12,1-obs,obs)
        top,left=tile_size//4,tile_size//4
        obs[:,:,top:top+tile_size//4,left:left+tile_size//4]=.5
        predicted_noise=model(xt,obs,t/steps)
        reconstructed=torch.clamp((xt-(1-a)**.5*predicted_noise)/(a**.5),0,1)
        baseline=torch.clamp(obs,.001,.999)
        restored=torch.clamp(reconstructed,.001,.999)
        target=clean
        def metrics(p):
            brier=float(((p-target)**2).mean().item())
            nll=float((-(target*torch.log(p)+(1-target)*torch.log(1-p))).mean().item())
            return {"brier":brier,"nll":nll}
        baseline_metrics=metrics(baseline)
        learned_metrics=metrics(restored)
    outdir.mkdir(parents=True,exist_ok=True)
    checkpoint=outdir/"c12_realmap_static_denoiser.pt"
    source_image=(map_yaml.parent/json.loads(json.dumps(__import__("yaml").safe_load(map_yaml.read_text())))["image"]).resolve()
    provenance={"source_map_yaml_sha256":hashlib.sha256(map_yaml.read_bytes()).hexdigest(),
                "source_map_image_sha256":hashlib.sha256(source_image.read_bytes()).hexdigest(),
                "seed":seed,"epochs":epochs,"diffusion_steps":steps,"tile_size":tile_size,
                "n_train_tiles":len(train),"n_test_tiles":len(test),
                "split":"disjoint_geographic_columns_with_one_column_gap",
                "true_observation_type":"authentic_static_office_occupancy_map",
                "artificial_data":"synthetic_observation_corruption_and_diffusion_noise",
                "future_occupancy_prediction_verified":False,"physical_robot_trial":False,
                "historical_numpy_score_network_used":False}
    torch.save({"state_dict":model.state_dict(),"provenance":provenance},checkpoint)
    result={"training":history,"baseline":baseline_metrics,"trained_noise_denoiser":learned_metrics,
            "provenance":provenance,
            "scientific_limitation":"Actual neural training on authentic real-world static map tiles with synthetic noise. No future observations, no motion prediction, no live LiDAR or physical robot control."}
    (outdir/"report.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("map_yaml",type=Path)
    p.add_argument("--output-dir",required=True,type=Path)
    p.add_argument("--epochs",type=int,default=2)
    p.add_argument("--steps",type=int,default=20)
    p.add_argument("--tile-size",type=int,default=32)
    p.add_argument("--seed",type=int,default=2026)
    args=p.parse_args()
    run(args.map_yaml.resolve(),args.output_dir.resolve(),args.seed,args.epochs,args.steps,args.tile_size)

if __name__=="__main__":
    main()
