"""C08 sensitivity sweep: no fabricated attacks or physical-robot conclusions."""
import importlib.util
import sys
from pathlib import Path
import numpy as np

DIR=Path(__file__).resolve().parents[1]/"experiments"
for p in (DIR,):
    if str(p) not in sys.path:
        sys.path.insert(0,str(p))
SOURCE=DIR/"eval_dingo_injection_sensitivity.py"
spec=importlib.util.spec_from_file_location("c08_counterfactual_sensitivity",SOURCE)
m=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=m
spec.loader.exec_module(m)

def test_five_bias_sizes_remain_offline_counterfactuals():
    from eval_real_dingo_odometry_synthetic_attack import evaluate_odometry
    times=np.arange(1300,dtype=float)*.1
    velocities=.2+.025*np.sin(np.arange(1300,dtype=float)/13)
    distances=np.cumsum(velocities)*.1
    odom=np.column_stack((times,distances,np.zeros_like(times)))
    for bias in (.1,.2,.35,.5,1.):
        report=evaluate_odometry(odom,attack_speed_m_s=bias)
        assert report["real_telemetry_base"] is True
        assert report["attack_is_synthetic_in_memory"] is True
        assert report["physical_robot_trials"]==0
        assert report["no_attack_ground_truth_assumed"] is False
        assert report["heldout_test_samples"]>100
