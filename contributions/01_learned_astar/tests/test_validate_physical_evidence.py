"""Tests for C01 physical-evidence integrity gate, with synthetic files only."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "experiments" / "validate_physical_evidence.py"
spec = importlib.util.spec_from_file_location("c01_hardware_gate", MODULE)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def fixture(tmp_path):
    bag = tmp_path / "record.mcap"
    trace = tmp_path / "planner_trace.jsonl"
    bag.write_bytes(b"synthetic file; NOT an actual ROS bag")
    trace.write_text("synthetic test only\n")
    hash_file = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    data = dict(
        trial_id="test-fixture-only", block_id="b1",
        planner_mode="learned_raw", git_sha="a" * 40,
        robot_model="FICTIONAL_FIXTURE", robot_id="fixture",
        ros_distro="jazzy", map_sha256="b" * 64,
        model_sha256="c" * 64, rosbag_path=bag.name,
        rosbag_sha256=hash_file(bag),
        planner_trace_path=trace.name,
        planner_trace_sha256=hash_file(trace),
        start_pose=[0, 0, 0], goal_pose=[1, 1, 0],
        operator_attestation=True, safety_approval=True,
        e_stop_check=True, trial_status="succeeded",
        validity_reason="", incident="",
    )
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path, data


def test_hash_gate_is_not_physical_evidence(tmp_path):
    path, data = fixture(tmp_path)
    status = module.validate_manifest(path)
    assert status["status"] == "STRUCTURAL_EVIDENCE_PASS_HUMAN_REVIEW_REQUIRED"
    assert "No automatic proof" in status["caveat"]


def test_tampering_rejected(tmp_path):
    path, data = fixture(tmp_path)
    (tmp_path / data["rosbag_path"]).write_bytes(b"changed data")
    assert module.validate_manifest(path)["status"] == "INVALID_EVIDENCE"


def test_missing_human_attestation_rejected(tmp_path):
    path, data = fixture(tmp_path)
    data["safety_approval"] = False
    path.write_text(json.dumps(data), encoding="utf-8")
    assert module.validate_manifest(path)["status"] == "INVALID_EVIDENCE"


def test_path_escape_rejected(tmp_path):
    path, data = fixture(tmp_path)
    data["rosbag_path"] = "../external.mcap"
    path.write_text(json.dumps(data), encoding="utf-8")
    result = module.validate_manifest(path)
    assert result["status"] == "INVALID_EVIDENCE"
    assert "escapes" in " ".join(result["errors"])


def test_missing_fields_rejected(tmp_path):
    path, data = fixture(tmp_path)
    data.pop("model_sha256")
    path.write_text(json.dumps(data), encoding="utf-8")
    assert module.validate_manifest(path)["status"] == "INVALID_EVIDENCE"


def test_non_json_rejected(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_text("{this is broken")
    assert module.validate_manifest(path)["status"] == "INVALID_EVIDENCE"
