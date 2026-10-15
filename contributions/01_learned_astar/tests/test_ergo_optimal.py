"""C01-ERGO regression tests; run pytest on this file."""
import importlib.util
from pathlib import Path
import random
from collections import deque
import numpy as np

FILE=Path(__file__).resolve().parents[1] / "code" / "ergo_optimal.py"
spec=importlib.util.spec_from_file_location("ergo_optimal",FILE)
import sys
mod=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=mod
spec.loader.exec_module(mod)

def bfs(grid,start,goal):
    q=deque([(start,0)]); seen={start}
    while q:
        n,d=q.popleft()
        if n==goal:return d
        for dx,dy in mod.NEIGHBORS:
            v=(n[0]+dx,n[1]+dy)
            if mod.valid(grid,v) and v not in seen:
                seen.add(v);q.append((v,d+1))
    return None

def test_random_optimality_and_budget():
    for seed in range(80):
        rng=random.Random(seed)
        grid=np.zeros((15,15),dtype=np.int8)
        for y in range(15):
            for x in range(15):
                if rng.random()<.28:grid[y,x]=1
        start,goal=(0,0),(14,14)
        grid[0,0]=grid[14,14]=0
        actual=mod.search(grid,start,goal,lambda n,g,grid: 1e6 if (n[0]+n[1])%2 else -1e6,budget=15)
        expected=bfs(grid,start,goal)
        assert (len(actual.path)-1 if actual.path else None)==expected
        assert actual.neural_calls<=15
        if actual.path:
            assert all(mod.valid(grid,n) for n in actual.path)

def test_cache_map_and_goal_separation():
    grid=np.zeros((9,9),dtype=np.int8)
    cache=mod.ExactMapCache()
    pred=lambda n,g,grid:float(n[0]+n[1]+g[0])
    a=mod.search(grid,(0,0),(8,8),pred,budget=1000,cache=cache)
    b=mod.search(grid,(0,0),(8,8),pred,budget=1000,cache=cache)
    assert a.neural_calls>0
    assert b.cache_hits>0
    assert b.neural_calls==0
    changed=grid.copy();changed[4,4]=1
    c=mod.search(changed,(0,0),(8,8),pred,budget=1000,cache=cache)
    assert c.neural_calls>0
    other_goal=mod.search(grid,(0,0),(8,7),pred,budget=1000,cache=cache)
    assert other_goal.neural_calls>0

def test_nonfinite_predictions_and_zero_budget():
    g=np.zeros((5,5),dtype=np.int8)
    for v in [float("nan"),float("inf"),float("-inf")]:
        r=mod.search(g,(0,0),(4,4),lambda *_:v,budget=10)
        assert len(r.path)-1==8
    r=mod.search(g,(0,0),(4,4),lambda *_: 5.,budget=0)
    assert r.neural_calls==0
