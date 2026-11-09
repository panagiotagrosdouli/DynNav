"""Read-only provenance gate for C01 physically executed robot trials.

A passing machine gate verifies file existence, integrity and declared metadata;
it DOES NOT independently establish that a physical robot moved or that the C01
controller generated the recorded path. An authorized independent hardware
review and synchronized sensor/planner review are still mandatory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

REQUIRED = (
    "trial_id", "block_id", "planner_mode", "git_sha", "robot_model",
    "robot_id", "ros_distro", "map_sha256", "model_sha256", "rosbag_path",
    "rosbag_sha256", "planner_trace_path", "planner_trace_sha256",
    "start_pose", "goal_pose", "operator_attestation",
    "safety_approval", "e_stop_check", "trial_status",
    "validity_reason", "incident",
)
MODES = {"astar_manhattan", "learned_raw", "learned_manhattan_clipped"}
DIGEST = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def validate_manifest(manifest_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"status": "INVALID_EVIDENCE", "errors": [f"Cannot parse manifest: {exc}"]}
    if not isinstance(data, dict):
        return {"status": "INVALID_EVIDENCE", "errors": ["Manifest must be a JSON object"]}
    missing = [field for field in REQUIRED if field not in data]
    errors.extend(f"Missing mandatory field: {key}" for key in missing)
    for field in REQUIRED:
        value = data.get(field)
        if isinstance(value, str) and not value.strip() and field not in {"incident", "validity_reason"}:
            errors.append(f"Empty mandatory field: {field}")
    if data.get("planner_mode") not in MODES:
        errors.append("Invalid C01 planner_mode")
    if not isinstance(data.get("git_sha"), str) or not GIT_SHA.fullmatch(data["git_sha"]):
        errors.append("git_sha must be a full 40-character lowercase hex SHA")
    for name in ("map_sha256", "model_sha256", "rosbag_sha256", "planner_trace_sha256"):
        value = data.get(name)
        if not isinstance(value, str) or not DIGEST.fullmatch(value):
            errors.append(f"{name} must be a 64-character lowercase hex digest")
    for name in ("start_pose", "goal_pose"):
        point = data.get(name)
        if not isinstance(point, list) or len(point) != 3 or not all(
            isinstance(x, (int, float)) and not isinstance(x, bool) for x in point
        ):
            errors.append(f"{name} must be an [x, y, yaw] numeric array")
    if data.get("trial_status") not in {"succeeded", "failed", "aborted", "invalid"}:
        errors.append("trial_status must be succeeded/failed/aborted/invalid")
    for name in ("operator_attestation", "safety_approval", "e_stop_check"):
        if data.get(name) is not True:
            errors.append(f"{name} must be explicitly true; mere presence is insufficient")

    evidence = {}
    for name in ("rosbag", "planner_trace"):
        file_key, digest_key = name + "_path", name + "_sha256"
        raw = data.get(file_key)
        if not isinstance(raw, str) or not raw.strip():
            continue
        path = (manifest_path.parent / raw).resolve()
        # Only accept records within the supplied evidence root. Prevent
        # accidentally hashing unrelated files through ../ or symlinks.
        if not path.is_relative_to(manifest_path.parent.resolve()):
            errors.append(f"{file_key} escapes the manifest directory")
        elif not path.is_file():
            errors.append(f"{file_key} is missing or not a regular file: {raw}")
        else:
            digest = file_hash(path)
            evidence[name] = {"sha256_verified": digest == data.get(digest_key), "bytes": path.stat().st_size}
            if not evidence[name]["sha256_verified"]:
                errors.append(f"{digest_key} does not match actual file bytes")
            if path.stat().st_size == 0:
                errors.append(f"{name} file is empty")

    # A ROS bag commonly consists of an MCAP/DB3 plus metadata.yaml. This
    # gate requires a single specified sensor record file and never presumes
    # a source machine's YAML alone is a physical execution.
    return {
        "status": "STRUCTURAL_EVIDENCE_PASS_HUMAN_REVIEW_REQUIRED" if not errors else "INVALID_EVIDENCE",
        "trial_id": data.get("trial_id"),
        "evidence": evidence,
        "errors": errors,
        "caveat": "No automatic proof of physical robot execution or C01 controller identity; inspect synchronized ROS topics and actual physical hardware in independent review.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, help="write a JSON validation result")
    args = parser.parse_args()
    result = validate_manifest(args.manifest.resolve())
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if result["status"] == "STRUCTURAL_EVIDENCE_PASS_HUMAN_REVIEW_REQUIRED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
