from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from dynnav.experiments.v4_analysis import (
    V4AnalysisRow,
    calibration_metrics,
    fixed_bin_calibration,
    paired_v4_comparison,
)


def _bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "1"}:
        return True
    if normalized in {"false", "0"}:
        return False
    raise ValueError(f"invalid boolean value: {value!r}")


def _load(path: Path) -> list[V4AnalysisRow]:
    rows: list[V4AnalysisRow] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            rows.append(
                V4AnalysisRow(
                    scenario=raw["scenario"],
                    topology_family=raw["topology_family"],
                    seed=int(raw["seed"]),
                    planner=raw["planner"],
                    observation_regime=raw["observation_regime"],
                    path_length=float(raw["path_length"]),
                    predicted_return_probability=float(
                        raw["predicted_return_probability"]
                    ),
                    return_feasible=_bool(raw["return_feasible"]),
                    mission_success=_bool(raw["mission_success"]),
                    protocol_valid=_bool(raw["protocol_valid"]),
                )
            )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze a retained V4 trials.csv with frozen pairing rules."
    )
    parser.add_argument("trials", type=Path)
    parser.add_argument("--regime", default="O2")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("v4_analysis.json"),
    )
    parser.add_argument("--bootstrap-seed", type=int, default=2026100304)
    parser.add_argument("--resamples", type=int, default=5000)
    args = parser.parse_args()

    rows = _load(args.trials)

    comparisons = {}
    for baseline in (
        "detector_as_truth",
        "prior_only",
        "fixed_marginal_exact",
        "activation_oracle",
        "hard_belief",
    ):
        comparisons[f"belief_vs_{baseline}"] = paired_v4_comparison(
            rows,
            proposed="belief",
            baseline=baseline,
            observation_regime=args.regime,
            resamples=args.resamples,
            seed=args.bootstrap_seed,
        )

    calibration = {}
    calibration_summary = {}
    for planner in (
        "belief",
        "detector_as_truth",
        "prior_only",
        "fixed_marginal_exact",
        "activation_oracle",
        "hard_belief",
    ):
        bins = fixed_bin_calibration(
            rows,
            planner=planner,
            observation_regime=args.regime,
        )
        calibration_summary[planner] = calibration_metrics(
            rows,
            planner=planner,
            observation_regime=args.regime,
        )
        calibration[planner] = [
            {
                "lower": item.lower,
                "upper": item.upper,
                "count": item.count,
                "mean_prediction": (
                    None
                    if not math.isfinite(item.mean_prediction)
                    else item.mean_prediction
                ),
                "empirical_frequency": (
                    None
                    if not math.isfinite(item.empirical_frequency)
                    else item.empirical_frequency
                ),
            }
            for item in bins
        ]

    output = {
        "protocol": "EXPERIMENT_PROTOCOL_V4.md",
        "regime": args.regime,
        "bootstrap_seed": args.bootstrap_seed,
        "bootstrap_resamples": args.resamples,
        "comparisons": comparisons,
        "calibration_metrics": calibration_summary,
        "calibration": calibration,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
