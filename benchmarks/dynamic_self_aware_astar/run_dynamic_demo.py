#!/usr/bin/env python3
"""Dynamic SelfAwareAStar benchmark demo.

Run from repository root:

    python benchmarks/dynamic_self_aware_astar/run_dynamic_demo.py
"""

from __future__ import annotations

import csv
from pathlib import Path

from dynnav.planners.dynamic_self_aware_astar import (
    DynamicSelfAwareAStarConfig,
    apply_grid_updates,
    dynamic_self_aware_astar,
)
from dynnav.planners.grid_map import GridCell, GridMap
from dynnav.planners.self_aware_astar import SelfAwareAStarWeights

RESULT_PATH = Path("results/dynamic_self_aware_astar_demo.csv")
REPORT_PATH = Path("results/dynamic_self_aware_astar_demo.md")


def build_initial_grid() -> GridMap:
    risk = {(x, 1): 0.10 for x in range(10)}
    risk.update({(x, 0): 0.20 for x in range(10)})
    uncertainty = {(x, 1): 0.60 for x in range(10)}
    uncertainty.update({(x, 0): 0.20 for x in range(10)})
    return GridMap.from_obstacles(width=10, height=3, obstacles={(4, 2)}, risk=risk, uncertainty=uncertainty)


def dynamic_update(step: int, grid: GridMap, current: GridCell) -> GridMap:
    # At step 2, the initially attractive corridor becomes blocked.
    if step == 2:
        return apply_grid_updates(grid, obstacles_to_add={(4, 1), (5, 1)})
    # At step 4, a future part of the fallback route becomes high-risk.
    if step == 4:
        return apply_grid_updates(grid, risk_updates={(6, 0): 0.85, (7, 0): 0.85})
    return grid


def main() -> None:
    grid = build_initial_grid()
    result = dynamic_self_aware_astar(
        initial_grid=grid,
        start=(0, 1),
        goal=(9, 1),
        map_update_fn=dynamic_update,
        config=DynamicSelfAwareAStarConfig(
            weights=SelfAwareAStarWeights(
                risk_cost=8.0,
                uncertainty_cost=0.3,
                low_recoverability_cost=4.0,
                information_gain_reward=0.8,
            ),
            risk_replan_threshold=0.75,
            max_steps=64,
        ),
    )

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "module_id": "C28",
        "experiment_name": "dynamic_self_aware_astar_demo",
        "seed": 0,
        "scenario": "dynamic_corridor_blockage_and_risk_spike",
        "method": "dynamic_self_aware_astar",
        "baseline": "static_self_aware_astar",
        "n_trials": 1,
        "success_rate": 1.0 if result.success else 0.0,
        "collision_rate": 1.0 if result.max_risk >= 0.95 else 0.0,
        "path_length": float(max(0, len(result.path) - 1)),
        "time_to_goal": result.steps,
        "replans": result.replans,
        "blocked_replans": result.blocked_replans,
        "risk_replans": result.risk_replans,
        "nodes_expanded": result.total_nodes_expanded,
        "mean_risk": result.mean_risk,
        "max_risk": result.max_risk,
        "cvar_risk": result.max_risk,
        "uncertainty_integral": 0.0,
        "information_gain": result.information_gain,
        "recoverability": result.recoverability,
        "intervention_rate": 0.0,
        "compute_time_ms": result.total_planning_time_ms,
        "failure_reason": result.failure_reason,
        "path": result.path,
    }
    with RESULT_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
        writer.writeheader()
        writer.writerow(row)

    report = "\n".join(
        [
            "# Dynamic SelfAwareAStar Demo",
            "",
            "This controlled demo introduces online replanning when the remaining path becomes blocked or too risky.",
            "",
            "| Metric | Value |",
            "|---|---:|",
            f"| Success | {row['success_rate']} |",
            f"| Path length | {row['path_length']} |",
            f"| Replans | {row['replans']} |",
            f"| Blocked replans | {row['blocked_replans']} |",
            f"| Risk replans | {row['risk_replans']} |",
            f"| Mean risk | {row['mean_risk']:.3f} |",
            f"| Max risk | {row['max_risk']:.3f} |",
            f"| Recoverability | {row['recoverability']:.3f} |",
            f"| Nodes expanded | {row['nodes_expanded']} |",
            "",
            "## Interpretation",
            "",
            "The demo verifies that DynNav can replan online when new map evidence invalidates the original route.",
            "This remains a synthetic benchmark, not a real-robot validation.",
        ]
    )
    REPORT_PATH.write_text(report + "\n", encoding="utf-8")
    print(f"Wrote {RESULT_PATH}")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
