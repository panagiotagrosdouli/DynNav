#!/usr/bin/env python3
"""Randomized dynamic benchmark for SelfAwareAStar.

This benchmark compares:

1. static_self_aware_astar: plans once and executes without replanning;
2. dynamic_self_aware_astar: replans when the remaining path becomes blocked or risky.

Run from repository root:

    python benchmarks/dynamic_self_aware_astar/randomized_dynamic_benchmark.py --seeds 50
"""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path
from statistics import mean, pstdev

from dynnav.core.information_gain import expected_information_gain
from dynnav.planners.dynamic_self_aware_astar import (
    DynamicSelfAwareAStarConfig,
    apply_grid_updates,
    dynamic_self_aware_astar,
)
from dynnav.planners.grid_map import GridCell, GridMap
from dynnav.planners.self_aware_astar import SelfAwareAStarWeights, self_aware_astar

RESULT_PATH = Path("results/dynamic_self_aware_astar_randomized.csv")
REPORT_PATH = Path("results/dynamic_self_aware_astar_randomized.md")


def build_grid(seed: int, width: int = 14, height: int = 7) -> GridMap:
    rng = random.Random(seed)
    risk: dict[GridCell, float] = {}
    uncertainty: dict[GridCell, float] = {}
    obstacles: set[GridCell] = set()
    mid = height // 2

    for x in range(width):
        for y in range(height):
            cell = (x, y)
            if cell in {(0, mid), (width - 1, mid)}:
                continue
            if rng.random() < 0.08 and y not in {mid, mid - 1, mid + 1}:
                obstacles.add(cell)
                continue
            corridor_risk = 0.18 if y == mid else 0.08
            uncertainty_boost = 0.55 if y in {mid - 1, mid + 1} else 0.15
            risk[cell] = min(1.0, corridor_risk + 0.25 * rng.random())
            uncertainty[cell] = min(1.0, uncertainty_boost + 0.20 * rng.random())

    return GridMap.from_obstacles(width=width, height=height, obstacles=obstacles, risk=risk, uncertainty=uncertainty)


def dynamic_updates_for_seed(seed: int):
    rng = random.Random(seed + 10_000)

    def update(step: int, grid: GridMap, current: GridCell) -> GridMap:
        # Introduce hazards ahead of the robot at deterministic but seed-specific times.
        updates: dict[GridCell, float] = {}
        obstacles: set[GridCell] = set()
        mid = grid.height // 2

        if step in {2, 4, 6}:
            x = min(grid.width - 2, current[0] + rng.randint(2, 4))
            if rng.random() < 0.55:
                obstacles.add((x, mid))
            else:
                updates[(x, mid)] = 0.90
                updates[(min(grid.width - 1, x + 1), mid)] = 0.82

        if not obstacles and not updates:
            return grid
        return apply_grid_updates(grid, obstacles_to_add=obstacles, risk_updates=updates)

    return update


def path_metrics(grid: GridMap, path: list[GridCell]) -> tuple[float, float, float, float]:
    if not path:
        return 0.0, 0.0, 0.0, 0.0
    risks = [grid.cell_risk(cell) for cell in path]
    mean_risk = mean(risks)
    max_risk = max(risks)
    information_gain = expected_information_gain(path, grid.occupancy_belief(), sensor_radius=1)
    recoverability = 1.0 - max_risk
    return mean_risk, max_risk, information_gain, recoverability


def run_static_execution(
    initial_grid: GridMap,
    start: GridCell,
    goal: GridCell,
    update_fn,
    weights: SelfAwareAStarWeights,
    max_steps: int,
) -> dict[str, object]:
    plan = self_aware_astar(initial_grid, start, goal, weights)
    grid = initial_grid
    executed = [start]
    current = start
    failure_reason = ""

    if not plan.success:
        failure_reason = "initial_plan_failed"
    else:
        remaining = plan.path[1:]
        for step in range(max_steps):
            if current == goal:
                break
            grid = update_fn(step, grid, current)
            if not remaining:
                failure_reason = "plan_exhausted"
                break
            next_cell = remaining.pop(0)
            if not grid.passable(next_cell):
                failure_reason = "blocked_static_path"
                break
            if grid.cell_risk(next_cell) >= 0.95:
                failure_reason = "high_risk_static_path"
                break
            current = next_cell
            executed.append(current)
        if current != goal and not failure_reason:
            failure_reason = "max_steps_exceeded"

    mean_risk, max_risk, info_gain, recoverability = path_metrics(grid, executed)
    return {
        "success": current == goal,
        "path": executed,
        "replans": 0,
        "blocked_replans": 0,
        "risk_replans": 0,
        "nodes_expanded": plan.nodes_expanded,
        "compute_time_ms": plan.planning_time_ms,
        "mean_risk": mean_risk,
        "max_risk": max_risk,
        "information_gain": info_gain,
        "recoverability": recoverability,
        "failure_reason": failure_reason,
    }


def run_dynamic_execution(
    initial_grid: GridMap,
    start: GridCell,
    goal: GridCell,
    update_fn,
    weights: SelfAwareAStarWeights,
    max_steps: int,
) -> dict[str, object]:
    result = dynamic_self_aware_astar(
        initial_grid=initial_grid,
        start=start,
        goal=goal,
        map_update_fn=update_fn,
        config=DynamicSelfAwareAStarConfig(
            weights=weights,
            max_steps=max_steps,
            risk_replan_threshold=0.75,
        ),
    )
    return {
        "success": result.success,
        "path": result.path,
        "replans": result.replans,
        "blocked_replans": result.blocked_replans,
        "risk_replans": result.risk_replans,
        "nodes_expanded": result.total_nodes_expanded,
        "compute_time_ms": result.total_planning_time_ms,
        "mean_risk": result.mean_risk,
        "max_risk": result.max_risk,
        "information_gain": result.information_gain,
        "recoverability": result.recoverability,
        "failure_reason": result.failure_reason,
    }


def row_from_result(seed: int, method: str, result: dict[str, object]) -> dict[str, object]:
    path = result["path"]
    assert isinstance(path, list)
    return {
        "module_id": "C28",
        "experiment_name": "dynamic_self_aware_astar_randomized",
        "seed": seed,
        "scenario": "randomized_dynamic_obstacle_and_risk_updates",
        "method": method,
        "baseline": "static_self_aware_astar",
        "n_trials": 1,
        "success_rate": 1.0 if result["success"] else 0.0,
        "collision_rate": 1.0 if float(result["max_risk"]) >= 0.95 or result["failure_reason"] == "blocked_static_path" else 0.0,
        "path_length": float(max(0, len(path) - 1)),
        "time_to_goal": float(max(0, len(path) - 1)),
        "replans": result["replans"],
        "blocked_replans": result["blocked_replans"],
        "risk_replans": result["risk_replans"],
        "nodes_expanded": result["nodes_expanded"],
        "mean_risk": result["mean_risk"],
        "max_risk": result["max_risk"],
        "cvar_risk": result["max_risk"],
        "uncertainty_integral": 0.0,
        "information_gain": result["information_gain"],
        "recoverability": result["recoverability"],
        "intervention_rate": 0.0,
        "compute_time_ms": result["compute_time_ms"],
        "failure_reason": result["failure_reason"],
    }


def run_benchmark(n_seeds: int, max_steps: int) -> list[dict[str, object]]:
    weights = SelfAwareAStarWeights(
        risk_cost=8.0,
        uncertainty_cost=0.3,
        low_recoverability_cost=4.0,
        information_gain_reward=0.8,
    )
    rows: list[dict[str, object]] = []
    for seed in range(n_seeds):
        grid = build_grid(seed)
        start = (0, grid.height // 2)
        goal = (grid.width - 1, grid.height // 2)
        update_fn = dynamic_updates_for_seed(seed)

        static_result = run_static_execution(grid, start, goal, update_fn, weights, max_steps)
        dynamic_result = run_dynamic_execution(grid, start, goal, dynamic_updates_for_seed(seed), weights, max_steps)

        rows.append(row_from_result(seed, "static_self_aware_astar", static_result))
        rows.append(row_from_result(seed, "dynamic_self_aware_astar", dynamic_result))
    return rows


def aggregate(rows: list[dict[str, object]]) -> dict[str, dict[str, float]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(str(row["method"]), []).append(row)
    metrics = [
        "success_rate",
        "collision_rate",
        "path_length",
        "replans",
        "nodes_expanded",
        "mean_risk",
        "max_risk",
        "recoverability",
        "compute_time_ms",
    ]
    summary: dict[str, dict[str, float]] = {}
    for method, method_rows in grouped.items():
        summary[method] = {}
        for metric in metrics:
            values = [float(row[metric]) for row in method_rows]
            summary[method][f"{metric}_mean"] = mean(values)
            summary[method][f"{metric}_std"] = pstdev(values) if len(values) > 1 else 0.0
    return summary


def write_outputs(rows: list[dict[str, object]], csv_path: Path, report_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary = aggregate(rows)
    lines = [
        "# Dynamic SelfAwareAStar Randomized Benchmark",
        "",
        "| Method | Success | Collision proxy | Path length | Replans | Mean risk | Max risk | Recoverability | Nodes expanded |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for method, stats in sorted(summary.items()):
        lines.append(
            f"| {method} | {stats['success_rate_mean']:.3f} | {stats['collision_rate_mean']:.3f} | "
            f"{stats['path_length_mean']:.2f} ± {stats['path_length_std']:.2f} | "
            f"{stats['replans_mean']:.2f} | {stats['mean_risk_mean']:.3f} | {stats['max_risk_mean']:.3f} | "
            f"{stats['recoverability_mean']:.3f} | {stats['nodes_expanded_mean']:.1f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This benchmark compares execution without replanning against online replanning under randomized dynamic obstacle and risk updates.",
            "It is still synthetic, but it directly tests whether dynamic replanning improves robustness after new map evidence arrives.",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=50, help="Number of randomized dynamic scenarios.")
    parser.add_argument("--max-steps", type=int, default=128, help="Maximum execution steps per scenario.")
    parser.add_argument("--csv", type=Path, default=RESULT_PATH, help="CSV output path.")
    parser.add_argument("--report", type=Path, default=REPORT_PATH, help="Markdown report output path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = run_benchmark(args.seeds, args.max_steps)
    write_outputs(rows, args.csv, args.report)
    print(f"Wrote {args.csv}")
    print(f"Wrote {args.report}")


if __name__ == "__main__":
    main()
