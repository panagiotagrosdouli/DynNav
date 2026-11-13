"""C02-C26 exhaustive audit invariants; no robotics hardware needed."""
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/"scripts"/"audit_contributions_c02_c26.py"
spec=importlib.util.spec_from_file_location("contributions_c02_c26_auditor",MODULE)
audit=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=audit
spec.loader.exec_module(audit)

def test_c07_has_two_histories_and_is_one_registry_entry():
    dirs=audit.inventory(ROOT)
    assert len(dirs)==25
    assert len(dirs["C07"])==2
    assert all(len(dirs[f"C{n:02d}"])>=1 for n in range(2,27))

def test_corrupted_python_file_is_fail_not_skipped(tmp_path):
    bad=tmp_path/"broken.py"
    bad.write_text("def broken(\n",encoding="utf-8")
    result=audit.inspect_file(bad,tmp_path)
    assert result["status"]=="FAILED"
    assert result.get("error")

def test_csv_is_read_and_checked_not_called_scientific_proof(tmp_path):
    csv=tmp_path/"data.csv"
    csv.write_text("prediction,target,sigma\n1,2,0.1\n",encoding="utf-8")
    result=audit.inspect_file(csv,tmp_path)
    assert result["status"]=="CSV_STRUCTURALLY_VALID"
    assert result["rows"]==1

def test_missing_registered_contribution_is_rejected(tmp_path):
    (tmp_path/"contributions").mkdir()
    with pytest.raises(FileNotFoundError):
        audit.inventory(tmp_path)

def test_failed_npz_array_rejected(tmp_path):
    import numpy as np
    path=tmp_path/"bad.npz"
    np.savez(path,values=np.array([0.0,float("nan")]))
    result=audit.inspect_file(path,tmp_path)
    assert result["status"]=="FAILED"

def test_nested_real_checkpoint_metadata_and_weights_are_checked():
    torch=pytest.importorskip("torch")
    path=ROOT/"contributions"/"02_uncertainty_calibration"/"models"/"drift_uncertainty_net.pt"
    result=audit.inspect_file(path,ROOT,torch)
    assert result["status"]=="PT_TENSORS_AND_METADATA_VALID",result
    assert "model_state_dict" in result["checkpoint_schema"]
    assert "feature_cols" in result["checkpoint_schema"]

def test_nested_nonfinite_tensor_rejected():
    torch=pytest.importorskip("torch")
    with pytest.raises(ValueError,match="Nonfinite"):
        audit.inspect_checkpoint_payload({"model_state_dict":{"bad":torch.tensor([float("nan")])}},torch)
