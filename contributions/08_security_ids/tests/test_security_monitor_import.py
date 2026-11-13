"""C08 regression test for usable existing sequential IDS source import and response."""
import importlib.util
import sys
from pathlib import Path
import numpy as np

MODULE=Path(__file__).resolve().parents[1]/"code"/"security_monitor_cusum.py"
spec=importlib.util.spec_from_file_location("c08_security_monitor_cusum_runtime",MODULE)
m=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=m
spec.loader.exec_module(m)

def test_original_monitor_imports_actual_sequential_ids_and_detects_large_nis():
    mon=m.SecurityMonitorCUSUM(sensors=["wheel"],
        cusum_cfg=m.CUSUMConfig(k=1.0,h=5.0))
    x=mon.update_from_nis("wheel",10.0)
    assert x.alarm
    assert x.cusum>=5
    mon.reset("wheel")
    y=mon.update_from_innovation("wheel",np.array([1.0]),np.array([[1.0]]))
    assert y.nis==1.0 and not y.alarm

def test_unknown_sensor_fails_instead_of_silent_substitution():
    mon=m.SecurityMonitorCUSUM(sensors=["wheel"])
    try:
        mon.update_from_nis("vo",2)
    except KeyError:
        return
    raise AssertionError("Unknown stream should not silently fall back to wheel")
