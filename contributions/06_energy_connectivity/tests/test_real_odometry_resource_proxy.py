"""C06 odometry validation and no invented battery/connectivity tests."""
import importlib.util,sys
from pathlib import Path
import pytest

SRC=Path(__file__).resolve().parents[1]/"experiments"/"eval_real_dingo_odometry_resources.py"
spec=importlib.util.spec_from_file_location("c06_actual_odom",SRC)
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)

def test_actual_xy_translation_integrated_and_invalid_jumps_rejected():
    rows=[(0.,0.,0.),(1.,.3,.4),(2.,.6,.8),(3.,20.,20.),(4.,20.3,20.4)]
    result=m.integrate_deltas(rows,max_step_m=2.)
    assert result["accepted_steps"]==3
    assert result["rejected_steps"]==1
    assert result["observed_planar_odometry_distance_m"]==pytest.approx(1.5)

def test_invalid_and_nonmonotonic_samples_not_counted():
    rows=[(1.,0.,0.),(2.,float("nan"),0.),(.5,.3,.4),(3.,.6,.8)]
    result=m.integrate_deltas(rows,max_step_m=2.)
    assert result["rejected_steps"]>=2

def test_no_valid_motion_is_not_fake_success():
    with pytest.raises(ValueError):
        m.integrate_deltas([(0.,0.,0.),(1.,100.,100.)],max_step_m=2.)

def test_negative_step_threshold_rejected():
    with pytest.raises(ValueError):
        m.integrate_deltas([(0,0,0),(1,1,1)],max_step_m=-.1)
