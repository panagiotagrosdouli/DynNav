"""Fail-closed parsing regressions for C19 untrusted model responses."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from llm_mission_planner import LLMMissionPlanner  # noqa: E402


def test_valid_json_and_fenced_json():
    planner = LLMMissionPlanner()
    payload = json.dumps({
        "confidence": 0.9,
        "waypoints": [{"label": "Kitchen", "priority": 2}, {"label": "exit", "priority": 1}],
    })
    for raw in (payload, "```json\n" + payload + "\n```"):
        mission = planner._parse_llm_response("go", raw)
        assert mission is not None
        assert [w.label for w in mission.waypoints] == ["exit", "kitchen"]


def test_malformed_responses_rejected_without_exceptions():
    planner = LLMMissionPlanner()
    invalid = [
        "null", "[]", '{"waypoints": null}', '{"waypoints": [null]}',
        '{"waypoints": [{"label": null}]}',
        '{"waypoints": [{"label": ""}]}',
        '{"waypoints": [{"label": "a", "priority": true}]}',
        '{"waypoints": [{"label": "a", "priority": 0}]}',
        '{"waypoints": [{"label": "a", "priority": 1}, {"label": "b", "priority": 1}]}',
        '{"confidence": 5, "waypoints": []}',
        '{"confidence": "high", "waypoints": []}',
        '{"waypoints": [{"label": "a", "duration_s": -1}]}',
        '{"waypoints": [{"label": "a", "duration_s": 1e999}]}',
        '{"waypoints": [{"label": "a", "action": "execute_shell"}]}',
        "```json\n{}",
    ]
    for raw in invalid:
        assert planner._parse_llm_response("go", raw) is None, raw


def test_invalid_model_response_uses_offline_fallback(monkeypatch):
    planner = LLMMissionPlanner()
    monkeypatch.setattr(planner, "_query_llm", lambda instruction: '{"waypoints": [null]}')
    mission = planner.parse("go to kitchen then exit")
    assert [w.label for w in mission.waypoints] == ["kitchen", "exit"]
