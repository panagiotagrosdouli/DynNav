"""C11 VLM outputs are untrusted; validate before metric navigation."""
import importlib.util
import json
import math
import sys
from pathlib import Path
import numpy as np
import pytest

FILE=Path(__file__).resolve().parents[1]/"vlm_planner.py"
spec=importlib.util.spec_from_file_location("c11_vlm_untrusted",FILE)
m=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=m
spec.loader.exec_module(m)

def agent(payload):
    planner=m.VLMNavigationPlanner()
    planner._encode_frame=lambda image:"FAKE_IMAGE_NO_MODEL"
    planner._query_vlm=lambda image:payload
    return planner

@pytest.mark.parametrize("conf",["NaN","Infinity","-0.2","1.2"])
def test_invalid_confidence_json_rejected(conf):
    planner=agent('{"goal":"forward","region":"corridor","confidence":'+conf+'}')
    assert planner.plan(np.zeros((4,4,3),dtype=np.uint8)) is None
    assert planner.session_summary()["total"]==0

@pytest.mark.parametrize("pixel",[(4,1),(-1,1),(1,4),(1,-1)])
def test_invalid_pixel_coordinates_fail_closed(pixel):
    payload=json.dumps({"goal":"forward","region":"corridor","confidence":.95,"pixel_u":pixel[0],"pixel_v":pixel[1]})
    assert agent(payload).plan(np.zeros((4,4,3),dtype=np.uint8),np.ones((4,4),dtype=float)) is None

@pytest.mark.parametrize("invalid_depth",[float("nan"),float("inf"),-1.,0.])
def test_bad_depth_cannot_be_used_as_waypoint(invalid_depth):
    payload='{"goal":"forward","region":"corridor","confidence":0.95,"pixel_u":1,"pixel_v":2}'
    depth=np.ones((4,4),dtype=float)
    depth[2,1]=invalid_depth
    result=agent(payload).plan(np.zeros((4,4,3),dtype=np.uint8),depth)
    assert result is None

def test_missing_or_incomplete_pixel_pair_rejected_for_depth():
    payload='{"goal":"forward","region":"corridor","confidence":0.95,"pixel_u":1}'
    assert agent(payload).plan(np.zeros((4,4,3),dtype=np.uint8)) is None
    payload='{"goal":"forward","region":"corridor","confidence":0.95}'
    assert agent(payload).plan(np.zeros((4,4,3),dtype=np.uint8),np.ones((4,4))) is None

def test_finite_grounded_depth_generates_finite_waypoint():
    payload='{"goal":"forward","region":"corridor","confidence":0.95,"pixel_u":1,"pixel_v":2}'
    goal=agent(payload).plan(np.zeros((4,4,3),dtype=np.uint8),np.ones((4,4)))
    assert goal is not None
    assert goal.metric_waypoint is not None
    assert all(math.isfinite(x) for x in goal.metric_waypoint)

def test_fenced_json_is_parsed_without_lstrip_character_corruption():
    payload='```json\n{"goal":"left","region":"doorway","confidence":0.9}\n```'
    assert agent(payload)._parse_response(payload).region_label=="doorway"

def test_bad_frame_and_pose_rejected_before_model_call():
    planner=agent('{"goal":"forward","region":"corridor","confidence":0.9}')
    assert planner.plan(np.zeros((4,4),dtype=np.uint8)) is None
    assert planner.plan(np.zeros((4,4,3),dtype=np.uint8),current_pose=(float("nan"),0.,0.)) is None
    assert planner.session_summary()["total"]==0
