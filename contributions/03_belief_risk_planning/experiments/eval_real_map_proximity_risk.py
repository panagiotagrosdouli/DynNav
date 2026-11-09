"""C03 real-world occupancy-map route evaluation, NOT physical robot trials.

The map geometry comes from an actual recorded indoor office environment.
The proximity risk field is an explicit analytic proxy, NOT an estimated
physical accident probability. Edge-additive risk shaping is not CVaR
optimization; upper-tail CVaR is an independent POST-HOC path metric.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import heapq
import json
import math
import time
from pathlib import Path
import numpy as np
from scipy.ndimage import distance_transform_edt, label

from dynnav.mapping.ros_map import load_ros_map

MOVES=((1,0),(-1,0),(0,1),(0,-1))
CROSS=np.array([[0,1,0],[1,1,1],[0,1,0]],dtype=np.uint8)

def occupancy(ros_map):
    g=np.zeros((ros_map.grid.height,ros_map.grid.width),dtype=np.uint8)
    for x,y in ros_map.grid.obstacles:
        g[y,x]=1
    return g

def proximity_field(grid, decay_cells=5.0):
    if decay_cells<=0:
        raise ValueError("decay_cells must be positive")
    free=grid==0
    if not np.any(free):
        raise ValueError("Map has no free cells")
    dist=distance_transform_edt(free)
    risk=np.exp(-dist/decay_cells)
    risk[~free]=1.0
    return risk

def sample_connected_pairs(grid,count,seed,min_distance):
    labels,n=label(grid==0,structure=CROSS)
    sizes=np.bincount(labels.reshape(-1))
    sizes[0]=0
    dominant=int(np.argmax(sizes))
    if n==0 or sizes[dominant]<2:
        raise ValueError("No connected free-space component")
    cells=np.argwhere(labels==dominant)
    rng=np.random.default_rng(seed)
    result=[]
    seen=set()
    for _ in range(count):
        for attempt in range(10000):
            ix=rng.choice(len(cells),size=2,replace=False)
            (sy,sx),(gy,gx)=cells[ix]
            start,goal=(int(sx),int(sy)),(int(gx),int(gy))
            if abs(sx-gx)+abs(sy-gy)>=min_distance and (start,goal) not in seen:
                seen.add((start,goal))
                result.append((start,goal))
                break
        else:
            raise ValueError("Insufficient separated free endpoints")
    return result

def search(grid,start,goal,risk,weight):
    """Optimal A* for the chosen nonnegative *additive* risk-weighted edge cost."""
    if not math.isfinite(weight) or weight<0:
        raise ValueError("risk weight must be finite and nonnegative")
    h,w=grid.shape
    for x,y in (start,goal):
        if not 0<=x<w or not 0<=y<h or grid[y,x]:
            raise ValueError("Start/goal blocked or out of bounds")
    pq=[(abs(start[0]-goal[0])+abs(start[1]-goal[1]),0.,start)]
    best={start:0.}
    parent={start:None}
    expanded=set()
    while pq:
        _,g,node=heapq.heappop(pq)
        if node in expanded or g>best[node]+1e-9:
            continue
        expanded.add(node)
        if node==goal:
            path=[]
            while node is not None:
                path.append(node)
                node=parent[node]
            return path[::-1],len(expanded),g
        x,y=node
        for dx,dy in MOVES:
            nx,ny=x+dx,y+dy
            nxt=(nx,ny)
            if not (0<=nx<w and 0<=ny<h) or grid[ny,nx] or nxt in expanded:
                continue
            step=1.+weight*float(risk[ny,nx])
            ng=g+step
            if ng+1e-12<best.get(nxt,math.inf):
                best[nxt]=ng
                parent[nxt]=(x,y)
                heuristic=abs(nx-goal[0])+abs(ny-goal[1])
                heapq.heappush(pq,(ng+heuristic,ng,nxt))
    return None,len(expanded),math.inf

def validate_path(grid,path,start,goal):
    if path is None or path[0]!=start or path[-1]!=goal:
        return False
    return all(0<=x<grid.shape[1] and 0<=y<grid.shape[0] and not grid[y,x] for x,y in path) and all(
        abs(a[0]-b[0])+abs(a[1]-b[1])==1 for a,b in zip(path,path[1:])
    )

def empirical_cvar(values,alpha):
    if not 0<=alpha<1:
        raise ValueError("alpha outside [0,1)")
    x=np.asarray(values,dtype=float).ravel()
    if not len(x) or not np.isfinite(x).all():
        raise ValueError("Finite nonempty values required")
    # Exact upper-tail average with fractional boundary under the empirical distribution.
    x=np.sort(x)[::-1]
    count=(1-alpha)*len(x)
    whole=int(math.floor(count))
    fraction=count-whole
    weighted=float(np.sum(x[:whole]))
    if whole<len(x):
        weighted+=fraction*float(x[whole])
    return weighted/count

def evaluate(yaml_path,outdir,seed,n_tasks,risk_weight,decay_cells,alpha):
    import yaml
    yml=yaml_path.resolve()
    mapmeta=yaml.safe_load(yml.read_text())
    image=(yml.parent/mapmeta["image"]).resolve()
    ros_map=load_ros_map(yml,unknown_as_obstacle=True)
    grid=occupancy(ros_map)
    field=proximity_field(grid,decay_cells)
    pairs=sample_connected_pairs(grid,n_tasks,seed,min_distance=8)
    rows=[]
    for task_id,(start,goal) in enumerate(pairs):
        for method,weight in (("distance_only",0.),("additive_proximity_risk",risk_weight)):
            begin=time.perf_counter()
            path,expansions,objective=search(grid,start,goal,field,weight)
            elapsed_ms=(time.perf_counter()-begin)*1000
            if not validate_path(grid,path,start,goal):
                raise AssertionError(f"Invalid path: {task_id}, {method}")
            vals=np.asarray([field[y,x] for x,y in path[1:]])
            rows.append(dict(task=task_id,start_x=start[0],start_y=start[1],
                             goal_x=goal[0],goal_y=goal[1],method=method,
                             length_cells=len(path)-1,length_m=(len(path)-1)*ros_map.resolution,
                             expansions=expansions,objective=objective,
                             total_proximity_risk=float(vals.sum()),
                             mean_proximity_risk=float(vals.mean()),
                             cvar_proximity_risk=empirical_cvar(vals,alpha),
                             maximum_proximity_risk=float(vals.max()),
                             elapsed_ms=elapsed_ms,path_valid=True))
    outdir.mkdir(parents=True,exist_ok=True)
    with (outdir/"trials.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report=dict(evidence="actual_office_occupancy_map_with_generated_queries_and_analytic_proximity_risk",
                original_map_yaml_sha256=hashlib.sha256(yml.read_bytes()).hexdigest(),
                original_map_image_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
                map_dimensions=[int(grid.shape[1]),int(grid.shape[0])],
                resolution_m=ros_map.resolution,n_queries=n_tasks,random_seed=seed,
                risk_weight=risk_weight,risk_decay_cells=decay_cells,cvar_alpha=alpha,
                cvar_is_posthoc_metric_not_optimization_target=True,
                physical_robot_trials=0,
                original_dingo_actions_under_c03_control=False,
                claim_boundary="Measured real map geometry, but hazard field is deterministic obstacle-distance proxy; no calibrated probability, real localization, moving obstacles or physical robot execution.")
    (outdir/"summary.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2,sort_keys=True))
    print("C03 measured paired trials:",len(rows))
    return rows,report

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map_yaml",type=Path)
    parser.add_argument("--output-dir",type=Path,required=True)
    parser.add_argument("--seed",type=int,default=17)
    parser.add_argument("--n-tasks",type=int,default=5)
    parser.add_argument("--risk-weight",type=float,default=8.)
    parser.add_argument("--decay-cells",type=float,default=5.)
    parser.add_argument("--alpha",type=float,default=.9)
    args=parser.parse_args()
    evaluate(args.map_yaml,args.output_dir,args.seed,args.n_tasks,args.risk_weight,args.decay_cells,args.alpha)
if __name__=="__main__":
    main()
