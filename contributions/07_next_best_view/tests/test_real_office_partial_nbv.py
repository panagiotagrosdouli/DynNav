"""Regression tests for C07 actual map geometry + synthetic visibility boundaries."""
import importlib.util
import sys
from pathlib import Path
import numpy as np
import pytest

pytest.importorskip("scipy")
FILE=Path(__file__).resolve().parents[1]/"experiments"/"eval_real_office_partial_observation_nbv.py"
spec=importlib.util.spec_from_file_location("c07_real_office_partial_nbv",FILE)
m=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=m
spec.loader.exec_module(m)

def test_observed_grid_never_reveals_cell_outside_radius():
    grid=np.zeros((70,70),dtype=np.uint8)
    grid[35,30]=1
    known,obstacles,free=m.generate_observed(grid,(35,35),10)
    assert known[35,35]
    assert known[35,30] and obstacles[35,30] and not free[35,30]
    assert not known[35,46]
    assert not obstacles[35,46] and not free[35,46]

def test_connected_frontiers_and_score_independent_of_unobserved_truth():
    grid=np.zeros((70,70),dtype=np.uint8)
    for x in (15,50):
        grid[35,x]=1
    base=(35,35)
    known,occ,free=m.generate_observed(grid,base,12)
    distance=m.known_distances(free,base)
    candidates,metadata=m.frontier_candidates(known,free,distance,occ,base,7,sample_max=35,seed=7)
    assert len(candidates)>3
    assert all(metadata[c.name]["known_geometric_return_to_base"] for c in candidates)
    assert all(c.information_gain>0 and c.travel_cost>=1 for c in candidates)
    # Alter the hidden occupancy map outside the observation circle.
    grid[~known]=1
    k2,o2,f2=m.generate_observed(grid,base,12)
    d2=m.known_distances(f2,base)
    c2,meta2=m.frontier_candidates(k2,f2,d2,o2,base,7,sample_max=35,seed=7)
    assert candidates==c2 and metadata==meta2

def test_blocked_base_fails_closed():
    grid=np.zeros((20,20),dtype=np.uint8)
    grid[10,10]=1
    known,obs,free=m.generate_observed(grid,(10,10),6)
    with pytest.raises(ValueError):
        m.known_distances(free,(10,10))
