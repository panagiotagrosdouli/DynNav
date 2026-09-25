"""Multi-seed replication for the post-V1 G3 risk-budget frontier."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from statistics import mean, stdev
from typing import Any

from dynnav.experiments.risk_budget_learning_benchmark import (
    run_risk_budget_learning_benchmark,
)


def run_risk_budget_replication(
    *,
    opportunities: int = 1_000,
    repetitions: int = 10,
    seed: int = 20260925,
) -> dict[str, object]:
    """Run the frozen post-V1 risk-budget grid over independent repetitions."""

    if opportunities <= 0:
        raise ValueError("opportunities must be positive")
    if repetitions <= 0:
        raise ValueError("repetitions must be positive")

    raw: list[dict[str, object]] = []
    condition = 0
    for true_probability in (0.1, 0.3, 0.5, 0.7):
        for minimum_return in (0.5, 0.7, 0.9):
            for repetition in range(repetitions):
                rows = run_risk_budget_learning_benchmark(
                    opportunities=opportunities,
                    true_closure_probability=true_probability,
                    minimum_return_probability=minimum_return,
                    confidence=0.90,
                    budgets=(5.0, 20.0, 50.0),
                    seed=seed + 10_000 + condition * 101 + repetition,
                )
                for row in rows:
                    item = asdict(row)
                    item["repetition"] = repetition
                    raw.append(item)
            condition += 1

    grouped: dict[tuple[float, float, str], list[dict[str, object]]] = defaultdict(list)
    for row in raw:
        key = (
            float(row["true_closure_probability"]),
            float(row["minimum_return_probability"]),
            str(row["policy"]),
        )
        grouped[key].append(row)

    summary: list[dict[str, Any]] = []
    for (true_probability, minimum_return, policy), rows in sorted(grouped.items()):
        item: dict[str, Any] = {
            "true_closure_probability": true_probability,
            "minimum_return_probability": minimum_return,
            "policy": policy,
            "repetitions": len(rows),
        }
        for metric in (
            "exposures",
            "exploratory_exposures",
            "return_failures",
            "absolute_error",
            "budget_spent",
        ):
            values = [float(row[metric]) for row in rows]
            item[f"{metric}_mean"] = mean(values)
            item[f"{metric}_sd"] = stdev(values) if len(values) > 1 else 0.0
        summary.append(item)

    return {
        "metadata": {
            "seed": seed,
            "repetitions": repetitions,
            "opportunities_per_condition": opportunities,
            "scope": "post-V1 exploratory multi-seed replication; not deployment safety",
        },
        "raw": raw,
        "summary": summary,
    }
