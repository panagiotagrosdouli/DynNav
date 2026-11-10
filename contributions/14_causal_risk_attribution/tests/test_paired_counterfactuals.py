"""C14 causal intervention pairing, numerical sign and fail-closed contracts."""
import importlib.util
import sys
from pathlib import Path
import pytest

SCRIPT=Path(__file__).resolve().parents[1]/"experiments"/"eval_paired_counterfactuals.py"
spec=importlib.util.spec_from_file_location("c14_paired_counterfactuals",SCRIPT)
m=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=m
spec.loader.exec_module(m)

def test_noise_is_identical_in_both_factual_and_intervention():
    scm=m.NavigationSCM()
    noise={"sensor_noise":1.3,"localization_error":.2,"path_risk":.4}
    fact,ranked=m.paired_effects(scm,noise)
    for cause,value in m.NEUTRAL.items():
        actual=fact["collision"]-scm.counterfactual_query(noise,{cause:value})["collision"]
        assert dict(ranked)[cause]==pytest.approx(actual,abs=1e-12)

def test_neutral_repairs_use_domain_valid_map_and_detection_baselines():
    assert m.NEUTRAL["map_accuracy"]==1
    assert m.NEUTRAL["obstacle_detection"]==1
    assert m.NEUTRAL["localization_error"]==0

def test_finite_input_and_unknown_variables_are_rejected():
    scm=m.NavigationSCM()
    with pytest.raises(ValueError):
        m.paired_effects(scm,{"sensor_noise":float("nan")})
    with pytest.raises(ValueError):
        m.paired_effects(scm,{"unknown":1})
    with pytest.raises(ValueError):
        m.factorial_ground_truth(scm,0,10,root="unknown")

def test_reproducible_injection_benchmark(tmp_path):
    a=m.run(tmp_path/"first",2026,50)
    b=m.run(tmp_path/"second",2026,50)
    assert a==b
    assert a["physical_robot_trials"]==0
    assert 0<=a["overall_top1_accuracy"]<=1
    assert sum(v["n"] for v in a["per_cause"].values())==50
    assert (tmp_path/"first"/"counterfactual_trials.csv").is_file()
