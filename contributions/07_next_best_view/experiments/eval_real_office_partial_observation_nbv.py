"""C07 actual indoor-map geometry, GENERATED partial visibility and NBV rankings.

Uses real LILocBench office occupancy geometry only as the world model.
The observation mask is a synthetic radius-limited reveal; visibility has NO
ray-casting or physical LiDAR ground truth. Information gain is the count
of unknown cells in an ideal circular footprint, NOT sensed entropy.
No robot or communication RSSI measurements are used.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import sys
from collections import deque
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_dilation, distance_transform_edt, label
import yaml
from dynnav.mapping.ros_map import load_ros_map

HERE=Path(__file__).resolve().parent
CODE=HERE.parent/"code"
C03=HERE.parents[1]/"03_belief_risk_planning"/"experiments"
for directory in (CODE,C03):
    if str(directory) not in sys.path:
        sys.path.insert(0,str(directory))
from nbv_scoring import ViewCandidate,score_candidates,NBVWeights
from eval_real_map_proximity_risk import occupancy

FOUR=np.array([[0,1,0],[1,1,1],[0,1,0]],dtype=bool)

def generate_observed(grid,base,radius):
    """Artificially reveal true map pixels within radius; unknown elsewhere."""
    if radius<3:
        raise ValueError("Synthetic observation radius too short")
    h,w=grid.shape
    bx,by=base
    y0=max(0,by-radius);y1=min(h,by+radius+1)
    x0=max(0,bx-radius);x1=min(w,bx+radius+1)
    known=np.zeros((h,w),dtype=bool)
    ys,xs=np.ogrid[y0:y1,x0:x1]
    known[y0:y1,x0:x1]=(xs-bx)**2+(ys-by)**2<=radius**2
    occupied_known=known & (grid!=0)
    free_known=known & (grid==0)
    return known,occupied_known,free_known

def known_distances(free_known,base):
    h,w=free_known.shape
    bx,by=base
    if not (0<=bx<w and 0<=by<h and free_known[by,bx]):
        raise ValueError("Base not in known free-space")
    dist=np.full((h,w),-1,dtype=np.int32)
    q=deque([(bx,by)])
    dist[by,bx]=0
    while q:
        x,y=q.popleft()
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            xx,yy=x+dx,y+dy
            if 0<=xx<w and 0<=yy<h and free_known[yy,xx] and dist[yy,xx]<0:
                dist[yy,xx]=dist[y,x]+1
                q.append((xx,yy))
    return dist

def choose_bases(grid,n,seed,minimum_clearance=32):
    free=grid==0
    distance=distance_transform_edt(free)
    labels,n_components=label(free,structure=FOUR.astype(np.uint8))
    counts=np.bincount(labels.ravel())
    counts[0]=0
    dominant=int(np.argmax(counts))
    cells=np.argwhere((labels==dominant)&(distance>=minimum_clearance))
    if len(cells)<n:
        raise ValueError("Insufficient verified clear real-map free-space starts")
    rng=np.random.default_rng(seed)
    # Sample diverse physical map regions instead of four nearly adjacent
    # points in the only giant open room. The 4-connected component remains
    # the same but selected bases must be spatially separated where possible.
    order=rng.permutation(len(cells))
    chosen=[]
    min_separation=max(12,2*minimum_clearance)
    for idx in order:
        y,x=map(int,cells[idx])
        if all((x-px)**2+(y-py)**2 >= min_separation**2 for px,py in chosen):
            chosen.append((x,y))
            if len(chosen)==n:
                break
    if len(chosen)<n:
        raise ValueError("Insufficient geographically separated, connected real-map start regions")
    return chosen

def frontier_candidates(known,free_known,dist,occupied_known,base,sensor_radius,
                        sample_max=100,seed=0):
    # A frontier is a REACHABLE KNOWN FREE cell adjacent to a simulated unknown cell.
    unknown=~known
    frontier=free_known & (dist>=0) & binary_dilation(unknown,structure=FOUR)
    ys,xs=np.nonzero(frontier)
    if not len(xs):
        raise ValueError("No reachable simulated frontier on this real map")
    rng=np.random.default_rng(seed)
    indices=rng.choice(len(xs),size=min(len(xs),sample_max),replace=False)
    # Only known obstacle geometry may influence risk. NO ground-truth obstacle
    # lookup outside known cells is allowed at scoring time.
    clearance=distance_transform_edt(~occupied_known)
    offsets=[(dx,dy) for dy in range(-sensor_radius,sensor_radius+1)
             for dx in range(-sensor_radius,sensor_radius+1)
             if dx*dx+dy*dy <= sensor_radius*sensor_radius]
    h,w=known.shape
    candidates=[]
    metadata={}
    for i in indices:
        x,y=int(xs[i]),int(ys[i])
        info=sum(0<=x+dx<w and 0<=y+dy<h and not known[y+dy,x+dx]
                 for dx,dy in offsets)
        if info<=0:
            continue
        travel=int(dist[y,x])
        # Known-cell clearance, not physical collision likelihood.
        clearance_proxy=float(np.exp(-clearance[y,x]/5.))
        # Returnability is actual connected known-free path to the declared base.
        # The penalty is an arbitrary normalized distance, not kinodynamics.
        recovery=1./(1.+travel/30.)
        name=f"x{x}_y{y}"
        candidates.append(ViewCandidate(
            name=name,information_gain=float(info),travel_cost=float(travel+1),
            path_risk=clearance_proxy,returnability=float(recovery),connectivity=1.))
        metadata[name]=dict(x=x,y=y,unknown_footprint_cells=info,
                            known_free_travel_steps=travel,
                            known_obstacle_proximity_proxy=clearance_proxy,
                            known_geometric_return_to_base=True)
    if len(candidates)<2:
        raise ValueError("Too few valid independent candidate viewpoints")
    return candidates,metadata

def evaluate(map_yaml,out_dir,n_starts,seed,observed_radius,sensor_radius):
    yaml_path=map_yaml.resolve()
    meta=yaml.safe_load(yaml_path.read_text())
    image=(yaml_path.parent/meta["image"]).resolve()
    obj=load_ros_map(yaml_path,unknown_as_obstacle=True)
    grid=occupancy(obj)
    bases=choose_bases(grid,n_starts,seed,minimum_clearance=max(5,observed_radius//3))
    rows=[];summary=[]
    for task,base in enumerate(bases):
        known,occupied,free=generate_observed(grid,base,observed_radius)
        dist=known_distances(free,base)
        candidates,metadata=frontier_candidates(
            known,free,dist,occupied,base,sensor_radius,seed=seed+task)
        scores=score_candidates(candidates,NBVWeights(risk_weight=3,returnability_weight=2,
                                                  connectivity_weight=0))
        classic=next(s for s in scores if s.selected_by_classic)
        safe=next(s for s in scores if s.selected_by_safe)
        for score in scores:
            rows.append(dict(task=task,base_x=base[0],base_y=base[1],
                             **metadata[score.name],**score.to_dict()))
        summary.append(dict(task=task,base_x=base[0],base_y=base[1],
                            candidates=len(scores),
                            classic_selected=classic.name,
                            returnability_selected=safe.name,
                            classic_IG_cells=classic.information_gain,
                            safe_IG_cells=safe.information_gain,
                            classic_risk_proxy=classic.path_risk,
                            safe_risk_proxy=safe.path_risk,
                            classic_returnability_proxy=classic.returnability,
                            safe_returnability_proxy=safe.returnability))
    out_dir.mkdir(parents=True,exist_ok=True)
    for name,data in (("viewpoints.csv",rows),("paired_rankings.csv",summary)):
        with (out_dir/name).open("w",newline="",encoding="utf-8") as f:
            writer=csv.DictWriter(f,fieldnames=list(data[0]))
            writer.writeheader()
            writer.writerows(data)
    provenance=dict(evidence="real_office_geometry_with_synthetic_partial_observations",
                    map_yaml_sha256=hashlib.sha256(yaml_path.read_bytes()).hexdigest(),
                    map_image_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
                    map_shape=[grid.shape[1],grid.shape[0]],
                    observation_model="ideal radius-limited circular reveal; no occlusion or ray-casting",
                    information_gain="count of still unknown pixels in ideal future circular footprint; not entropy",
                    known_returnability="reachable known free-space return to start with 4-connected BFS",
                    path_cost="known-free-space BFS path length",
                    risk="analytic proximity to KNOWN obstacles only; not collision probability",
                    connectivity="fixed non-measured constant; no communication evidence",
                    n_starts=n_starts,random_seed=seed,
                    observed_radius_cells=observed_radius,sensor_radius_cells=sensor_radius,
                    physical_robot_trials=0,actual_sensor_scans_used=False,
                    action_triggered_navigation=False)
    (out_dir/"provenance.json").write_text(json.dumps(provenance,indent=2,sort_keys=True)+"\n")
    print(json.dumps(provenance,indent=2,sort_keys=True))
    print("Completed C07 paired ranking problems:",len(summary))
    return rows,summary,provenance

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("map_yaml",type=Path)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--starts",type=int,default=4)
    p.add_argument("--seed",type=int,default=17)
    p.add_argument("--observed-radius",type=int,default=24)
    p.add_argument("--sensor-radius",type=int,default=15)
    a=p.parse_args()
    evaluate(a.map_yaml,a.output_dir,a.starts,a.seed,a.observed_radius,a.sensor_radius)
if __name__=="__main__":
    main()
