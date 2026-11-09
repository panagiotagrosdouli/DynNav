"""C02 three-way instance-disjoint calibration test contracts."""
from pathlib import Path
import importlib.util
import sys
import numpy as np
import pytest

SCRIPT=Path(__file__).resolve().parents[1]/"experiments"/"eval_three_way_group_coverage.py"
spec=importlib.util.spec_from_file_location("c02_three_way",SCRIPT)
m=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=m
spec.loader.exec_module(m)

def test_disjoint_fit_calibration_test_instances():
    groups=np.repeat(np.arange(30),5)
    masks,ids=m.grouped_partition(groups,17)
    assert all(mask.any() for mask in masks)
    assert np.all(sum(mask.astype(int) for mask in masks)==1)
    assert not (set(ids[0])&set(ids[1]) or set(ids[0])&set(ids[2]) or set(ids[1])&set(ids[2]))
    assert len(ids[0])==15 and len(ids[1])==7 and len(ids[2])==8

def test_finite_quantile_boundary():
    assert m.finite_sample_quantile(np.array([0,1,2,3,4,5,6,7,8]),.1)==8
    assert m.finite_sample_quantile(np.array([0,1,2,3]),.1)==float("inf")
    with pytest.raises(ValueError):
        m.finite_sample_quantile(np.array([0,float("nan")]),.1)

def test_evaluation_refuses_missing_group_independence():
    with pytest.raises(ValueError,match=">=5"):
        m.grouped_partition(np.array([1,1,2,2]),23)

def test_archive_gives_valid_heldout_map_metrics():
    source=Path(__file__).resolve().parents[1]/"results"/"uncertainty_error_data.csv"
    if not source.is_file():
        pytest.skip("Original data unavailable")
    result=m.evaluate(source,.1,[3,7])
    assert result["physical_robot_trials"]==0
    for trial in result["trials"]:
        for method in trial["methods"].values():
            assert 0<=method["empirical_state_coverage"]<=1
            assert method["n_test_states"]>0
            assert len(method["per_test_map_coverage"])>0
