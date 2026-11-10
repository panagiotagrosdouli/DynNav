"""C16 actual-Dingo pseudo-federation numerical and evidence invariants."""
import importlib.util
import sys
from pathlib import Path
import numpy as np
import pytest

SCRIPT=Path(__file__).resolve().parents[1]/"experiments"/"eval_real_dingo_pseudoclient_fedavg.py"
spec=importlib.util.spec_from_file_location("c16_real_dingo_pseudo_fed",SCRIPT)
m=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=m
spec.loader.exec_module(m)

def example_data(n=300):
    rng=np.random.default_rng(55)
    v=rng.normal(size=n)*.15
    w=rng.normal(size=n)*.08
    dt=np.full(n,.07)
    seq=np.column_stack((v*dt,np.zeros(n),w*dt,v,w,dt))
    return seq

def test_independent_chronological_partitions_and_pseudo_client_labels():
    seq=example_data()
    clients,val,test=m.temporal_partition(seq,6)
    assert len(clients)==6
    assert clients[-1][-1]<val[0]
    assert val[-1]<test[0]
    assert sum(len(x) for x in clients)+len(val)+len(test)==len(seq)

def test_weighted_fedavg_runs_with_actual_federated_server_aggregation():
    seq=example_data()
    X,Y=m.features_and_targets(seq)
    clients,val,test=m.temporal_partition(seq,6)
    Xn,Yn,norm=m.standardize_training_only(X,Y,np.concatenate(clients))
    trained=m.offline_fedavg(Xn,Yn,clients,rounds=10)
    assert trained["W"].shape==(3,3)
    assert np.isfinite(trained["W"]).all()
    assert np.isfinite(trained["b"]).all()

def test_train_only_scaler_excludes_extreme_test_values():
    seq=example_data()
    seq[-1,3]=2000.
    clients,val,test=m.temporal_partition(seq,6)
    X,Y=m.features_and_targets(seq)
    _,_,norm=m.standardize_training_only(X,Y,np.concatenate(clients))
    assert abs(norm[0][0])<2.

def test_fail_closed_bad_client_count():
    with pytest.raises(ValueError):
        m.temporal_partition(example_data(20),6)
    with pytest.raises(ValueError):
        m.temporal_partition(np.full((100,6),float("nan")),6)
