"""C03 real-map risk-A* research and CVaR mathematical regression contracts."""
import importlib.util
import sys
from pathlib import Path
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[3]
SRC=Path(__file__).resolve().parents[1]/"experiments"/"eval_real_map_proximity_risk.py"
spec=importlib.util.spec_from_file_location("c03_real_risk",SRC)
m=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=m
spec.loader.exec_module(m)

def test_precise_empirical_upper_tail_cvar_fractional_boundary():
    assert m.empirical_cvar([1,2,3,4],.5)==pytest.approx(3.5)
    # Worst 37.5% probability mass: one entire worst sample + half next
    assert m.empirical_cvar([1,2,3,4],.625)==pytest.approx((4+.5*3)/1.5)
    with pytest.raises(ValueError):
        m.empirical_cvar([1],1.0)

def test_risk_aware_optimal_for_cost_and_original_endpoints():
    g=np.zeros((9,9),dtype=np.uint8)
    g[4,2:7]=1
    g[4,4]=0
    start,goal=(0,0),(8,8)
    risk=m.proximity_field(g,decay_cells=3)
    base,_,_ = m.search(g,start,goal,risk,0)
    aware,_,weighted=m.search(g,start,goal,risk,20)
    assert m.validate_path(g,base,start,goal)
    assert m.validate_path(g,aware,start,goal)
    base_weighted=sum(1+20*risk[y,x] for x,y in base[1:])
    assert weighted <= base_weighted+1e-7

def test_all_obstacles_rejected_and_paths_cannot_move_diagonally():
    with pytest.raises(ValueError):
        m.proximity_field(np.ones((3,3),dtype=np.uint8))
    grid=np.array([[0,1,0],[0,1,0],[0,1,0]],dtype=np.uint8)
    path,_,_=m.search(grid,(0,0),(0,2),m.proximity_field(grid),5)
    assert m.validate_path(grid,path,(0,0),(0,2))
    path,_,_=m.search(grid,(0,0),(2,0),m.proximity_field(grid),5)
    assert path is None

def test_connected_query_sampler_produces_valid_reachable_pairs():
    g=np.zeros((12,12),dtype=np.uint8)
    g[5,:11]=1
    tasks=m.sample_connected_pairs(g,3,seed=12,min_distance=8)
    assert len(tasks)==3
    assert all(abs(s[0]-t[0])+abs(s[1]-t[1])>=8 for s,t in tasks)
