"""C14 paired counterfactual and structural graph correctness tests.

These are exact SCM mathematical contracts, NOT identification of causal
effects in real physical robot data.
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("c14_paired_scm",ROOT/"causal_risk.py")
m=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=m
spec.loader.exec_module(m)

def test_unrelated_exogenous_node_has_exact_zero_paired_counterfactual_effect():
    scm=m.NavigationSCM()
    scm.add_node(m.CausalNode("irrelevant_noise",m.NodeType.EXOGENOUS,
                              structural_eq=lambda p,n: n))
    ranking=dict(scm.root_cause_ranking({"sensor_noise":1.2},n_samples=150))
    assert ranking["irrelevant_noise"]==pytest.approx(0.0,abs=1e-12)
    assert ranking["sensor_noise"]>0

def test_full_noise_observation_makes_ranking_independent_of_monte_carlo_count():
    scm=m.NavigationSCM()
    noises={name:0.0 for name in scm.nodes}
    noises["sensor_noise"]=1.6
    noises["path_risk"]=.3
    first=dict(scm.root_cause_ranking(noises,n_samples=1))
    second=dict(scm.root_cause_ranking(noises,n_samples=100))
    assert first==pytest.approx(second)

def test_unknown_node_and_nonfinite_noise_fail_closed():
    scm=m.NavigationSCM()
    with pytest.raises(ValueError):
        scm.observational_query({"typo":.1})
    with pytest.raises(ValueError):
        scm.counterfactual_query({},{"unknown":0.})
    with pytest.raises(ValueError):
        scm.counterfactual_query({"sensor_noise":np.nan},{"sensor_noise":0.})
    with pytest.raises(ValueError):
        scm.root_cause_ranking({},n_samples=0)

def test_causal_graph_supports_new_nodes_and_detects_cycles():
    scm=m.NavigationSCM()
    scm.add_node(m.CausalNode("additional",m.NodeType.ENDOGENOUS,
                              parents=["collision"],structural_eq=lambda p,n:p["collision"]+n))
    values=scm.observational_query({"sensor_noise":.7})
    assert values["additional"]==pytest.approx(values["collision"])
    with pytest.raises(ValueError):
        scm.add_node(m.CausalNode("additional"))
    scm.add_node(m.CausalNode("loop_a",parents=["loop_b"]))
    scm.add_node(m.CausalNode("loop_b",parents=["loop_a"]))
    with pytest.raises(ValueError,match="cycle"):
        scm.observational_query({})

def test_intervention_keeps_same_noise_for_other_structural_equations():
    scm=m.NavigationSCM()
    noises={"sensor_noise":.9,"localization_error":.2,"path_risk":.1}
    factual=scm.observational_query(noises)
    counter=scm.counterfactual_query(noises,{"sensor_noise":0.})
    assert counter["sensor_noise"]==0.
    assert counter["localization_error"]!=pytest.approx(factual["localization_error"])
