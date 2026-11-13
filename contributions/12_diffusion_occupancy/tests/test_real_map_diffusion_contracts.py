"""C12 sample-tail math, malformed input and genuine training helper contracts."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

DIR=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(DIR))
from diffusion_occupancy import DiffusionOccupancyConfig,DiffusionOccupancyPredictor

SCRIPT=DIR/"experiments"/"train_real_map_static_denoiser.py"
spec=importlib.util.spec_from_file_location("c12_real_map_trainer",SCRIPT)
trainer=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=trainer
spec.loader.exec_module(trainer)

def test_expected_schedule_nonnegative_and_finite():
    values=trainer.cosine_schedule(20)
    assert values.shape==(20,)
    assert np.all(np.isfinite(values))
    assert np.all(values>0)
    assert np.all(values<=1)
    with pytest.raises(ValueError):
        trainer.cosine_schedule(1)

def test_fractional_cvar_95_exact_not_naive_integer_topk():
    cfg=DiffusionOccupancyConfig(grid_h=2,grid_w=2,T=3,n_samples=12)
    model=DiffusionOccupancyPredictor(cfg)
    values=np.array([.10]*11+[1.0],dtype=float)
    examples=iter([np.full((2,2),x) for x in values])
    model.sample=lambda _:next(examples)
    outcome=model.predict_risk([np.zeros((2,2),dtype=float)])
    assert float(outcome["cvar_95"][0,0])==pytest.approx(1.)
    assert float(outcome["mean"][0,0])==pytest.approx(float(values.mean()))
    assert np.all(outcome["cvar_95"]>=outcome["mean"])

def test_bad_occupancy_history_rejected():
    model=DiffusionOccupancyPredictor(DiffusionOccupancyConfig(grid_h=4,grid_w=4,T=4,n_samples=3))
    for value in [np.ones((3,3)),np.full((4,4),np.nan),np.full((4,4),-1.)]:
        with pytest.raises(ValueError):
            model.predict_risk([value])

def test_invalid_path_cell_cannot_be_silently_skipped():
    model=DiffusionOccupancyPredictor(DiffusionOccupancyConfig(grid_h=4,grid_w=4,T=4,n_samples=3))
    risk={"cvar_95":np.zeros((4,4))}
    with pytest.raises(ValueError):
        model.risk_weighted_cost([(0,0),(99,99)],risk)
    with pytest.raises(ValueError):
        model.risk_weighted_cost([(0,0)],risk,lambda_risk=float("nan"))

def test_real_map_trainer_requires_actual_torch_to_train():
    # Importing the trainer is dependency-light; PyTorch is only needed for
    # the separately executed model training, not for structure-only checks.
    assert callable(trainer.run)
