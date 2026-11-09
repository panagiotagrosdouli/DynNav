"""C04 SafeMode precise endpoint and malformed input fail-closed tests."""
import sys
from pathlib import Path
import numpy as np
import pytest

CODE=Path(__file__).resolve().parents[1]/"code"
sys.path.insert(0,str(CODE))
from irreversibility_safe_mode import SafeModeConfig,run_irreversibility_with_safe_mode

def test_tau_max_is_checked_even_if_step_does_not_land_on_it():
    free=np.ones((1,4),dtype=bool)
    I=np.array([[0.0,.15,.55,.2]])
    d=run_irreversibility_with_safe_mode(
        free,I,(0,0),(0,3),tau0=.1,
        cfg=SafeModeConfig(tau_max=.55,tau_step=.2,max_tau_gap=.5))
    assert d.success
    assert d.mode=="SAFE_RELAX_TAU"
    assert d.tau_used==pytest.approx(.55)
    assert d.max_I_on_path==pytest.approx(.55)

def test_gap_guard_stops_when_relaxation_is_excessive():
    free=np.ones((1,3),dtype=bool)
    I=np.array([[.05,.8,.05]])
    d=run_irreversibility_with_safe_mode(
        free,I,(0,0),(0,2),tau0=.1,
        cfg=SafeModeConfig(tau_max=1,tau_step=.1,max_tau_gap=.2))
    assert not d.success and d.mode=="SAFE_STOP"

@pytest.mark.parametrize("tau",[-.01,1.01,float("nan")])
def test_invalid_requested_tau_rejected(tau):
    with pytest.raises(ValueError):
        run_irreversibility_with_safe_mode(np.ones((2,2),bool),np.zeros((2,2)),(0,0),(1,1),tau)

def test_nonfinite_or_mismatched_irreversibility_is_rejected():
    with pytest.raises(ValueError):
        run_irreversibility_with_safe_mode(np.ones((2,2),bool),np.array([[0.,np.nan],[0,0]]),(0,0),(1,1),.5)
    with pytest.raises(ValueError):
        run_irreversibility_with_safe_mode(np.ones((2,3),bool),np.zeros((2,2)),(0,0),(1,1),.5)
