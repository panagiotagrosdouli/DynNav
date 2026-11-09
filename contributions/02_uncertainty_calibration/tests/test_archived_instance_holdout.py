"""Regression checks for C02 archived map-level calibration split."""
import importlib.util
import sys
from pathlib import Path
import numpy as np
import pytest

DIR=Path(__file__).resolve().parents[1]
SCRIPT=DIR/"experiments"/"eval_archived_instance_holdout.py"
spec=importlib.util.spec_from_file_location("c02_archived_holdout",SCRIPT)
mod=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=mod
spec.loader.exec_module(mod)

def test_heldout_instance_ids_do_not_leak():
    groups=np.repeat(np.arange(30),10)
    mask, train_ids, test_ids=mod.separate_instances(groups,.6,123)
    assert set(train_ids).isdisjoint(set(test_ids))
    assert len(train_ids)==18
    assert len(test_ids)==12
    assert mask.sum()==180

def test_split_is_deterministic():
    groups=np.repeat(np.arange(20),5)
    assert mod.separate_instances(groups,.5,23)[1:]==mod.separate_instances(groups,.5,23)[1:]

def test_missing_or_invalid_rows_are_rejected(tmp_path):
    filename=tmp_path/"input.csv"
    filename.write_text("instance_id,mu,h_star,sigma\n" +
                        "".join(f"{i//10},0,1,-0.3\n" for i in range(30)))
    with pytest.raises(ValueError,match="sigma positive"):
        mod.load_archive(filename)

def test_true_archive_is_generated_not_physical():
    archive=DIR/"results"/"uncertainty_error_data.csv"
    if not archive.exists():
        pytest.skip("Archived C02 dataset unavailable")
    groups,pred,target,sigma=mod.load_archive(archive)
    assert len(groups)>1000
    assert len(set(groups))>1
    mask,train_ids,test_ids=mod.separate_instances(groups,.6,23)
    assert not set(train_ids)&set(test_ids)
    assert np.isfinite(sigma).all()
