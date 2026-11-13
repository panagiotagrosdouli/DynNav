"""Read the retained audit without executing or silently replacing experiments."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "results/audits/2026-11-12"
FILES = (
    "unavoidable_96/summary.json",
    "unavoidable_96/protocol.json",
    "unavoidable_96/trials.csv",
    "publication-comparison.json",
)


def load_audit(directory: Path = AUDIT) -> dict:
    """Verify file integrity and paired raw-row denominators before exposing values.

    Checksums establish agreement with the retained index, not independent
    authenticity of that index or validation of the scientific model.
    """
    directory = directory.resolve()
    index_bytes = (directory / "artifact_index.json").read_bytes()
    index = json.loads(index_bytes)
    revision = index["code_revision"]
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Audit index must identify a full source commit")
    entries = index["artifacts"]
    by_path = {entry["path"]: entry for entry in entries}
    if len(by_path) != len(entries):
        raise ValueError("Duplicate paths in audit index")
    verified = {}
    for name in FILES:
        path = (directory / name).resolve()
        if not path.is_relative_to(directory):
            raise ValueError("Audit artifact escapes evidence directory")
        data = path.read_bytes()
        entry = by_path[name]
        if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError(f"Audit checksum mismatch: {name}")
        verified[name] = data

    summary = json.loads(verified[FILES[0]])
    protocol = json.loads(verified[FILES[1]])
    comparison = json.loads(verified[FILES[3]])
    if comparison.get("all_passed") is not True or not all(comparison.get("checks", {}).values()):
        raise ValueError("Retained publication comparison did not pass")
    counts = Counter()
    failures = Counter()
    seen = set()
    planners = {"shortest", "state_only_single", "state_only_exact", "history_exact"}
    expected_scenarios = {f"frozen_{i:02d}" for i in range(protocol["scenario_count"])}
    expected_seeds = set(range(protocol["execution_seeds"]))
    for row in csv.DictReader(io.StringIO(verified[FILES[2]].decode("utf-8"))):
        scenario, seed, planner = row["scenario"], int(row["seed"]), row["planner"]
        key = (scenario, seed, planner)
        if key in seen or scenario not in expected_scenarios or seed not in expected_seeds or planner not in planners:
            raise ValueError("Invalid or duplicate paired trial identity")
        if row["return_infeasible"] not in {"True", "False"}:
            raise ValueError("Invalid binary trial outcome")
        seen.add(key)
        counts[scenario, planner] += 1
        failures[planner] += row["return_infeasible"] == "True"
    if any(counts[s, p] != len(expected_seeds) for s in expected_scenarios for p in planners):
        raise ValueError("Incomplete paired scenario/seed matrix")
    denominator = len(expected_scenarios) * len(expected_seeds)
    for planner in planners:
        aggregate = summary["aggregate"][planner]
        if aggregate["trials"] != denominator or not math.isclose(
            aggregate["mean_return_infeasible_rate"], failures[planner] / denominator, abs_tol=1e-12
        ):
            raise ValueError("Raw trial outcomes disagree with retained aggregate")
    effect = summary["aggregate"]["history_exact_vs_state_only_exact_scenario_effect"]
    if not all(math.isfinite(effect[k]) for k in ("estimate", "lower", "upper")):
        raise ValueError("Nonfinite uncertainty estimate")
    if not effect["lower"] <= effect["estimate"] <= effect["upper"] or effect["sample_size"] != len(expected_scenarios):
        raise ValueError("Invalid scenario-level uncertainty interval")
    return {
        "summary": summary,
        "protocol": protocol,
        "effect": effect,
        "code_revision": revision,
        "verified_files": verified,
        "index_sha256": hashlib.sha256(index_bytes).hexdigest(),
        "trial_rows": len(seen),
        "scope": "Synthetic generated topology; paired scenario bootstrap, not physical-world effectiveness",
        "provenance_boundary": (
            "Index revision identifies the audit code checkpoint. Individual original commands were not all "
            "stamped with their generating commit; this is not proof that every file was generated at that revision."
        ),
    }
