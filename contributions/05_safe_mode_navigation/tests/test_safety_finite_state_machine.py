"""C05 invalid-input stop and finite-state transition invariants."""
import math,sys
from pathlib import Path
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"code"))
from safe_mode_controller import SafeModeConfig,SafeModeController,SafeModeState

@pytest.mark.parametrize("bad",[float("nan"),float("inf"),float("-inf"),-0.1,1.001])
def test_invalid_risk_cannot_continue_normal_navigation(bad):
    c=SafeModeController()
    assert c.update(.1).state==SafeModeState.NORMAL
    output=c.update(bad)
    assert output.state==SafeModeState.EMERGENCY_STOP
    assert output.speed_scale==0
    assert output.alert_operator and output.emergency_stop
    assert output.risk==1.0
    assert output.transition=="INVALID_RISK->EMERGENCY_STOP"

@pytest.mark.parametrize("params",[
    {"normal_speed":0.2,"safe_speed":.4},
    {"risk_off_threshold":.8,"risk_on_threshold":.7},
    {"safe_inflation_radius":.4,"normal_inflation_radius":1.0},
    {"risk_on_threshold":float("nan")},
    {"critical_threshold":1.1},
])
def test_unsafe_configs_rejected(params):
    with pytest.raises(ValueError):
        SafeModeConfig(**params)

def test_hysteresis_persistence_and_emergency_recovery():
    c=SafeModeController()
    assert c.update(.75).state==SafeModeState.NORMAL
    assert c.update(.75).state==SafeModeState.SAFE_MODE
    assert c.update(.5).state==SafeModeState.SAFE_MODE
    assert c.update(.96).state==SafeModeState.EMERGENCY_STOP
    assert c.update(.2).state==SafeModeState.EMERGENCY_STOP
    assert c.update(.2).state==SafeModeState.EMERGENCY_STOP
    out=c.update(.2)
    assert out.state==SafeModeState.SAFE_MODE and out.should_replan
    assert not out.emergency_stop
    assert c.update(.2).state==SafeModeState.SAFE_MODE
    assert c.update(.2).state==SafeModeState.SAFE_MODE
    assert c.update(.2).state==SafeModeState.NORMAL
