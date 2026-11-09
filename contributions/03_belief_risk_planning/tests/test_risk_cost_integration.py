"""Regression coverage for C03 human and ethical risk cost integration."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

C03 = Path(__file__).resolve().parents[1]
SCRIPT=C03/"code"/"risk_cost_utils.py"
spec=importlib.util.spec_from_file_location("c03_risk_utils_integrated",SCRIPT)
mod=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=mod
spec.loader.exec_module(mod)

def test_combined_ethical_cost_returns_full_breakdown():
    policy=mod.EthicalRiskPolicy(mod.EthicalRiskConfig(
        ethical_weight=2.0, human_proximity_penalty=4.0,
        private_zone_penalty=8.0, vulnerable_area_penalty=10.0
    ))
    result=mod.human_and_ethical_edge_cost(
        3.0, .25, 4.0, policy, near_human=True, in_private_zone=True
    )
    assert result["physical_risk_cost"] == pytest.approx(1.0)
    assert result["ethical_risk"] == pytest.approx(12.0)
    assert result["total_cost"] == pytest.approx(28.0)

def test_human_preference_penalties_are_applied():
    pref=mod.HumanPreference(risk_preference=.25,avoid_dark_areas=True,avoid_low_feature_areas=True)
    result=mod.human_aware_edge_cost(2.0,.5,2.0,pref,is_dark=True,is_low_feature=True)
    assert result == pytest.approx(13.0)

def test_path_risk_and_length():
    risk=np.array([[0.0,.2],[.3,.4]],dtype=float)
    path=[(0,0),(1,0),(1,1)]
    assert mod.path_risk_sum(path,risk)==pytest.approx(.6)
    assert mod.path_length_l2(path)==pytest.approx(2.0)
