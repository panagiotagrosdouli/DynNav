"""C13 actual recorded-action model input alignment and chronological split contracts."""
import importlib.util
import sys
from pathlib import Path
import numpy as np
import pytest

S=Path(__file__).resolve().parents[1]/"experiments"/"train_real_dingo_action_dynamics.py"
spec=importlib.util.spec_from_file_location("c13_real_dynamics",S)
m=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=m
spec.loader.exec_module(m)

def test_body_motion_rotation_and_yaw_wrap():
    a=(0.,0.,0.,np.pi/2)
    b=(.1,0.,1.,-np.pi/2)
    dx,dy,dtheta,dt=m.body_step(a,b)
    assert dx==pytest.approx(1.)
    assert dy==pytest.approx(0.,abs=1e-12)
    assert abs(dtheta)==pytest.approx(np.pi)
    assert dt==pytest.approx(.1)

def test_aligned_command_never_leaks_future_command():
    odom=[(.05,0.,0.,0.),(.15,.01,0.,0.),(.25,.02,0.,0.),(.35,.03,0.,0.)]
    commands=[(.00,.10,.00),(.20,.90,.00),(.4,10.,0.)]
    # Too few steps for a full real training run, but alignment itself should
    # reject as underpowered; replicate physically realistic intervals instead.
    full_odom=[(i*.1,i*.01,0.,0.) for i in range(250)]
    full_cmd=[(i*.1-.05,.10 if i<125 else .40,.0) for i in range(250)]
    rows=m.aligned_steps(full_odom,full_cmd)
    assert rows[0,3]==pytest.approx(.10)
    assert rows[50,3]==pytest.approx(.10)
    assert rows[200,3]==pytest.approx(.40)

def test_chronological_split_excludes_history_overlap_and_test_fit():
    data=np.arange(200*6,dtype=np.float32).reshape(200,6)
    splits,regions=m.strict_block_windows(data,window=8)
    assert regions["train"]==(0,130)
    assert regions["validation"]==(130,160)
    assert regions["test"]==(160,200)
    for key in splits:
        X,A,Y=splits[key]
        assert len(X)==len(Y)==len(A)
        assert X.shape[1:]==(8,6)
    assert splits["train"][2][-1,0] < splits["validation"][0][0,0,0]
    assert splits["validation"][2][-1,0] < splits["test"][0][0,0,0]

def test_normalization_only_from_train_and_not_heldout_outliers():
    data=np.ones((200,6),dtype=np.float32)
    data[0:130,:]=np.arange(130,dtype=np.float32)[:,None]
    data[160:,:]=1000000
    splits,_=m.strict_block_windows(data,8)
    xm,xs,am,astd,ym,ys=m.fit_statistics(splits)
    assert np.max(xm)<130
    assert np.max(ym)<130
    assert np.all(xs>0)
    assert np.all(ys>0)

def test_short_sequence_fails_closed():
    with pytest.raises(ValueError):
        m.strict_block_windows(np.zeros((10,6)),window=8)
