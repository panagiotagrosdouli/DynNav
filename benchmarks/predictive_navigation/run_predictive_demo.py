#!/usr/bin/env python3
"""Predictive navigation benchmark demo.

Run from repository root:

    python benchmarks/predictive_navigation/run_predictive_demo.py
"""

from __future__ import annotations

import csv
from pathlib import Path

from dynnav.planners import GridMap, self_aware_astar
from dynnav.planners.predictive_self_aware_astar import (
    PredictiveSelfAwareAStarWeights,
    predictive_self_aware_astar,
)
from dynnav.prediction import ConstantVelocityRiskPredictor, MovingRiskSource

RESULT_PATH = Path("results/predictive_navigation_demo.csv")
REPORT_PATH = Path("results/predictive_navigation_demo.md")


def path_metrics(predictive_risk, path):
    return {
        "path_length": float(max(0, len(path) - 1)),
        "predicted_mean_risk": predictive_risk.mean_risk_along(path),
        "predicted_max_risk": predictive_risk.max_risk_along(path),
        "avoids_future_hazard": 1.0 if predictive_risk.max_risk_along(path) < 0.8 else 0.0,
    }


def main() -> None:
    grid = GridMap.from_obstacles(width=8, height=3)
    predictor = ConstantVelocityRiskPredictor(
        sources=(MovingRiskSource(position=(1, 1), velocity=(1, 0), risk=0.9, radius=0),)
    )
    predictive_risk = predictor.predict(grid, horizon=8)

    baseline = self_aware_astar(grid, (0, 1), (7, 1))
    predictive = predictive_self_aware_astar(
        grid,
        predictive_risk,
        (0, 1),
        (7, 1),
        PredictiveSelfAwareAStarWeights(
            current_risk_cost=0.0,
            predicted_risk_cost=10.0,
            uncertainty_cost=0.0,
            information_gain_reward=0.0,
        ),
    )

    rows = []
    for method, result in [
        ("self_aware_astar", baseline),
        ("predictive_self_aware_astar", predictive),
    ]:
        metrics = path_metrics(predictive_risk, result.path)
        rows.append(
            {
                "module_id": "C29",
                "experiment_name": "predictive_dynamic_risk_demo",
                "seed": 0,
                "scenario": "constant_velocity_moving_hazard",
                "method": method,
                "baseline": "self_aware_astar",
                "n_trials": 1,
                "success_rate": 1.0 if result.success else 0.0,
                "collision_rate": 1.0 if metrics["predicted_max_risk"] >= 0.8 else 0.0,
                "path_length": metrics["path_length"],
                "time_to_goal": metrics["path_length"],
                "replans": 0,
                "nodes_expanded": result.nodes_expanded,
                "mean_risk": metrics["predicted_mean_risk"],
                "max_risk": metrics["predicted_max_risk"],
                "cvar_risk": metrics["predicted_max_risk"],
                "uncertainty_integral": 0.0,
                "information_gain": 0.0,
                "recoverability": 1.0 - metrics["predicted_max_risk"],
                "avoids_future_hazard": metrics["avoids_future_hazard"],
                "intervention_rate": 0.0,
                "compute_time_ms": result.planning_time_ms,
                "planner_cost": result.cost,
                "path": result.path,
            }
        )

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULT_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# Predictive Dynamic Risk Demo",
        "",
        "This benchmark compares planning with current risk only against planning with time-indexed predicted risk.",
        "",
        "| Method | Success | Path length | Predicted max risk | Avoids future hazard | Nodes expanded |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['method']} | {row['success_rate']} | {row['path_length']} | "
            f"{float(row['max_risk']):.3f} | {row['avoids_future_hazard']} | {row['nodes_expanded']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The predictive planner should avoid cells that are currently safe but predicted to become risky at the time of arrival.",
            "This is a controlled synthetic demonstration, not a real-robot validation.",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {RESULT_PATH}")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
