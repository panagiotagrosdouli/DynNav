#!/usr/bin/env python3
"""Dynamic replanning benchmark for SelfAwareAStar.

This benchmark simulates online navigation on a grid where obstacles and risk
values can change while the robot is executing a route. The robot replans from
its current cell whenever the next planned step becomes blocked or unsafe.

Run from repository root:

    python benchmarks/dynamic_replanning/dynamic_self_aware_replanning.py --seeds 30
"""

from __future__ import annotations

import argparse
import csv
import random
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

from dynnav.planners import GridMap, SelfAwareAStarWeights, astar, self_aware_astar

RESULT_PATH = Path("results/dynamic_self_aware_replanning.csv")
REPORT_PATH = Path("results/dynamic_self_aware_replanning.md")

GridCell = tuple[int, int]


@dataclass(frozen=True)
class DynamicRunResult:
    method: str
    seed: int
    success: bool
    collision_proxy: bool
    path_length: int
    replans: int
    blocked_events: int
    risk_spikes: int
    mean_risk: float
    max_risk: float
    recoverability: float
    nodes_expanded: int
    compute_time_ms: float


def base_grid(seed: int, width: int = 16, height: int = 9) -> GridMap:
    rng = random.Random(seed)
    obstacles: set[GridCell] = set()
    risk: dict[GridCell, float] = {}
    uncertainty: dict[GridCell, float] = {}

    start = (0, height // 2)
    goal = (width - 1, height // 2)

    for x in range(width):
        for y in range(height):
            cell = (x, y)
            if cell in (start, goal):
                continue
            if rng.random() < 0.07 and y not in (height // 2, height // 2 + 1):
                obstacles.add(cell)
                continue
            corridor_risk = 0.25 if y == height // 2 and 3 <= x <= width - 4 else 0.0
            risk[cell] = min(1.0, 0.05 + corridor_risk + 0.20 * rng.random())
            uncertainty[cell] = min(1.0, 0.20 + 0.35 * rng.random())

    return GridMap.from_obstacles(width=width, height=height, obstacles=obstacles, risk=risk, uncertainty=uncertainty)


def mutate_grid(grid: GridMap, rng: random.Random, robot: GridCell, goal: GridCell) -> tuple[GridMap, int, int]:
    """Return a mutated grid plus counts for blocked and risk-spike events."""
    obstacles = set(grid.obstacles)
    risk = dict(grid.risk)
    uncertainty = dict(grid.uncertainty)
    blocked_events = 0
    risk_spikes = 0

    candidate_cells = [
        (robot[0] + dx, robot[1] + dy)
        for dx, dy in [(1, 0), (2, 0), (1, 1), (1, -1)]
    ]
    candidate_cells = [c for c in candidate_cells if grid.in_bounds(c) and c not in {robot, goal}]

    if candidate_cells and rng.random() < 0.22:
        cell = rng.choice(candidate_cells)
        obstacles.add(cell)
        blocked_events += 1

    if candidate_cells and rng.random() < 0.35:
        cell = rng.choice(candidate_cells)
        risk[cell] = max(risk.get(cell, 0.0), 0.90)
        uncertainty[cell] = max(uncertainty.get(cell, 0.0), 0.80)
        risk_spikes += 1

    return GridMap.from_obstacles(grid.width, grid.height, obstacles, risk, uncertainty), blocked_events, risk_spikes


def plan(method: str, grid: GridMap, start: GridCell, goal: GridCell):
    if method == "classic_astar":
        return astar(grid, start, goal)
    if method == "dynamic_self_aware_astar":
        return self_aware_astar(
            grid,
            start,
            goal,
            SelfAwareAStarWeights(
                risk_cost=9.0,
                uncertainty_cost=0.8,
                low_recoverability_cost=4.0,
                information_gain_reward=0.8,
            ),
        )
    raise ValueError(f"unknown method: {method}")


def run_dynamic_episode(seed: int, method: str, max_steps: int = 80, risk_threshold: float = 0.85) -> DynamicRunResult:
    rng = random.Random(seed)
    grid = base_grid(seed)
    robot = (0, grid.height // 2)
    goal = (grid.width - 1, grid.height // 2)

    executed: list[GridCell] = [robot]
    risks: list[float] = []
    replans = 0
    blocked_events = 0
    risk_spikes = 0
    nodes_expanded = 0
    compute_time_ms = 0.0
    collision_proxy = False

    current_plan: list[GridCell] = []
    plan_index = 0

    for _ in range(max_steps):
        if robot == goal:
            break

        if not current_plan or plan_index >= len(current_plan) - 1:
            result = plan(method, grid, robot, goal)
            replans += 1
            nodes_expanded += result.nodes_expanded
            compute_time_ms += result.planning_time_ms
            if not result.success:
                break
            current_plan = result.path
            plan_index = 0

        next_cell = current_plan[plan_index + 1]
        grid, blocked_delta, risk_delta = mutate_grid(grid, rng, robot, goal)
        blocked_events += blocked_delta
        risk_spikes += risk_delta

        next_blocked = not grid.passable(next_cell)
        next_unsafe = grid.cell_risk(next_cell) >= risk_threshold

        if next_blocked or next_unsafe:
            result = plan(method, grid, robot, goal)
            replans += 1
            nodes_expanded += result.nodes_expanded
            compute_time_ms += result.planning_time_ms
            if not result.success:
                break
            current_plan = result.path
            plan_index = 0
            if len(current_plan) < 2:
                break
            next_cell = current_plan[1]

        risk = grid.cell_risk(next_cell)
        risks.append(risk)
        if risk >= risk_threshold:
            collision_proxy = True
        robot = next_cell
        executed.append(robot)
        plan_index += 1

    success = robot == goal
    max_risk = max(risks) if risks else 0.0
    return DynamicRunResult(
        method=method,
        seed=seed,
        success=success,
        collision_proxy=collision_proxy,
        path_length=max(0, len(executed) - 1),
        replans=replans,
        blocked_events=blocked_events,
        risk_spikes=risk_spikes,
        mean_risk=mean(risks) if risks else 0.0,
        max_risk=max_risk,
        recoverability=1.0 - max_risk,
        nodes_expanded=nodes_expanded,
        compute_time_ms=compute_time_ms,
    )


def run_benchmark(n_seeds: int) -> list[DynamicRunResult]:
    results: list[DynamicRunResult] = []
    for seed in range(n_seeds):
        for method in ["classic_astar", "dynamic_self_aware_astar"]:
            results.append(run_dynamic_episode(seed=seed, method=method))
    return results


def write_csv(results: list[DynamicRunResult], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
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
                "replans",
                "blocked_events",
                "risk_spikes",
                "nodes_expanded",
                "mean_risk",
                "max_risk",
                "cvar_risk",
                "recoverability",
                "compute_time_ms",
            ],
        )
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "module_id": "C28",
                    "experiment_name": "dynamic_self_aware_replanning",
                    "seed": result.seed,
                    "scenario": "online_mutating_risk_obstacle_grid",
                    "method": result.method,
                    "baseline": "classic_astar",
                    "n_trials": 1,
                    "success_rate": 1.0 if result.success else 0.0,
                    "collision_rate": 1.0 if result.collision_proxy else 0.0,
                    "path_length": result.path_length,
                    "replans": result.replans,
                    "blocked_events": result.blocked_events,
                    "risk_spikes": result.risk_spikes,
                    "nodes_expanded": result.nodes_expanded,
                    "mean_risk": result.mean_risk,
                    "max_risk": result.max_risk,
                    "cvar_risk": result.max_risk,
                    "recoverability": result.recoverability,
                    "compute_time_ms": result.compute_time_ms,
                }
            )


def aggregate(results: list[DynamicRunResult]) -> dict[str, dict[str, float]]:
    groups: dict[str, list[DynamicRunResult]] = {}
    for result in results:
        groups.setdefault(result.method, []).append(result)
    summary: dict[str, dict[str, float]] = {}
    for method, rows in groups.items():
        summary[method] = {
            "success_rate": mean([1.0 if r.success else 0.0 for r in rows]),
            "collision_rate": mean([1.0 if r.collision_proxy else 0.0 for r in rows]),
            "path_length": mean([r.path_length for r in rows]),
            "replans": mean([r.replans for r in rows]),
            "mean_risk": mean([r.mean_risk for r in rows]),
            "max_risk": mean([r.max_risk for r in rows]),
            "recoverability": mean([r.recoverability for r in rows]),
            "nodes_expanded": mean([r.nodes_expanded for r in rows]),
        }
    return summary


def write_report(results: list[DynamicRunResult], path: Path) -> None:
    summary = aggregate(results)
    lines = [
        "# Dynamic SelfAwareAStar Replanning Benchmark",
        "",
        "This benchmark simulates online replanning under changing obstacles and risk spikes.",
        "",
        "| Method | Success | Collision proxy | Path length | Replans | Mean risk | Max risk | Recoverability | Nodes expanded |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for method, stats in sorted(summary.items()):
        lines.append(
            f"| {method} | {stats['success_rate']:.3f} | {stats['collision_rate']:.3f} | "
            f"{stats['path_length']:.2f} | {stats['replans']:.2f} | {stats['mean_risk']:.3f} | "
            f"{stats['max_risk']:.3f} | {stats['recoverability']:.3f} | {stats['nodes_expanded']:.1f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The goal is to test whether risk-aware replanning reacts better than classical shortest-path replanning when the environment changes during execution.",
            "",
            "## Limitation",
            "",
            "This is still a synthetic grid benchmark. It does not model dynamics, actuation limits, sensor latency, or physics collisions.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=30, help="Number of dynamic episodes per method.")
    parser.add_argument("--csv", type=Path, default=RESULT_PATH, help="CSV output path.")
    parser.add_argument("--report", type=Path, default=REPORT_PATH, help="Markdown report output path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = run_benchmark(args.seeds)
    write_csv(results, args.csv)
    write_report(results, args.report)
    print(f"Wrote {args.csv}")
    print(f"Wrote {args.report}")


if __name__ == "__main__":
    main()
