"""C10 executable non-finite sensor, language and operator-confirmation guards."""
from pathlib import Path
import importlib.util
import sys
import math
import pytest

FILE=Path(__file__).resolve().parents[1]/"code"/"human_ethics_policy.py"
spec=importlib.util.spec_from_file_location("c10_ethics_policy_safe",FILE)
m=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=m
spec.loader.exec_module(m)

@pytest.mark.parametrize("field,bad",[
    ("distance_to_human_m",float("nan")),
    ("distance_to_human_m",-1.0),
    ("operator_trust",float("inf")),
    ("language_confidence",float("nan")),
    ("requested_autonomy",1.5),
])
def test_invalid_safety_context_never_allows_movement(field,bad):
    values={"zone_type":m.ZoneType.NONE,"distance_to_human_m":5.,
            "operator_trust":.9,"language_confidence":.95,"requested_autonomy":.8}
    values[field]=bad
    decision=m.decide_human_ethics_policy(m.HumanEthicsContext(**values))
    assert decision.action==m.PlannerAction.BLOCK_PATH
    assert not decision.path_allowed
    assert decision.max_speed==0.
    assert decision.requires_operator_confirmation

def test_unrecognized_ethical_zone_fails_closed():
    context=m.HumanEthicsContext(zone_type="unknown_zone")
    result=m.decide_human_ethics_policy(context)
    assert result.action==m.PlannerAction.BLOCK_PATH
    assert not result.path_allowed

@pytest.mark.parametrize("trust,confidence",[(0.2,0.9),(.9,.2)])
def test_operator_confirmation_request_does_not_authorize_motion(trust,confidence):
    context=m.HumanEthicsContext(operator_trust=trust,language_confidence=confidence)
    result=m.decide_human_ethics_policy(context)
    assert result.action==m.PlannerAction.ASK_OPERATOR
    assert not result.path_allowed
    assert result.max_speed==0.
    assert result.requires_operator_confirmation

def test_clear_and_no_go_cases_remain_distinct():
    normal=m.decide_human_ethics_policy(m.HumanEthicsContext())
    prohibited=m.decide_human_ethics_policy(m.HumanEthicsContext(zone_type=m.ZoneType.NO_GO))
    assert normal.action==m.PlannerAction.NORMAL
    assert normal.path_allowed and normal.max_speed>0
    assert prohibited.action==m.PlannerAction.BLOCK_PATH
    assert not prohibited.path_allowed and prohibited.max_speed==0.
