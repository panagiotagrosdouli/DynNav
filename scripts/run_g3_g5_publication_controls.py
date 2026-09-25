from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import asdict
import json
from pathlib import Path

from dynnav.experiments.g3_information_assumptions import (
    run_information_assumption_benchmark,
)
from dynnav.experiments.history_compression_memory import (
    run_history_compression_memory_scaling,
)


def _aggregate_g3(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[float, float, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        key = (
            float(row["true_target_probability"]),
            float(row["minimum_return_probability"]),
            str(row["policy"]),
        )
        grouped[key].append(row)

    result: list[dict[str, object]] = []
    for (probability, threshold, policy), items in sorted(grouped.items()):
        n = len(items)
        result.append(
            {
                "true_target_probability": probability,
                "minimum_return_probability": threshold,
                "policy": policy,
                "repetitions": n,
                "mean_absolute_error": sum(
                    float(item["absolute_error"]) for item in items
                )
                / n,
                "mean_target_exposures": sum(
                    int(item["target_exposures"]) for item in items
                )
                / n,
                "mean_side_observations": sum(
                    int(item["side_observations"]) for item in items
                )
                / n,
                "mean_target_failures": sum(
                    int(item["target_failures"]) for item in items
                )
                / n,
                "mean_budget_spent": sum(
                    float(item["budget_spent"]) for item in items
                )
                / n,
                "mean_structural_bias": (
                    sum(
                        float(item["structural_bias"])
                        for item in items
                        if item["structural_bias"] is not None
                    )
                    / sum(
                        item["structural_bias"] is not None for item in items
                    )
                    if any(
                        item["structural_bias"] is not None for item in items
                    )
                    else None
                ),
            }
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run frozen G3 information-assumption and G5 compression controls."
    )
    parser.add_argument("--opportunities", type=int, default=1000)
    parser.add_argument("--repetitions", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20260925)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/research_gap_program/g3_g5_publication_controls.json"),
    )
    args = parser.parse_args()
    if args.opportunities <= 0 or args.repetitions <= 0:
        raise ValueError("opportunities and repetitions must be positive")

    g3_rows: list[dict[str, object]] = []
    condition = 0
    for probability in (0.1, 0.3, 0.5, 0.7):
        for threshold in (0.5, 0.7, 0.9):
            for repetition in range(args.repetitions):
                records = run_information_assumption_benchmark(
                    opportunities=args.opportunities,
                    true_target_probability=probability,
                    minimum_return_probability=threshold,
                    confidence=0.90,
                    risk_budget=20.0,
                    passive_observation_rate=0.25,
                    transfer_observation_rate=0.25,
                    transfer_biases=(-0.2, 0.0, 0.2),
                    seed=args.seed + condition * 100_000 + repetition,
                )
                for record in records:
                    row = asdict(record)
                    row["repetition"] = repetition
                    row["condition_index"] = condition
                    g3_rows.append(row)
            condition += 1

    g5_records = run_history_compression_memory_scaling(
        module_counts=(2, 3, 4, 5, 6),
        recoverability_weight=2.0,
    )
    payload = {
        "metadata": {
            "seed": args.seed,
            "g3_opportunities_per_condition": args.opportunities,
            "g3_repetitions_per_condition": args.repetitions,
            "g3_true_probabilities": [0.1, 0.3, 0.5, 0.7],
            "g3_return_thresholds": [0.5, 0.7, 0.9],
            "g3_risk_budget": 20.0,
            "g3_passive_observation_rate": 0.25,
            "g3_transfer_observation_rate": 0.25,
            "g3_transfer_biases": [-0.2, 0.0, 0.2],
            "g5_module_counts": [2, 3, 4, 5, 6],
            "g5_recoverability_weight": 2.0,
            "scope": "bounded synthetic publication-control study",
        },
        "G3_raw": g3_rows,
        "G3_summary": _aggregate_g3(g3_rows),
        "G5_memory_scaling": [asdict(record) for record in g5_records],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
