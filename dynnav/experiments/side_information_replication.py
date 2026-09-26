"""Multi-seed replication for G3 sentinel side-information transfer."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from statistics import mean, stdev
from typing import Any

from dynnav.experiments.side_information_learning_benchmark import (
    run_side_information_learning_benchmark,
)


def run_side_information_replication(
    *,
    opportunities: int = 1_000,
    repetitions: int = 10,
    seed: int = 20260926,
) -> dict[str, object]:
    """Replicate exact and misspecified sentinel transfer across a frozen grid."""

    if opportunities <= 0:
        raise ValueError("opportunities must be positive")
    if repetitions <= 0:
        raise ValueError("repetitions must be positive")

    raw: list[dict[str, object]] = []
    condition_index = 0
    for target_probability in (0.1, 0.3, 0.5, 0.7):
        sentinel_conditions = (
            ("exact_shared", target_probability),
            ("optimistic_misspecified", max(0.0, target_probability - 0.4)),
            ("pessimistic_misspecified", min(1.0, target_probability + 0.4)),
        )
        for minimum_return in (0.5, 0.7, 0.9):
            for sentinel_condition, sentinel_probability in sentinel_conditions:
                for repetition in range(repetitions):
                    rows = run_side_information_learning_benchmark(
                        opportunities=opportunities,
                        true_target_probability=target_probability,
                        true_sentinel_probability=sentinel_probability,
                        minimum_return_probability=minimum_return,
                        confidence=0.90,
                        seed=seed + 10_000 + 211 * condition_index + repetition,
                    )
                    for row in rows:
                        item = asdict(row)
                        item["sentinel_condition"] = sentinel_condition
                        item["repetition"] = repetition
                        raw.append(item)
                condition_index += 1

    grouped: dict[
        tuple[float, float, str, str],
        list[dict[str, object]],
    ] = defaultdict(list)
    for row in raw:
        key = (
            float(row["true_target_probability"]),
            float(row["minimum_return_probability"]),
            str(row["sentinel_condition"]),
            str(row["policy"]),
        )
        grouped[key].append(row)

    summary: list[dict[str, Any]] = []
    for (
        target_probability,
        minimum_return,
        sentinel_condition,
        policy,
    ), rows in sorted(grouped.items()):
        item: dict[str, Any] = {
            "true_target_probability": target_probability,
            "minimum_return_probability": minimum_return,
            "sentinel_condition": sentinel_condition,
            "true_sentinel_probability": float(
                rows[0]["true_sentinel_probability"]
            ),
            "policy": policy,
            "repetitions": len(rows),
        }
        for metric in (
            "target_exposures",
            "target_failures",
            "false_safe_exposures",
            "absolute_error",
        ):
            values = [float(row[metric]) for row in rows]
            item[f"{metric}_mean"] = mean(values)
            item[f"{metric}_sd"] = stdev(values) if len(values) > 1 else 0.0

        first_steps = [
            float(row["first_target_exposure_step"])
            for row in rows
            if row["first_target_exposure_step"] is not None
        ]
        item["first_target_exposure_step_mean"] = (
            mean(first_steps) if first_steps else None
        )
        item["target_exposure_repetition_rate"] = (
            sum(int(row["target_exposures"]) > 0 for row in rows) / len(rows)
        )
        summary.append(item)

    return {
        "metadata": {
            "seed": seed,
            "repetitions": repetitions,
            "opportunities_per_condition": opportunities,
            "target_probabilities": [0.1, 0.3, 0.5, 0.7],
            "minimum_return_probabilities": [0.5, 0.7, 0.9],
            "confidence": 0.90,
            "scope": (
                "G3 side-information identifiability study; sentinel transfer "
                "requires a declared shared-parameter assumption"
            ),
        },
        "raw": raw,
        "summary": summary,
    }
