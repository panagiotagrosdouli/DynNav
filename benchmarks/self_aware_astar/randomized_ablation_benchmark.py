#!/usr/bin/env python3
"""Randomized ablation benchmark for SelfAwareAStar.

This benchmark evaluates whether the self-aware terms improve risk and
recoverability across multiple synthetic maps rather than a single hand-designed
corridor.

Run from repository root:

    python benchmarks/self_aware_astar/randomized_ablation_benchmark.py --seeds 50
"""

from __future__ import annotations

import argparse
import csv
import random
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, pstdev

from dynnav.core.information_gain import expected_information_gain
from dynnav.planners import GridMap, SelfAwareAStarWeights, astar, self_aware_astar

RESULT_PATH = Path("results/self_aware_astar_randomized_ablation.csv")
REPORT_PATH = Path("results/self_aware_astar_randomized_ablation.md")


@dataclass(frozen=True)
class PlannerConfig:
    name: str
    weights: SelfAwareAStarWeights | None


def build_random_grid(seed: int, width: int = 14, height: int = 9) -> GridMap:
    """Create a deterministic random grid with risk and uncertainty fields."""
    rng = random.Random(seed)
    start = (0, height // 2)
    goal = (width - 1, height // 2)

    obstacles: set[tuple[int, int]] = set()
    risk: dict[tuple[int, int], float] = {}
    uncertainty: dict[tuple[int, int], float] = {}

    for x in range(width):
        for y in range(height):
            cell = (x, y)
            if cell in (start, goal):
                continue

            # Keep the map mostly traversable, but introduce sparse obstacles.
            if rng.random() < 0.10 and y not in (height // 2, height // 2 + 1):
                obstacles.add(cell)
                continue

            # Risk corridor near the middle, plus random local hazards.
            corridor_bias = 0.45 if abs(y - height // 2) <= 1 and 3 <= x <= width - 4 else 0.0
            random_hazard = 0.45 if rng.random() < 0.12 else 0.0
            risk[cell] = min(1.0, 0.05 + corridor_bias + random_hazard + 0.15 * rng.random())

            # Unknown side regions encourage information-gathering detours.
            side_uncertainty = 0.55 if y in (1, height - 2) else 0.0
            uncertainty[cell] = min(1.0, 0.15 + side_uncertainty + 0.25 * rng.random())

    return GridMap.from_obstacles(width=width, height=height, obstacles=obstacles, risk=risk, uncertainty=uncertainty)


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
        "mean_risk": mean(risks),
        "max_risk": max(risks),
        "mean_uncertainty": mean(uncertainties),
        "information_gain": expected_information_gain(path, grid.occupancy_belief(), sensor_radius=1),
        "recoverability": 1.0 - max(risks),
    }


def run_planner(config: PlannerConfig, grid: GridMap, start: tuple[int, int], goal: tuple[int, int]):
    if config.weights is None:
        return astar(grid, start, goal)
    return self_aware_astar(grid, start, goal, config.weights)


def configs() -> list[PlannerConfig]:
    return [
        PlannerConfig("classic_astar", None),
        PlannerConfig(
            "self_aware_full",
            SelfAwareAStarWeights(
                risk_cost=8.0,
                uncertainty_cost=0.5,
                low_recoverability_cost=4.0,
                information_gain_reward=0.8,
            ),
        ),
        PlannerConfig(
            "ablation_no_risk",
            SelfAwareAStarWeights(
                risk_cost=0.0,
                uncertainty_cost=0.5,
                low_recoverability_cost=0.0,
                information_gain_reward=0.8,
            ),
        ),
        PlannerConfig(
            "ablation_no_uncertainty",
            SelfAwareAStarWeights(
                risk_cost=8.0,
                uncertainty_cost=0.0,
                low_recoverability_cost=4.0,
                information_gain_reward=0.8,
            ),
        ),
        PlannerConfig(
            "ablation_no_information_gain",
            SelfAwareAStarWeights(
                risk_cost=8.0,
                uncertainty_cost=0.5,
                low_recoverability_cost=4.0,
                information_gain_reward=0.0,
            ),
        ),
    ]


def run_benchmark(n_seeds: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for seed in range(n_seeds):
        grid = build_random_grid(seed)
        start = (0, grid.height // 2)
        goal = (grid.width - 1, grid.height // 2)
        for config in configs():
            result = run_planner(config, grid, start, goal)
            metrics = path_metrics(grid, result.path)
            rows.append(
                {
                    "module_id": "C27",
                    "experiment_name": "self_aware_astar_randomized_ablation",
                    "seed": seed,
                    "scenario": "randomized_risk_uncertainty_grid",
                    "method": config.name,
                    "baseline": "classic_astar",
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
                }
            )
    return rows


def aggregate(rows: list[dict[str, object]]) -> dict[str, dict[str, float]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(str(row["method"]), []).append(row)

    metrics = [
        "success_rate",
        "collision_rate",
        "path_length",
        "nodes_expanded",
        "mean_risk",
        "max_risk",
        "information_gain",
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


def write_csv(rows: list[dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_report(summary: dict[str, dict[str, float]], path: Path, n_seeds: int) -> None:
    lines = [
        "# SelfAwareAStar Randomized Ablation Benchmark",
        "",
        f"Trials: {n_seeds} randomized maps per method.",
        "",
        "| Method | Success | Collision proxy | Path length | Mean risk | Max risk | Info gain | Recoverability | Nodes expanded |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for method, stats in sorted(summary.items()):
        lines.append(
            f"| {method} | {stats['success_rate_mean']:.3f} | {stats['collision_rate_mean']:.3f} | "
            f"{stats['path_length_mean']:.2f} ± {stats['path_length_std']:.2f} | "
            f"{stats['mean_risk_mean']:.3f} | {stats['max_risk_mean']:.3f} | "
            f"{stats['information_gain_mean']:.3f} | {stats['recoverability_mean']:.3f} | "
            f"{stats['nodes_expanded_mean']:.1f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This benchmark tests whether the full self-aware objective improves risk and recoverability across randomized synthetic maps.",
            "Ablations isolate the contribution of risk, uncertainty, and information-gain terms.",
            "",
            "## Limitation",
            "",
            "The benchmark is still synthetic and uses a collision proxy based on high-risk cells. It should be treated as controlled algorithmic evidence, not real-robot validation.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=50, help="Number of randomized maps to evaluate.")
    parser.add_argument("--csv", type=Path, default=RESULT_PATH, help="CSV output path.")
    parser.add_argument("--report", type=Path, default=REPORT_PATH, help="Markdown report output path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = run_benchmark(args.seeds)
    write_csv(rows, args.csv)
    write_report(aggregate(rows), args.report, args.seeds)
    print(f"Wrote {args.csv}")
    print(f"Wrote {args.report}")


if __name__ == "__main__":
    main()
