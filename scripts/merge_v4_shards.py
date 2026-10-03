from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def merge_v4_shards(
    input_root: Path,
    output_dir: Path,
    *,
    expected_shards: int,
) -> dict[str, object]:
    if expected_shards <= 0:
        raise ValueError("expected_shards must be positive")

    metadata_paths = sorted(input_root.glob("**/run_metadata.json"))
    if len(metadata_paths) != expected_shards:
        raise ValueError(
            f"expected {expected_shards} shard metadata files, "
            f"found {len(metadata_paths)}"
        )

    metadata = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in metadata_paths
    ]
    shard_indices = sorted(int(item["shard_index"]) for item in metadata)
    if shard_indices != list(range(expected_shards)):
        raise ValueError(
            f"shard indices must be 0..{expected_shards - 1}, got {shard_indices}"
        )

    invariant_fields = (
        "protocol",
        "split",
        "observation_regime",
        "true_sensitivity",
        "true_specificity",
        "assumed_sensitivity",
        "assumed_specificity",
        "assumed_arming_offset",
        "seeds_per_scenario",
        "head_sha",
        "manifest_sha256",
        "manifest_scenario_count",
        "shard_count",
    )
    reference = metadata[0]
    for item in metadata[1:]:
        for field in invariant_fields:
            if item[field] != reference[field]:
                raise ValueError(
                    f"shards disagree on {field}: "
                    f"{reference[field]!r} != {item[field]!r}"
                )

    if int(reference["shard_count"]) != expected_shards:
        raise ValueError("metadata shard_count disagrees with expected_shards")

    rows: list[dict[str, str]] = []
    fieldnames: list[str] | None = None
    seen: set[tuple[str, int, str]] = set()
    scenarios: set[str] = set()

    for metadata_path in metadata_paths:
        trial_path = metadata_path.parent / "trials.csv"
        if not trial_path.exists():
            raise ValueError(f"missing trials.csv beside {metadata_path}")

        with trial_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise ValueError(f"missing CSV header in {trial_path}")
            if fieldnames is None:
                fieldnames = list(reader.fieldnames)
            elif list(reader.fieldnames) != fieldnames:
                raise ValueError("shard CSV schemas differ")

            for row in reader:
                key = (
                    row["scenario"],
                    int(row["seed"]),
                    row["planner"],
                )
                if key in seen:
                    raise ValueError(f"duplicate merged trial key: {key}")
                seen.add(key)
                scenarios.add(row["scenario"])
                rows.append(row)

    if fieldnames is None or not rows:
        raise ValueError("no shard trial rows found")

    expected_scenarios = int(reference["manifest_scenario_count"])
    if len(scenarios) != expected_scenarios:
        raise ValueError(
            f"expected {expected_scenarios} scenarios, found {len(scenarios)}"
        )

    planner_names = sorted(
        {
            planner
            for item in metadata
            for planner in item["planners"]
        }
    )
    expected_rows = (
        expected_scenarios
        * int(reference["seeds_per_scenario"])
        * len(planner_names)
    )
    if len(rows) != expected_rows:
        raise ValueError(
            f"expected {expected_rows} merged rows, found {len(rows)}"
        )

    rows.sort(
        key=lambda row: (
            row["scenario"],
            int(row["seed"]),
            row["planner"],
        )
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    trials_path = output_dir / "trials.csv"
    with trials_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    merged_metadata = {
        **{
            field: reference[field]
            for field in invariant_fields
            if field != "shard_count"
        },
        "shard_count": expected_shards,
        "scenario_count": len(scenarios),
        "planners": planner_names,
        "merged_row_count": len(rows),
        "raw_trials": str(trials_path),
        "raw_trials_sha256": _sha256(trials_path),
        "source_shards": [
            {
                "shard_index": int(item["shard_index"]),
                "scenario_count": int(item["scenario_count"]),
                "raw_trials_sha256": item["raw_trials_sha256"],
            }
            for item in sorted(
                metadata,
                key=lambda value: int(value["shard_index"]),
            )
        ],
    }
    metadata_path = output_dir / "run_metadata.json"
    metadata_path.write_text(
        json.dumps(merged_metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return merged_metadata


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge deterministic V4 held-out scenario shards."
    )
    parser.add_argument("input_root", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--expected-shards", type=int, default=12)
    args = parser.parse_args()

    metadata = merge_v4_shards(
        args.input_root,
        args.output_dir,
        expected_shards=args.expected_shards,
    )
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
