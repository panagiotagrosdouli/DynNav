"""Regression tests for historical model API and the full C01 file auditor."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec=importlib.util.spec_from_file_location(name, path)
    obj=importlib.util.module_from_spec(spec)
    sys.modules[name]=obj
    spec.loader.exec_module(obj)
    return obj


def test_legacy_hidden_alias_controls_actual_network_width():
    torch = pytest.importorskip("torch")
    code = ROOT / "code"
    sys.path.insert(0, str(code))
    try:
        m=load("c01_heuristic_hidden_contract",code/"learned_heuristic.py")
    finally:
        sys.path.remove(str(code))
    for hidden in (32, 64, 128):
        net=m.HeuristicNet(in_dim=4,hidden=hidden)
        assert net.net[0].weight.shape == (hidden,4)
        assert net.net[2].weight.shape == (hidden,hidden)
        assert net(torch.zeros(4)).shape == (1,1)
    with pytest.raises(ValueError,match="Conflicting"):
        m.HeuristicNet(in_dim=4,hidden=32,hidden_dim=128)


def test_every_created_audit_record_is_honestly_classified(tmp_path):
    pytest.importorskip("numpy")
    pytest.importorskip("PIL")
    path=ROOT/"experiments"/"audit_all_c01_files.py"
    a=load("c01_all_file_audit_under_test",path)
    sample=tmp_path/"code"
    sample.mkdir()
    (sample/"valid.py").write_text("x = 1\n")
    (sample/"broken.py").write_text("def oops(\n")
    (tmp_path/"README.md").write_text("not proof of robot motion")
    result=a.audit(tmp_path,tmp_path/"artifacts"/"audit.json")
    assert result["status_counts"]["FAILED"]==1
    records={x["file"]:x for x in result["files"]}
    assert records["code/valid.py"]["status"]=="SOURCE_COMPILES_RUNTIME_NOT_FULLY_EXECUTED"
    assert records["code/broken.py"]["status"]=="FAILED"
    assert (tmp_path/"artifacts"/"audit.json").is_file()
    assert result["not_proven"]


def test_exact_checkpoint_width_and_finite_parameters():
    torch=pytest.importorskip("torch")
    path=ROOT/"models"/"heuristic_net_rich.pt"
    state=torch.load(path,map_location="cpu",weights_only=True)
    assert state["net.0.weight"].shape[1]==11
    assert all(torch.isfinite(v).all() for v in state.values())
