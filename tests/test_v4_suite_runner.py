from __future__ import annotations

import csv
import json
import subprocess
import sys

import pytest
from pathlib import Path

from scripts.run_v4_suite import select_scenario_shard

from dynnav.experiments.v4_scenario_manifest import (
    V4_DEVELOPMENT_SEED,
    development_suite,
    write_manifest,
)


def test_v4_suite_runner_records_true_and_assumed_models(tmp_path: Path) -> None:
    manifest = tmp_path / "tiny.json"
    write_manifest(
        (development_suite()[0],),
        manifest,
        split="development",
        seed=V4_DEVELOPMENT_SEED,
    )
    output = tmp_path / "run"

    subprocess.run(
        [
            sys.executable,
            "scripts/run_v4_suite.py",
            "--split",
            "development",
            "--manifest",
            str(manifest),
            "--regime",
            "O2",
            "--seeds",
            "1",
            "--assumed-sensitivity",
            "0.95",
            "--assumed-specificity",
            "0.70",
            "--assumed-arming-offset",
            "0.2",
            "--output-dir",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    metadata = json.loads(
        (output / "run_metadata.json").read_text(encoding="utf-8")
    )
    assert metadata["true_sensitivity"] == 0.85
    assert metadata["true_specificity"] == 0.85
    assert metadata["assumed_sensitivity"] == 0.95
    assert metadata["assumed_specificity"] == 0.70
    assert metadata["assumed_arming_offset"] == 0.2

    with (output / "trials.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 7
    assert {row["planner"] for row in rows} == {
        "shortest",
        "fixed_marginal_exact",
        "prior_only",
        "activation_oracle",
        "detector_as_truth",
        "belief",
        "hard_belief",
    }
    assert {float(row["true_sensitivity"]) for row in rows} == {0.85}
    assert {float(row["assumed_sensitivity"]) for row in rows} == {0.95}
    assert {float(row["assumed_specificity"]) for row in rows} == {0.70}
    assert all(row["true_arming_probabilities"] for row in rows)
    assert all(row["assumed_arming_probabilities"] for row in rows)


def test_v4_suite_runner_refuses_heldout_without_explicit_gate() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_v4_suite.py",
            "--split",
            "heldout",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "held-out execution is locked" in (
        completed.stdout + completed.stderr
    )



def test_v4_suite_runner_refuses_heldout_with_wrong_freeze_sha() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_v4_suite.py",
            "--split",
            "heldout",
            "--allow-heldout",
            "--expected-head-sha",
            "0000000000000000000000000000000000000000",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "--expected-head-sha must exactly match" in (
        completed.stdout + completed.stderr
    )


def test_v4_modulo_sharding_is_deterministic_and_exhaustive() -> None:
    scenarios = tuple(f"s{i}" for i in range(24))
    shards = [
        select_scenario_shard(
            scenarios,
            shard_count=12,
            shard_index=index,
        )
        for index in range(12)
    ]

    assert all(len(shard) == 2 for shard in shards)
    assert sorted(item for shard in shards for item in shard) == sorted(scenarios)
    assert shards[0] == ("s0", "s12")
    assert shards[11] == ("s11", "s23")


def test_v4_modulo_sharding_rejects_invalid_index() -> None:
    with pytest.raises(ValueError, match="shard_index"):
        select_scenario_shard(
            ("a", "b"),
            shard_count=2,
            shard_index=2,
        )
