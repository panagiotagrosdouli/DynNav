"""Paired ERGO pilot: exact-map caching / budgets, NOT a full research validation.

Run: python contributions/01_learned_astar/experiments/ergo_pilot.py --episodes 40
For real neural runs set --model to an existing C01 checkpoint. Never silently fall back.
"""
import argparse,csv,hashlib,importlib.util,json,platform,random,sys,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"code"))
from ergo_optimal import search,ExactMapCache

def load_model(path):
    import torch
    from learned_heuristic import HeuristicNet
    if not path.is_file():
        raise FileNotFoundError(f"Explicit learned checkpoint unavailable: {path}")
    model=HeuristicNet(input_dim=11)
    try: state=torch.load(path,map_location="cpu",weights_only=True)
    except TypeError: state=torch.load(path,map_location="cpu")
    model.load_state_dict(state);model.eval()
    from importlib.util import spec_from_file_location,module_from_spec
    spec=spec_from_file_location("c01_reference",ROOT/"experiments"/"astar_learned_heuristic.py")
    m=module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
    wrapper=m.LearnedHeuristicWrapper(model_path=path,mode="raw",allow_missing_model=False)
    assert wrapper.model is not None
    return wrapper.h,hashlib.sha256(path.read_bytes()).hexdigest()

def make_grid(rng,size,density):
    g=(np.array([rng.random() for _ in range(size*size)]).reshape(size,size)<density).astype(np.int8)
    g[0,:]=0;g[:,0]=0;g[-1,:]=0;g[:,-1]=0
    return g

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--episodes",type=int,default=40)
    p.add_argument("--size",type=int,default=40)
    p.add_argument("--density",type=float,default=.2)
    p.add_argument("--seed",type=int,default=123)
    p.add_argument("--model",type=Path)
    p.add_argument("--out",type=Path,default=Path("results/c01_ergo_pilot"))
    a=p.parse_args()
    if a.episodes<=0 or not 0<=a.density<1:raise ValueError("bad episodes/density")
    prediction,checkpoint=(load_model(a.model) if a.model else (lambda n,g,grid:float(abs(n[0]-g[0])+abs(n[1]-g[1])),"synthetic_manhattan_proxy_NOT_NEURAL"))
    a.out.mkdir(parents=True,exist_ok=True)
    rng=random.Random(a.seed)
    cache=ExactMapCache()
    rows=[]
    for episode in range(a.episodes):
        g=make_grid(rng,a.size,a.density)
        start=(0,0);goal=(a.size-1,a.size-1)
        # repeat identical query and then change a map cell to exercise invalidation
        for variant,grid in [("original",g),("repeated",g),("changed",g.copy())]:
            if variant=="changed":grid[a.size//2,a.size//2]=1-int(grid[a.size//2,a.size//2])
            for budget in [0,8,32,128]:
                r=search(grid,start,goal,prediction,budget=budget,cache=cache)
                row=dict(episode=episode,variant=variant,budget=budget,success=int(r.path is not None),path_cost=len(r.path)-1 if r.path else None,expansions=r.expansions,neural_calls=r.neural_calls,cache_hits=r.cache_hits,neural_ms=1000*r.neural_seconds,total_ms=1000*r.total_seconds)
                rows.append(row)
    out=a.out/"trials.csv"
    with out.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    meta=dict(seed=a.seed,episodes=a.episodes,size=a.size,density=a.density,checkpoint_sha256=checkpoint,python=sys.version,numpy=np.__version__,platform=platform.platform(),timestamp_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),method="Manhattan primary priority; neural secondary tie-break; exact full-grid cache")
    (a.out/"manifest.json").write_text(json.dumps(meta,indent=2)+"\n")
    print("Wrote",out,len(rows),"rows; model:",checkpoint)
if __name__=="__main__":main()
