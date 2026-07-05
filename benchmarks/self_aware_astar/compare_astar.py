#!/usr/bin/env python3
"""Compare classical A* with SelfAwareAStar on a synthetic risk corridor.

Run from repository root:

    python benchmarks/self_aware_astar/compare_astar.py
"""

from __future__ import annotations

import csv
from pathlib import Path

from dynnav.core.information_gain import expected_information_gain
from dynnav.planners import GridMap, SelfAwareAStarWeights, astar, self_aware_astar

RESULT_PATH = Path("results/self_aware_astar_comparison.csv")
REPORT_PATH = Path("results/self_aware_astar_comparison.md")


def path_metrics(grid: GridMap, path: list[tuple[int, int]]) -> dict[str, float]:
    if not path:
        return {
            "path_length": 0.0,
            "mean_risk": 0.0,
            "max_risk": 0.0,
            "mean_uncertainty": 0.0,
            "information_gain": 0.0,
            "recoverability": 0.0,
        }
    risks = [grid.cell_risk(cell) for cell in path]
    uncertainties = [grid.cell_uncertainty(cell) for cell in path]
    return {
        "path_length": float(max(0, len(path) - 1)),
        "mean_risk": sum(risks) / len(risks),
        "max_risk": max(risks),
        "mean_uncertainty": sum(uncertainties) / len(uncertainties),
        "information_gain": expected_information_gain(path, grid.occupancy_belief(), sensor_radius=1),
        "recoverability": 1.0 - max(risks),
    }


def build_corridor_grid() -> GridMap:
    risk = {(x, 0): 0.85 for x in range(2, 8)}
    risk.update({(x, 1): 0.15 for x in range(10)})
    uncertainty = {(x, 1): 0.75 for x in range(10)}
    uncertainty.update({(x, 0): 0.20 for x in range(10)})
    obstacles = {(4, 2), (5, 2)}
    return GridMap.from_obstacles(width=10, height=3, obstacles=obstacles, risk=risk, uncertainty=uncertainty)


def main() -> None:
    grid = build_corridor_grid()
    start = (0, 0)
    goal = (9, 0)

    baseline = astar(grid, start, goal)
    aware = self_aware_astar(
        grid,
        start,
        goal,
        SelfAwareAStarWeights(
            risk_cost=8.0,
            uncertainty_cost=0.4,
            low_recoverability_cost=4.0,
            information_gain_reward=0.8,
        ),
    )

    rows = []
    for name, result, baseline_name in [
        ("classic_astar", baseline, "classic_astar"),
        ("self_aware_astar", aware, "classic_astar"),
    ]:
        metrics = path_metrics(grid, result.path)
        rows.append(
            {
                "module_id": "C27",
                "experiment_name": "self_aware_astar_corridor_comparison",
                "seed": 0,
                "scenario": "synthetic_risk_corridor",
                "method": name,
                "baseline": baseline_name,
                "n_trials": 1,
                "success_rate": 1.0 if result.success else 0.0,
                "collision_rate": 1.0 if metrics["max_risk"] >= 0.8 else 0.0,
                "path_length": metrics["path_length"],
                "time_to_goal": metrics["path_length"],
                "replans": 0,
                "nodes_expanded": result.nodes_expanded,
                "mean_risk": metrics["mean_risk"],
                "max_risk": metrics["max_risk"],
                "cvar_risk": metrics["max_risk"],
                "uncertainty_integral": metrics["mean_uncertainty"],
                "information_gain": metrics["information_gain"],
                "recoverability": metrics["recoverability"],
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

    report_lines = [
        "# SelfAwareAStar vs Classical A*",
        "",
        "Synthetic corridor benchmark comparing shortest-path planning with self-aware risk-sensitive planning.",
        "",
        "| Method | Success | Path length | Mean risk | Max risk | Information gain | Recoverability | Nodes expanded |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        report_lines.append(
            f"| {row['method']} | {row['success_rate']} | {row['path_length']} | "
            f"{float(row['mean_risk']):.3f} | {float(row['max_risk']):.3f} | "
            f"{float(row['information_gain']):.3f} | {float(row['recoverability']):.3f} | {row['nodes_expanded']} |"
        )
    report_lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This is a controlled prototype benchmark. It tests whether the self-aware planner can trade extra distance for lower risk and higher recoverability.",
            "It should not be interpreted as real-world performance evidence yet.",
        ]
    )
    REPORT_PATH.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"Wrote {RESULT_PATH}")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
