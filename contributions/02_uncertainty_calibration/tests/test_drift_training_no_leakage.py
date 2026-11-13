"""C02 drift training reproducibility and leakage protections."""
from pathlib import Path
import importlib.util
import sys
import numpy as np
import pytest

torch=pytest.importorskip("torch")
pd=pytest.importorskip("pandas")
script=Path(__file__).resolve().parents[1]/"code"/"train_drift_uncertainty_net.py"
spec=importlib.util.spec_from_file_location("c02_drift_training",script)
mod=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=mod
spec.loader.exec_module(mod)

def test_training_only_normalization_excludes_heldout_extremum(tmp_path):
    data=pd.DataFrame({"entropy":[0,1,2,3,4,5,6,7,8,99999],
                       "local_uncertainty":np.arange(10,dtype=float),
                       "speed":np.arange(10,dtype=float)*.5,
                       "drift":np.arange(10,dtype=float)})
    path=tmp_path/"drift.csv"
    data.to_csv(path,index=False)
    ds=mod.DriftDataset(str(path),fit_indices=np.arange(9))
    assert ds.x_mean[0,0]==pytest.approx(4)
    assert ds.X[-1,0] > 1000
    assert ds.y_mean[0,0]==pytest.approx(4)

def test_train_actual_short_c02_model_without_overwriting_history(tmp_path):
    data=pd.DataFrame({"entropy":np.linspace(0,1,30),"local_uncertainty":np.linspace(1,2,30),
                       "speed":np.linspace(0,3,30),"drift":np.linspace(0.5,1.5,30)})
    csv=tmp_path/"drift.csv"
    model=tmp_path/"new.pt"
    stats=tmp_path/"norm.npz"
    data.to_csv(csv,index=False)
    mod.train(str(csv),str(model),str(stats),epochs=1,seed=10)
    assert model.exists() and stats.exists()
    ckpt=torch.load(model,map_location="cpu",weights_only=True)
    assert len(ckpt["feature_cols"])==3
    assert ckpt["input_dim"]==3
    with np.load(stats,allow_pickle=False) as arr:
        assert np.all(np.isfinite(arr["x_mean"]))
        assert np.all(arr["x_std"]>0)
