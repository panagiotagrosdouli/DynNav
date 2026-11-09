"""C04 real occupancy-map returnability and minimal irreversibility threshold.

Uses actual LILocBench office map GEOMETRY, generated connected endpoint
queries and an explicitly hand-designed geometric fragility score.
Static undirected grid reachability does NOT establish dynamic returnability
under closed doors, uncertainty, localization failures or physical dynamics.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import heapq
import json
import math
import sys
from collections import deque
from pathlib import Path

import numpy as np
from scipy.ndimage import convolve, distance_transform_edt

from dynnav.mapping.ros_map import load_ros_map

HERE=Path(__file__).resolve().parent
CODE=HERE.parent/"code"
C03=HERE.parents[1]/"03_belief_risk_planning"/"experiments"
for d in (CODE,C03):
    if str(d) not in sys.path:
        sys.path.insert(0,str(d))
from irreversibility_planner import astar_irreversibility_constrained
from eval_real_map_proximity_risk import occupancy,sample_connected_pairs,validate_path,search

NEIGHBORS=((1,0),(-1,0),(0,1),(0,-1))

def return_distances(free,base):
    h,w=free.shape
    bx,by=base
    if not (0<=bx<w and 0<=by<h and free[by,bx]):
        raise ValueError("Trusted base is outside free space")
    dist=np.full((h,w),-1,dtype=np.int32)
    dist[by,bx]=0
    q=deque([(bx,by)])
    while q:
        x,y=q.popleft()
        d=int(dist[y,x])+1
        for dx,dy in NEIGHBORS:
            nx,ny=x+dx,y+dy
            if 0<=nx<w and 0<=ny<h and free[ny,nx] and dist[ny,nx]<0:
                dist[ny,nx]=d
                q.append((nx,ny))
    return dist

def geometric_fragility(grid,return_distance,scale=None):
    """0..1 proxy only: return-distance, 4-neighbour escape scarcity, clearance."""
    free=grid==0
    if grid.shape!=return_distance.shape:
        raise ValueError("Grid and return distance shapes must agree")
    reach=free & (return_distance>=0)
    if not np.any(reach):
        raise ValueError("No geometrically returnable states")
    degree=convolve(free.astype(np.int8),np.array([[0,1,0],[1,0,1],[0,1,0]]),mode="constant",cval=0)
    if scale is None:
        # Predeclared fixed scale proportional to map dimensions; not fitted to test route.
        scale=float(grid.shape[0]+grid.shape[1])
    if scale<=0:
        raise ValueError("Distance scale must be positive")
    distance_cost=np.clip(return_distance.astype(float)/scale,0,1)
    clearance=distance_transform_edt(free)
    fragility=.50*distance_cost+.30*(1-degree/4.)+.20*np.exp(-clearance/5.)
    fragility=np.clip(fragility,0.,1.)
    fragility[~reach]=1.
    return fragility,reach

def minimum_feasible_tau(free,I,start,goal):
    """Exact minimax bottleneck among 4-connected paths, not coarse tau-grid search."""
    h,w=free.shape
    for x,y in (start,goal):
        if not 0<=x<w or not 0<=y<h or not free[y,x] or not np.isfinite(I[y,x]):
            raise ValueError("Invalid minimax endpoint")
    best=np.full((h,w),np.inf,dtype=np.float64)
    sx,sy=start
    gx,gy=goal
    best[sy,sx]=float(I[sy,sx])
    q=[(best[sy,sx],start)]
    while q:
        score,(x,y)=heapq.heappop(q)
        if score>best[y,x]+1e-12:
            continue
        if (x,y)==goal:
            return score
        for dx,dy in NEIGHBORS:
            nx,ny=x+dx,y+dy
            if 0<=nx<w and 0<=ny<h and free[ny,nx]:
                new=max(score,float(I[ny,nx]))
                if new+1e-12<best[ny,nx]:
                    best[ny,nx]=new
                    heapq.heappush(q,(new,(nx,ny)))
    return math.inf

def path_metrics(path,I,distance,free):
    vals=np.array([I[y,x] for x,y in path],dtype=float)
    return dict(steps=len(path)-1,
                max_I=float(vals.max()),
                mean_I=float(vals.mean()),
                min_recoverability=float(1-vals.max()),
                all_returnable=bool(all(distance[y,x]>=0 for x,y in path)),
                max_return_distance_cells=int(max(distance[y,x] for x,y in path)))

def evaluate(map_yaml,outdir,n_tasks,seed,tau):
    import yaml
    if not 0<=tau<=1:
        raise ValueError("tau must be in [0,1]")
    yml=map_yaml.resolve()
    metadata=yaml.safe_load(yml.read_text())
    image=(yml.parent/metadata["image"]).resolve()
    ros_map=load_ros_map(yml,unknown_as_obstacle=True)
    grid=occupancy(ros_map)
    # Each start is its own stated trusted base; future base changes are not tested.
    tasks=sample_connected_pairs(grid,n_tasks,seed,min_distance=8)
    rows=[]
    for index,(base,goal) in enumerate(tasks):
        distances=return_distances(grid==0,base)
        I,reachable=geometric_fragility(grid,distances)
        # Main optimal-length path; C03 search with zero risk weight.
        shortest,exp0,_=search(grid,base,goal,I,0.)
        if not validate_path(grid,shortest,base,goal):
            raise AssertionError("Baseline route invalid")
        minimum=minimum_feasible_tau(reachable,I,base,goal)
        minimum=min(1.,minimum+1e-9) if math.isfinite(minimum) else math.inf
        # Existing C04 hard-threshold A*: request tau, then exact minimax-safe threshold.
        nominal=astar_irreversibility_constrained(reachable,I,(base[1],base[0]),(goal[1],goal[0]),tau=tau)
        relaxed=astar_irreversibility_constrained(reachable,I,(base[1],base[0]),(goal[1],goal[0]),tau=minimum)
        if not relaxed.success:
            raise AssertionError(f"Exact feasible threshold failed to return path: {minimum}")
        converted=[(x,y) for y,x in relaxed.path]
        if not validate_path(grid,converted,base,goal):
            raise AssertionError("C04 relaxed route invalid")
        methods=[("distance_only",shortest,exp0,1.0),("hard_cap",[(x,y) for y,x in nominal.path] if nominal.success else None,nominal.expansions,tau),
                 ("minimax_feasible_cap",converted,relaxed.expansions,minimum)]
        for name,path,expanded,used_tau in methods:
            values=path_metrics(path,I,distances,reachable) if path else {}
            rows.append(dict(task=index,method=name,successful=bool(path),
                             start_x=base[0],start_y=base[1],
                             goal_x=goal[0],goal_y=goal[1],
                             requested_tau=tau,used_tau=used_tau,minimum_feasible_tau=minimum,
                             expansions=expanded,**values))
    outdir.mkdir(parents=True,exist_ok=True)
    with (outdir/"trials.csv").open("w",newline="",encoding="utf-8") as out:
        fields=list(dict.fromkeys(k for row in rows for k in row))
        writer=csv.DictWriter(out,fieldnames=fields)
        writer.writeheader();writer.writerows(rows)
    report=dict(evidence="authentic_indoor_occupancy_map_with_generated_tasks_geometric_returnability_proxy",
                map_yaml_sha256=hashlib.sha256(yml.read_bytes()).hexdigest(),
                map_image_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
                map_dimensions=[int(grid.shape[1]),int(grid.shape[0])],
                resolution_m=ros_map.resolution,
                n_tasks=n_tasks,random_seed=seed,nominal_tau=tau,
                returnability_definition="static_four_connected_reachability_to_declared_start_base",
                fragility_definition="0.50*normalized_base_distance + 0.30*(1-degree/4) + 0.20*exp(-obstacle_clearance_cells/5)",
                threshold_relaxation="exact_minimax_feasible_tau_with_floating_point_epsilon",
                physical_robot_trials=0,action_triggered_obstacle_evidence=False,
                physical_risk_calibration=False,
                scientific_limit="Real static map only; no closed-loop control, dynamic hazard, kinodynamic recoverability or physically measured return-to-base.")
    (outdir/"summary.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,sort_keys=True))
    print("C04 experimental rows:",len(rows))
    return rows,report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("map_yaml",type=Path)
    p.add_argument("--output-dir",required=True,type=Path)
    p.add_argument("--tasks",type=int,default=4)
    p.add_argument("--seed",type=int,default=17)
    p.add_argument("--tau",type=float,default=.22)
    a=p.parse_args()
    evaluate(a.map_yaml,a.output_dir,a.tasks,a.seed,a.tau)
if __name__=="__main__":
    main()
