"""C18 actual instantaneous CBF half-space feasibility regression suite.

Numerical QP feasibility is NOT a formal real robot safety certificate.
"""
import sys
from pathlib import Path
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from formal_safety_shields import CBFSafetyFilter,CBFConfig

def test_single_obstacle_exact_halfspace_projection():
    f=CBFSafetyFilter(CBFConfig(safety_radius=.4,alpha=1.5))
    u,info=f.filter_verified(np.array([2.,0.]),np.zeros(2),[np.array([1.,0.])])
    assert info["constraint_feasible"] is True
    assert u[0] == pytest.approx(.9,abs=1e-7)
    assert u[1] == pytest.approx(0.)
    assert info["minimum_cbf_margin"]>=-1e-8

def test_multiple_constraints_no_partial_unsafe_projection():
    f=CBFSafetyFilter()
    u,info=f.filter_verified(np.array([3.,3.]),np.zeros(2),
                             [np.array([1.,0.]),np.array([0.,1.])])
    assert info["constraint_feasible"]
    assert u[0]<=f.cfg.alpha*(1-f.cfg.safety_radius)+1e-8
    assert u[1]<=f.cfg.alpha*(1-f.cfg.safety_radius)+1e-8
    assert info["minimum_cbf_margin"]>=-1e-8

def test_unsafe_infeasible_pair_explicitly_fails_closed():
    f=CBFSafetyFilter(CBFConfig(safety_radius=.4,alpha=1.5))
    u,info=f.filter_verified(np.array([1.,0.]),np.zeros(2),
                             [np.array([.1,0.]),np.array([-.1,0.])])
    assert info["constraint_feasible"] is False
    assert "NOT_CERTIFIED" in info["status"]
    assert np.array_equal(u,np.zeros(2))
    filtered,report=f.batch_filter(np.array([1.,0.]),np.zeros(2),
                                  [np.array([.1,0.]),np.array([-.1,0.])])
    assert report["constraint_feasible"] is False
    assert report["safety_violated"] is True

def test_invalid_nonfinite_states_and_obstacles_rejected():
    f=CBFSafetyFilter()
    with pytest.raises(ValueError):f.filter_verified(np.array([np.nan,0]),np.zeros(2),[])
    with pytest.raises(ValueError):f.filter_verified(np.zeros(2),np.zeros(2),[np.array([np.inf,0])])
    with pytest.raises(ValueError):f.filter_verified(np.zeros(3),np.zeros(2),[])

def test_feasible_random_cases_satisfy_every_instantaneous_inequality():
    f=CBFSafetyFilter()
    rng=np.random.default_rng(2026)
    for _ in range(100):
        angles=rng.uniform(0,2*np.pi,size=4)
        radii=rng.uniform(.6,1.5,size=4)
        obstacles=[r*np.array([np.cos(a),np.sin(a)]) for r,a in zip(radii,angles)]
        u,info=f.filter_verified(rng.normal(size=2),np.zeros(2),obstacles)
        assert info["constraint_feasible"]
        for obs in obstacles:
            assert f.dh_dx(np.zeros(2),obs)@u+f.cfg.alpha*f.h(np.zeros(2),obs)>=-1e-7
