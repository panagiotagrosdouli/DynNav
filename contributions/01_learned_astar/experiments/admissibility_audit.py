"""Admissibility and consistency audit for Contribution 01.

This script evaluates whether a learned heuristic overestimates the exact
shortest-path cost-to-go on randomly sampled grid tasks.

Why this matters
----------------
A* preserves optimality when the heuristic is admissible. A raw neural heuristic
can reduce expansions, but it may overestimate true cost-to-go. This script makes
that risk measurable instead of implicit.

Run from the repository root:

    python contributions/01_learned_astar/experiments/admissibility_audit.py

Outputs:

    contributions/01_learned_astar/results/c01_admissibility_audit.csv
    contributions/01_learned_astar/results/c01_admissibility_summary.csv
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
from collections import deque
from pathlib import Path
from statistics import mean

import numpy as np

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from astar_learned_heuristic import LearnedHeuristicWrapper, astar_search, manhattan  # noqa: E402

Node = tuple[int, int]
Grid = np.ndarray

RESULTS_DIR = Path("contributions/01_learned_astar/results")
DEFAULT_AUDIT_OUT = RESULTS_DIR / "c01_admissibility_audit.csv"
DEFAULT_SUMMARY_OUT = RESULTS_DIR / "c01_admissibility_summary.csv"

SCENARIOS = [
    ("easy", 0.10),
    ("medium", 0.20),
    ("hard", 0.30),
    ("very_hard", 0.40),
]


def make_random_grid(size: int, obstacle_density: float, rng: random.Random) -> Grid:
    grid = np.zeros((size, size), dtype=np.int32)
    n_cells = size * size
    n_obstacles = int(round(n_cells * obstacle_density))
    candidates = [(x, y) for y in range(1, size - 1) for x in range(1, size - 1)]
    for x, y in rng.sample(candidates, min(n_obstacles, len(candidates))):
        grid[y, x] = 1
    return grid


def is_free(grid: Grid, node: Node) -> bool:
    x, y = node
    height, width = grid.shape
    return 0 <= x < width and 0 <= y < height and grid[y, x] == 0


def free_cells(grid: Grid) -> list[Node]:
    height, width = grid.shape
    return [(x, y) for y in range(height) for x in range(width) if grid[y, x] == 0]


def reverse_bfs_cost_to_goal(grid: Grid, goal: Node) -> dict[Node, int]:
    """Compute exact shortest-path cost-to-go for every reachable free cell."""
    if not is_free(grid, goal):
        return {}

    costs: dict[Node, int] = {goal: 0}
    q: deque[Node] = deque([goal])

    while q:
        x, y = q.popleft()
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nxt = (x + dx, y + dy)
            if nxt not in costs and is_free(grid, nxt):
                costs[nxt] = costs[(x, y)] + 1
                q.append(nxt)
    return costs


def sample_task(size: int, obstacle_density: float, rng: random.Random, min_reachable: int) -> tuple[Grid, Node, dict[Node, int]]:
    for _ in range(500):
        grid = make_random_grid(size, obstacle_density, rng)
        cells = free_cells(grid)
        if not cells:
            continue
        goal = rng.choice(cells)
        exact_cost = reverse_bfs_cost_to_goal(grid, goal)
        if len(exact_cost) >= min_reachable:
            return grid, goal, exact_cost
    raise RuntimeError("Could not sample a sufficiently connected map. Try lower density or smaller min_reachable.")


def consistency_gap(grid: Grid, node: Node, goal: Node, heuristic) -> float:
    """Return max(h(n) - 1 - h(n')) over free neighbours; positive means inconsistent."""
    x, y = node
    h_node = heuristic.h(node, goal, grid)
    gaps: list[float] = []
    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        nxt = (x + dx, y + dy)
        if is_free(grid, nxt):
            gaps.append(h_node - 1.0 - heuristic.h(nxt, goal, grid))
    return max(gaps) if gaps else 0.0


def audit_method(
    method: str,
    heuristic: LearnedHeuristicWrapper,
    grid: Grid,
    goal: Node,
    exact_cost: dict[Node, int],
    sampled_nodes: list[Node],
    scenario: str,
    task_id: str,
) -> list[dict[str, float | int | str]]:
    rows: list[dict[str, float | int | str]] = []
    for node in sampled_nodes:
        true_cost = exact_cost[node]
        h_value = heuristic.h(node, goal, grid)
        overestimate = h_value - true_cost
        gap = consistency_gap(grid, node, goal, heuristic)
        rows.append(
            {
                "task_id": task_id,
                "scenario": scenario,
                "method": method,
                "node": str(node),
                "goal": str(goal),
                "true_cost_to_goal": true_cost,
                "heuristic_value": h_value,
                "overestimate": overestimate,
                "admissibility_violation": int(overestimate > 1e-9),
                "consistency_gap": gap,
                "consistency_violation": int(gap > 1e-9),
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, float | int | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"No rows to write to {path}.")
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def summarise(rows: list[dict[str, float | int | str]]) -> list[dict[str, float | int | str]]:
    grouped: dict[tuple[str, str], list[dict[str, float | int | str]]] = {}
    for row in rows:
        grouped.setdefault((str(row["scenario"]), str(row["method"])), []).append(row)

    summary: list[dict[str, float | int | str]] = []
    for (scenario, method), group in sorted(grouped.items()):
        overestimates = [float(r["overestimate"]) for r in group]
        positive_overestimates = [x for x in overestimates if x > 1e-9]
        consistency_gaps = [float(r["consistency_gap"]) for r in group]
        positive_gaps = [x for x in consistency_gaps if x > 1e-9]
        summary.append(
            {
                "scenario": scenario,
                "method": method,
                "n_states": len(group),
                "admissibility_violations": sum(int(r["admissibility_violation"]) for r in group),
                "admissibility_violation_rate": sum(int(r["admissibility_violation"]) for r in group) / len(group),
                "max_overestimate": max(overestimates),
                "mean_positive_overestimate": mean(positive_overestimates) if positive_overestimates else 0.0,
                "consistency_violations": sum(int(r["consistency_violation"]) for r in group),
                "consistency_violation_rate": sum(int(r["consistency_violation"]) for r in group) / len(group),
                "max_consistency_gap": max(consistency_gaps),
                "mean_positive_consistency_gap": mean(positive_gaps) if positive_gaps else 0.0,
            }
        )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="C01 heuristic admissibility and consistency audit.")
    parser.add_argument("--grid-size", type=int, default=40)
    parser.add_argument("--tasks-per-density", type=int, default=25)
    parser.add_argument("--states-per-task", type=int, default=100)
    parser.add_argument("--min-reachable", type=int, default=250)
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--model", type=Path, default=Path("heuristic_net_rich.pt"))
    parser.add_argument("--audit-out", type=Path, default=DEFAULT_AUDIT_OUT)
    parser.add_argument("--summary-out", type=Path, default=DEFAULT_SUMMARY_OUT)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    raw_h = LearnedHeuristicWrapper(model_path=args.model, mode="raw", allow_missing_model=True)
    clipped_h = LearnedHeuristicWrapper(model_path=args.model, mode="manhattan_clipped", allow_missing_model=True)
    zero_h = LearnedHeuristicWrapper(model_path=args.model, mode="zero", allow_missing_model=True)

    methods = [
        ("zero_h0", zero_h),
        ("manhattan", LearnedHeuristicWrapper(model_path=args.model, mode="raw", allow_missing_model=True)),
        ("learned_raw", raw_h),
        ("learned_manhattan_clipped", clipped_h),
    ]

    # Replace the fallback/raw wrapper for Manhattan with a small object exposing .h.
    class ManhattanWrapper:
        def h(self, node: Node, goal: Node, grid: Grid) -> float:
            return manhattan(node, goal)

    methods[1] = ("manhattan", ManhattanWrapper())

    rows: list[dict[str, float | int | str]] = []
    for scenario, density in SCENARIOS:
        for task_idx in range(args.tasks_per_density):
            grid, goal, exact_cost = sample_task(args.grid_size, density, rng, args.min_reachable)
            reachable_nodes = list(exact_cost.keys())
            sampled_nodes = rng.sample(reachable_nodes, min(args.states_per_task, len(reachable_nodes)))
            task_id = f"{scenario}_{task_idx:04d}"
            print(f"[{scenario}] task {task_idx + 1}/{args.tasks_per_density}: goal={goal}, audited_states={len(sampled_nodes)}")
            for method, heuristic in methods:
                rows.extend(audit_method(method, heuristic, grid, goal, exact_cost, sampled_nodes, scenario, task_id))

    summary = summarise(rows)
    write_csv(args.audit_out, rows)
    write_csv(args.summary_out, summary)

    print(f"Saved state-level audit to {args.audit_out}")
    print(f"Saved summary audit to {args.summary_out}")
    print("Use the summary to support admissibility/consistency claims.")


if __name__ == "__main__":
    main()
