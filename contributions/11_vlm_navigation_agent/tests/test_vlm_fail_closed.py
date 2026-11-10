"""C11 VLM parsing and semantic gating contract tests.

Uses deterministic mocked responses. These tests do NOT execute a real VLM,
perceive a physical scene or command a robot.
"""
from __future__ import annotations
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location("c11_robust_planner",ROOT/"vlm_planner.py")
mod=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=mod
spec.loader.exec_module(mod)

VALID={"region":"corridor","goal":"move forward","confidence":0.89,"pixel_u":8,"pixel_v":8}
FRAME=np.zeros((32,32,3),dtype=np.uint8)

@pytest.mark.parametrize("payload",[
    {"region":"corridor","goal":"forward","confidence":float("nan")},
    {"region":"corridor","goal":"forward","confidence":1.3},
    {"region":"corridor","goal":"forward","confidence":True},
    {"region":"corridor","goal":"forward","confidence":"0.9"},
    {"region":"corridor","goal":"forward","confidence":.8,"pixel_u":10},
    {"region":"corridor","goal":"forward","confidence":.8,"pixel_u":1.5,"pixel_v":8},
    {"region":"corridor","goal":"","confidence":.8},
    [1,2,3]
])
def test_malformed_vlm_json_is_rejected(payload):
    planner=mod.VLMNavigationPlanner()
    assert planner._parse_response(json.dumps(payload)) is None

def test_fenced_json_parses_without_stripping_goal_content():
    planner=mod.VLMNavigationPlanner()
    goal=planner._parse_response("```json\n"+json.dumps(VALID)+"\n```")
    assert goal is not None
    assert goal.description=="move forward"
    assert goal.pixel_hint==(8,8)

@pytest.mark.parametrize("proposal",[
    {**VALID,"region":"restricted"},
    {**VALID,"goal":"enter private restricted room"},
    {**VALID,"pixel_u":40},
    {**VALID,"confidence":.25},
    {**VALID,"region":"floating_platform"},
])
def test_planner_never_accepts_unsafe_semantic_proposals(proposal,monkeypatch):
    planner=mod.VLMNavigationPlanner()
    monkeypatch.setattr(planner,"_query_vlm",lambda _:json.dumps(proposal))
    assert planner.plan(FRAME) is None
    assert planner.session_summary()["total"]==0

def test_good_image_with_confirmed_depth_can_generate_valid_waypoint(monkeypatch):
    cfg=mod.VLMPlannerConfig(require_metric_waypoint=True)
    planner=mod.VLMNavigationPlanner(cfg)
    monkeypatch.setattr(planner,"_query_vlm",lambda _:json.dumps(VALID))
    depth=np.ones((32,32),dtype=np.float32)*2.0
    out=planner.plan(FRAME,depth,current_pose=(0.,0.,0.))
    assert out is not None and out.metric_waypoint is not None
    assert np.all(np.isfinite(out.metric_waypoint))
    assert planner.session_summary()["total"]==1

def test_no_depth_is_not_silently_a_valid_metric_waypoint(monkeypatch):
    planner=mod.VLMNavigationPlanner(mod.VLMPlannerConfig(require_metric_waypoint=True))
    monkeypatch.setattr(planner,"_query_vlm",lambda _:json.dumps(VALID))
    assert planner.plan(FRAME) is None

@pytest.mark.parametrize("invalid", [float("nan"),0.0,-1.0])
def test_invalid_depth_rejected_without_returning_robot_current_position(monkeypatch,invalid):
    planner=mod.VLMNavigationPlanner(mod.VLMPlannerConfig(require_metric_waypoint=True))
    monkeypatch.setattr(planner,"_query_vlm",lambda _:json.dumps(VALID))
    depth=np.ones((32,32),dtype=np.float32)*2.0
    depth[8,8]=invalid
    assert planner.plan(FRAME,depth,current_pose=(0.,0.,0.)) is None

def test_invalid_rgb_or_mismatched_depth_rejected():
    planner=mod.VLMNavigationPlanner()
    with pytest.raises(ValueError):
        planner.plan(np.zeros((32,32),dtype=np.uint8))
    with pytest.raises(ValueError):
        planner.plan(FRAME,np.zeros((16,16)))
