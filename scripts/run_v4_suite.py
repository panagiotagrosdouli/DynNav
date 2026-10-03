from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
from dataclasses import asdict
from pathlib import Path

from dynnav.experiments.v4_belief_execution import (
    V4Planner,
    run_v4_execution_trial,
)
from dynnav.experiments.v4_scenario_manifest import load_manifest


OBSERVATION_REGIMES: dict[str, tuple[float, float]] = {
    "O0": (1.00, 1.00),
    "O1": (0.95, 0.95),
    "O2": (0.85, 0.85),
    "O3": (0.70, 0.70),
    "O4": (0.70, 0.95),
    "O5": (0.95, 0.70),
    "O6": (0.50, 0.50),
}

PLANNERS = (
    V4Planner.SHORTEST,
    V4Planner.FIXED_MARGINAL_EXACT,
    V4Planner.PRIOR_ONLY,
    V4Planner.ACTIVATION_ORACLE,
    V4Planner.DETECTOR_AS_TRUTH,
    V4Planner.BELIEF,
    V4Planner.HARD_BELIEF,
)


def select_scenario_shard(
    scenarios: tuple[object, ...] | list[object],
    *,
    shard_count: int,
    shard_index: int,
) -> tuple[object, ...]:
    """Return deterministic modulo shard without changing scenario order."""
    if shard_count <= 0:
        raise ValueError("shard_count must be positive")
    if shard_index < 0 or shard_index >= shard_count:
        raise ValueError("shard_index must satisfy 0 <= index < shard_count")
    return tuple(
        scenario
        for index, scenario in enumerate(scenarios)
        if index % shard_count == shard_index
    )


def _git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        text=True,
    ).strip()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json(value: object) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Execute a frozen DynNav V4 scenario suite."
    )
    parser.add_argument(
        "--split",
        choices=("development", "validation", "heldout"),
        default="development",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Override the canonical benchmarks/v4/<split>.json manifest.",
    )
    parser.add_argument(
        "--regime",
        choices=tuple(OBSERVATION_REGIMES),
        default="O2",
    )
    parser.add_argument("--seeds", type=int, default=None)
    parser.add_argument(
        "--shard-count",
        type=int,
        default=1,
        help="Deterministically split the frozen manifest by scenario index.",
    )
    parser.add_argument(
        "--shard-index",
        type=int,
        default=0,
        help="Zero-based modulo shard index.",
    )
    parser.add_argument(
        "--assumed-sensitivity",
        type=float,
        default=None,
        help="Planner-assumed detector sensitivity; defaults to true regime.",
    )
    parser.add_argument(
        "--assumed-specificity",
        type=float,
        default=None,
        help="Planner-assumed detector specificity; defaults to true regime.",
    )
    parser.add_argument(
        "--assumed-arming-offset",
        type=float,
        default=0.0,
        help=(
            "Additive planner-model offset applied to each frozen q_i and "
            "clipped to [0,1]. Truth remains unchanged."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/v4_suite"),
    )
    parser.add_argument(
        "--allow-heldout",
        action="store_true",
        help="Required explicit acknowledgement for held-out execution.",
    )
    parser.add_argument(
        "--expected-head-sha",
        default=None,
        help="For held-out runs, must exactly equal git rev-parse HEAD.",
    )
    args = parser.parse_args()

    if args.split == "heldout":
        if not args.allow_heldout:
            raise SystemExit(
                "held-out execution is locked; pass --allow-heldout only after "
                "the pre-outcome freeze commit is recorded"
            )
        head = _git_head()
        if args.expected_head_sha != head:
            raise SystemExit(
                "--expected-head-sha must exactly match the current frozen HEAD "
                f"({head})"
            )

    manifest = args.manifest or Path("benchmarks/v4") / f"{args.split}.json"
    all_scenarios = load_manifest(manifest)
    scenarios = select_scenario_shard(
        all_scenarios,
        shard_count=args.shard_count,
        shard_index=args.shard_index,
    )
    if not scenarios:
        raise ValueError("selected shard contains no scenarios")

    if args.seeds is None:
        seed_count = 250 if args.split == "heldout" and args.regime == "O2" else 100
    else:
        seed_count = args.seeds
    if seed_count <= 0:
        raise ValueError("--seeds must be positive")

    sensitivity, specificity = OBSERVATION_REGIMES[args.regime]
    assumed_sensitivity = (
        sensitivity
        if args.assumed_sensitivity is None
        else float(args.assumed_sensitivity)
    )
    assumed_specificity = (
        specificity
        if args.assumed_specificity is None
        else float(args.assumed_specificity)
    )
    for label, value in (
        ("assumed_sensitivity", assumed_sensitivity),
        ("assumed_specificity", assumed_specificity),
    ):
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{label} must be in [0, 1]")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = args.output_dir / "trials.csv"

    rows: list[dict[str, object]] = []
    for spec in scenarios:
        assumed_q = tuple(
            min(
                1.0,
                max(
                    0.0,
                    hazard.arming_probability + args.assumed_arming_offset,
                ),
            )
            for hazard in spec.hazards
        )
        scenario = spec.to_execution_scenario(
            sensitivity=sensitivity,
            specificity=specificity,
            assumed_sensitivity=assumed_sensitivity,
            assumed_specificity=assumed_specificity,
            assumed_arming_probabilities=assumed_q,
        )
        for seed in range(seed_count):
            for planner in PLANNERS:
                record = run_v4_execution_trial(
                    scenario,
                    seed=seed,
                    planner=planner,
                )
                row = asdict(record)
                row.update(
                    {
                        "protocol_version": "V4",
                        "split": args.split,
                        "topology_family": spec.family,
                        "observation_regime": args.regime,
                        "sensitivity": sensitivity,
                        "specificity": specificity,
                        "true_sensitivity": sensitivity,
                        "true_specificity": specificity,
                        "assumed_sensitivity": assumed_sensitivity,
                        "assumed_specificity": assumed_specificity,
                        "assumed_arming_offset": args.assumed_arming_offset,
                        "recoverability_weight": scenario.recoverability_weight,
                        "hard_return_threshold": scenario.hard_return_threshold,
                        "arming_probabilities": _json(
                            [h.arming_probability for h in spec.hazards]
                        ),
                        "true_arming_probabilities": _json(
                            [h.arming_probability for h in spec.hazards]
                        ),
                        "assumed_arming_probabilities": _json(assumed_q),
                        "closure_probabilities": _json(
                            [h.closure_probability for h in spec.hazards]
                        ),
                    }
                )
                for field in (
                    "path",
                    "true_armed_set",
                    "estimated_armed_set",
                    "trigger_ids_executed",
                    "detector_observations",
                    "realized_closure_cells",
                ):
                    row[field] = _json(row[field])

                if (
                    record.mission_success
                    and math.isfinite(record.predicted_return_probability)
                ):
                    row["brier_score"] = (
                        record.predicted_return_probability
                        - float(record.return_feasible)
                    ) ** 2
                else:
                    row["brier_score"] = float("nan")
                row["return_infeasible"] = bool(
                    record.mission_success and not record.return_feasible
                )
                rows.append(row)

    if not rows:
        raise RuntimeError("suite produced no rows")

    with raw_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    metadata = {
        "protocol": "EXPERIMENT_PROTOCOL_V4.md",
        "split": args.split,
        "observation_regime": args.regime,
        "sensitivity": sensitivity,
        "specificity": specificity,
        "true_sensitivity": sensitivity,
        "true_specificity": specificity,
        "assumed_sensitivity": assumed_sensitivity,
        "assumed_specificity": assumed_specificity,
        "assumed_arming_offset": args.assumed_arming_offset,
        "scenario_count": len(scenarios),
        "manifest_scenario_count": len(all_scenarios),
        "shard_count": args.shard_count,
        "shard_index": args.shard_index,
        "seeds_per_scenario": seed_count,
        "planners": [planner.value for planner in PLANNERS],
        "head_sha": _git_head(),
        "manifest": str(manifest),
        "manifest_sha256": _sha256(manifest),
        "raw_trials": str(raw_path),
        "raw_trials_sha256": _sha256(raw_path),
    }
    (args.output_dir / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
