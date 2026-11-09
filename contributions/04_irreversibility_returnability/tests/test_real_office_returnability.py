"""C04 real-map minimum feasible threshold and geometric returnability tests."""
import importlib.util
import sys
from pathlib import Path
import numpy as np
import pytest

pytest.importorskip("scipy")
SCRIPT=Path(__file__).resolve().parents[1]/"experiments"/"eval_real_office_returnability.py"
spec=importlib.util.spec_from_file_location("c04_real_returnability",SCRIPT)
module=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=module
spec.loader.exec_module(module)

def test_static_return_distances_and_disconnected_area():
    grid=np.zeros((7,9),dtype=np.uint8)
    grid[:,4]=1
    dist=module.return_distances(grid==0,(1,1))
    assert dist[1,1]==0
    assert dist[2,2]==2
    assert dist[1,7]==-1
    score,reach=module.geometric_fragility(grid,dist)
    assert np.all(score[~reach]==1)
    assert np.all((score[reach]>=0)&(score[reach]<=1))

def test_exact_minimax_threshold_uses_better_clear_route():
    free=np.ones((4,5),dtype=bool)
    I=np.ones((4,5),dtype=float)*.8
    I[0,:]=.2
    I[:,0]=.2
    I[:,4]=.2
    assert module.minimum_feasible_tau(free,I,(0,0),(4,0))==pytest.approx(.2)
    I[0,2]=.9
    # Take a lower loop with cost .8, avoiding a .9 obstacle.
    assert module.minimum_feasible_tau(free,I,(0,0),(4,0))==pytest.approx(.8)

def test_end_to_end_constrained_route_is_not_longer_than_the_shortest_baseline_when_unconstrained():
    grid=np.zeros((8,9),dtype=np.uint8)
    grid[4,1:8]=1
    grid[4,5]=0
    base=(0,0);goal=(8,7)
    d=module.return_distances(grid==0,base)
    I,reachable=module.geometric_fragility(grid,d)
    shortest,_,_=module.search(grid,base,goal,I,0)
    min_tau=module.minimum_feasible_tau(reachable,I,base,goal)
    original=module.astar_irreversibility_constrained(reachable,I,(base[1],base[0]),(goal[1],goal[0]),tau=1.0)
    assert original.success
    assert len(original.path)==len(shortest)
    restricted=module.astar_irreversibility_constrained(reachable,I,(base[1],base[0]),(goal[1],goal[0]),tau=min(1,min_tau+1e-9))
    assert restricted.success
    assert len(restricted.path)>=len(shortest)

def test_invalid_base_fails_closed():
    grid=np.ones((3,3),dtype=bool)
    grid[0,0]=False
    with pytest.raises(ValueError):
        module.return_distances(grid,(0,0))
