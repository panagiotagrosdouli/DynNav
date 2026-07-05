#!/usr/bin/env python3
"""Minimal benchmark for self-aware active navigation.

This script is intentionally small and deterministic. It compares candidate
paths using the first DynNav self-aware objective and writes a CSV artifact that
matches the repository benchmark protocol.

Run from the repository root:

    python benchmarks/self_aware_navigation/run_self_aware_demo.py
"""

from __future__ import annotations

import csv
import time
from pathlib import Path

from dynnav.core import (
    PathEvaluation,
    SelfAwareCostWeights,
    expected_information_gain,
    self_aware_path_cost,
)


RESULT_PATH = Path("results/self_aware_navigation_demo.csv")


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _cvar(values: list[float], quantile: float = 0.8) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    start = int(len(ordered) * quantile)
    tail = ordered[start:] or [ordered[-1]]
    return _mean(tail)


def evaluate_candidate(name: str, path: list[tuple[int, int]], risk: dict[tuple[int, int], float], belief: dict[tuple[int, int], float]) -> dict[str, object]:
    start = time.perf_counter()

    risk_values = [risk.get(cell, 0.0) for cell in path]
    information_gain = expected_information_gain(path, belief, sensor_radius=1)
    map_uncertainty = information_gain
    recoverability = max(0.0, 1.0 - max(risk_values or [0.0]))

    evaluation = PathEvaluation(
        path=path,
        path_length=float(max(0, len(path) - 1)),
        expected_collision_risk=_mean(risk_values),
        cvar_tail_risk=_cvar(risk_values),
        localization_uncertainty=0.25,
        map_uncertainty=map_uncertainty,
        information_gain=information_gain,
        recoverability=recoverability,
        compute_time_ms=(time.perf_counter() - start) * 1000.0,
    )

    cost = self_aware_path_cost(
        evaluation,
        SelfAwareCostWeights(
            alpha_length=1.0,
            beta_expected_risk=6.0,
            gamma_cvar_risk=4.0,
            delta_localization_uncertainty=2.0,
            eta_map_uncertainty=1.5,
            zeta_irreversibility=3.0,
            kappa_information_gain=2.5,
        ),
    )

    return {
        "candidate": name,
        "cost": cost,
        "path_length": evaluation.path_length,
        "mean_risk": evaluation.expected_collision_risk,
        "max_risk": max(risk_values or [0.0]),
        "cvar_risk": evaluation.cvar_tail_risk,
        "map_uncertainty": evaluation.map_uncertainty,
        "information_gain": evaluation.information_gain,
        "recoverability": evaluation.recoverability,
        "compute_time_ms": evaluation.compute_time_ms,
    }


def main() -> None:
    # Synthetic scenario: the short path is efficient but crosses higher risk.
    # The active path is longer, sees uncertain cells, and preserves recovery.
    risk = {
        (0, 0): 0.05,
        (1, 0): 0.20,
        (2, 0): 0.75,
        (3, 0): 0.70,
        (4, 0): 0.25,
        (5, 0): 0.05,
        (0, 1): 0.05,
        (1, 1): 0.10,
        (2, 1): 0.15,
        (3, 1): 0.20,
        (4, 1): 0.10,
        (5, 1): 0.05,
    }
    belief = {
        (0, 0): 0.10,
        (1, 0): 0.20,
        (2, 0): 0.70,
        (3, 0): 0.70,
        (4, 0): 0.20,
        (5, 0): 0.10,
        (0, 1): 0.50,
        (1, 1): 0.50,
        (2, 1): 0.50,
        (3, 1): 0.50,
        (4, 1): 0.50,
        (5, 1): 0.50,
    }

    candidates = {
        "shortest_path": [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0)],
        "self_aware_active_path": [(0, 0), (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (5, 0)],
    }

    rows = [evaluate_candidate(name, path, risk, belief) for name, path in candidates.items()]
    selected = min(rows, key=lambda row: float(row["cost"]))

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULT_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "module_id",
                "experiment_name",
                "seed",
                "scenario",
                "method",
                "baseline",
                "n_trials",
                "success_rate",
                "collision_rate",
                "path_length",
                "time_to_goal",
                "replans",
                "mean_risk",
                "max_risk",
                "cvar_risk",
                "uncertainty_integral",
                "information_gain",
                "recoverability",
                "intervention_rate",
                "compute_time_ms",
                "selected_candidate",
                "cost",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "module_id": "C27",
                    "experiment_name": "self_aware_active_navigation_demo",
                    "seed": 0,
                    "scenario": "synthetic_uncertain_corridor",
                    "method": row["candidate"],
                    "baseline": "shortest_path",
                    "n_trials": 1,
                    "success_rate": 1.0,
                    "collision_rate": 0.0 if row["max_risk"] < 0.8 else 1.0,
                    "path_length": row["path_length"],
                    "time_to_goal": row["path_length"],
                    "replans": 0,
                    "mean_risk": row["mean_risk"],
                    "max_risk": row["max_risk"],
                    "cvar_risk": row["cvar_risk"],
                    "uncertainty_integral": row["map_uncertainty"],
                    "information_gain": row["information_gain"],
                    "recoverability": row["recoverability"],
                    "intervention_rate": 0.0,
                    "compute_time_ms": row["compute_time_ms"],
                    "selected_candidate": selected["candidate"],
                    "cost": row["cost"],
                }
            )

    print(f"Selected candidate: {selected['candidate']} with cost={selected['cost']:.3f}")
    print(f"Wrote {RESULT_PATH}")


if __name__ == "__main__":
    main()
