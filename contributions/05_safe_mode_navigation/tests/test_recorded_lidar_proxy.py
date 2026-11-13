"""C05 real LaserScan proximity-proxy interpretation test contracts."""
import importlib.util,sys
from pathlib import Path
import numpy as np
import pytest

SCRIPT=Path(__file__).resolve().parents[1]/"experiments"/"eval_recorded_dingo_lidar_safe_mode.py"
spec=importlib.util.spec_from_file_location("c05_dingo_replay",SCRIPT)
mod=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=mod
spec.loader.exec_module(mod)

def test_physically_close_valid_laser_ranges_produce_critical_proxy():
    risk,p10=mod.proximity_proxy([.2,.3,.4,.5]*10,.1,30.)
    assert risk>0.95
    assert p10<.5

def test_clear_scans_produce_low_proxy():
    risk,p10=mod.proximity_proxy([5.,4.,3.,float("inf")]*10,.05,30.)
    assert risk==0
    assert p10>=3

def test_missing_valid_lasers_trigger_critical_stop():
    risk,p10=mod.proximity_proxy([float("nan"),float("inf"),-.5],.1,20.)
    assert risk==1.0 and p10 is None
    out=mod.SafeModeController().update(risk)
    assert out.emergency_stop and out.speed_scale==0

def test_proxy_is_finite_and_normalized():
    for distance in np.linspace(.1,10,100):
        risk,p10=mod.proximity_proxy([distance]*8,.1,30.)
        assert 0<=risk<=1
