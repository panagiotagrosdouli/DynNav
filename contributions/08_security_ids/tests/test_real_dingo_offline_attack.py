"""C08 real-recording IDS numerical and fail-closed evidence tests."""
import importlib.util
import sys
from pathlib import Path
import numpy as np
import pytest

FILE=Path(__file__).resolve().parents[1]/"experiments"/"eval_real_dingo_odometry_synthetic_attack.py"
spec=importlib.util.spec_from_file_location("c08_real_recording_attack",FILE)
module=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=module
spec.loader.exec_module(module)

def test_nonmonotonic_and_discontinuity_steps_discarded():
    t=np.arange(180,dtype=float)*.1
    x=np.arange(180,dtype=float)*.02
    a=np.column_stack([t,x,np.zeros_like(x)])
    a[45,0]=a[44,0]
    a[80,1]=100
    time,speed,rejected=module.velocity_samples(a)
    assert rejected>=2
    assert np.isfinite(speed).all() and np.all(speed>=0)
    assert len(speed)>=100

def test_injected_detection_is_explicitly_synthetic():
    rng=np.random.default_rng(5)
    # Deliberately nonzero baseline motion, no physical sensor claimed.
    t=np.arange(1100,dtype=float)*.1
    vx=.2+.02*np.sin(np.arange(1100)/17.)
    x=np.cumsum(vx)*.1
    a=np.column_stack([t,x,np.zeros_like(x)])
    result=module.evaluate_odometry(a,attack_speed_m_s=1.)
    assert result["attack_is_synthetic_in_memory"]
    assert not result["physical_robot_c08_control"]
    assert result["physical_robot_trials"]==0
    assert result["baseline_fit_samples"]>100
    assert result["heldout_test_samples"]>100

def test_adversarial_parameter_rejected():
    t=np.arange(300,dtype=float)*.1
    x=np.arange(300,dtype=float)*.01
    with pytest.raises(ValueError):
        module.evaluate_odometry(np.column_stack([t,x,np.zeros_like(x)]),attack_speed_m_s=-1)

def test_no_independent_original_ground_truth_claim():
    source=FILE.read_text(encoding="utf-8")
    assert '"no_attack_ground_truth_assumed":False' in source
    assert '"physical_robot_trials":0' in source
