from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from scripts.merge_v4_shards import merge_v4_shards


def _write_shard(
    root: Path,
    *,
    shard_index: int,
    scenario: str,
    duplicate_seed: bool = False,
) -> None:
    directory = root / f"shard-{shard_index}"
    directory.mkdir(parents=True)
    planners = ["belief", "detector_as_truth"]
    rows = []
    for seed in range(2):
        for planner in planners:
            rows.append(
                {
                    "scenario": scenario,
                    "seed": seed,
                    "planner": planner,
                    "value": f"{shard_index}-{seed}-{planner}",
                }
            )
    if duplicate_seed:
        rows.append(dict(rows[0]))

    with (directory / "trials.csv").open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    metadata = {
        "protocol": "EXPERIMENT_PROTOCOL_V4.md",
        "split": "heldout",
        "observation_regime": "O2",
        "true_sensitivity": 0.85,
        "true_specificity": 0.85,
        "assumed_sensitivity": 0.85,
        "assumed_specificity": 0.85,
        "assumed_arming_offset": 0.0,
        "seeds_per_scenario": 2,
        "head_sha": "abc",
        "manifest_sha256": "def",
        "manifest_scenario_count": 2,
        "shard_count": 2,
        "shard_index": shard_index,
        "scenario_count": 1,
        "planners": planners,
        "raw_trials_sha256": f"hash-{shard_index}",
    }
    (directory / "run_metadata.json").write_text(
        json.dumps(metadata),
        encoding="utf-8",
    )


def test_merge_v4_shards_is_complete_and_deterministic(tmp_path: Path) -> None:
    root = tmp_path / "inputs"
    _write_shard(root, shard_index=0, scenario="s0")
    _write_shard(root, shard_index=1, scenario="s1")

    output = tmp_path / "merged"
    metadata = merge_v4_shards(
        root,
        output,
        expected_shards=2,
    )

    assert metadata["scenario_count"] == 2
    assert metadata["merged_row_count"] == 8
    assert metadata["planners"] == ["belief", "detector_as_truth"]

    with (output / "trials.csv").open(
        newline="",
        encoding="utf-8",
    ) as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 8
    assert [(row["scenario"], int(row["seed"]), row["planner"]) for row in rows] == sorted(
        (row["scenario"], int(row["seed"]), row["planner"])
        for row in rows
    )


def test_merge_v4_shards_rejects_duplicate_trial_key(tmp_path: Path) -> None:
    root = tmp_path / "inputs"
    _write_shard(
        root,
        shard_index=0,
        scenario="s0",
        duplicate_seed=True,
    )
    _write_shard(root, shard_index=1, scenario="s1")

    with pytest.raises(ValueError, match="duplicate merged trial key"):
        merge_v4_shards(
            root,
            tmp_path / "merged",
            expected_shards=2,
        )


def test_merge_v4_shards_rejects_missing_shard(tmp_path: Path) -> None:
    root = tmp_path / "inputs"
    _write_shard(root, shard_index=0, scenario="s0")

    with pytest.raises(ValueError, match="expected 2 shard metadata"):
        merge_v4_shards(
            root,
            tmp_path / "merged",
            expected_shards=2,
        )
