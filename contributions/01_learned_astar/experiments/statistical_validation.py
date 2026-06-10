"""Statistical validation benchmark for Contribution 01.

This script evaluates four planning variants on random obstacle-density maps:

- Dijkstra: A* with h=0.
- A* Manhattan: optimal 4-neighbour grid baseline.
- Learned Raw: neural heuristic without admissibility guarantee.
- Learned Clipped: min(h_theta, h_manhattan), admissible but conservative.

The goal is to make C01 scientifically auditable: every claim about expansions,
runtime, optimality preservation, and success rate should be traceable to the CSV
outputs produced here.

Run from the repository root:

    python contributions/01_learned_astar/experiments/statistical_validation.py

Outputs:

    contributions/01_learned_astar/results/c01_validation_trials.csv
    contributions/01_learned_astar/results/c01_validation_summary.csv
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median, stdev
from typing import Callable

import numpy as np

# Allow importing the local C01 core when the script is run from repo root.
THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from astar_learned_heuristic import (  # noqa: E402
    LearnedHeuristicWrapper,
    astar_learned,
    astar_search,
    manhattan,
)

Node = tuple[int, int]
Grid = np.ndarray

RESULTS_DIR = Path("contributions/01_learned_astar/results")
DEFAULT_TRIALS_OUT = RESULTS_DIR / "c01_validation_trials.csv"
DEFAULT_SUMMARY_OUT = RESULTS_DIR / "c01_validation_summary.csv"


@dataclass(frozen=True)
class Scenario:
    label: str
    obstacle_density: float


SCENARIOS = [
    Scenario("easy", 0.10),
    Scenario("medium", 0.20),
    Scenario("hard", 0.30),
    Scenario("very_hard", 0.40),
]


def make_random_grid(size: int, obstacle_density: float, rng: random.Random) -> Grid:
    """Create a random binary occupancy grid with the requested density."""
    grid = np.zeros((size, size), dtype=np.int32)
    n_cells = size * size
    n_obstacles = int(round(n_cells * obstacle_density))

    # Leave the outer border mostly usable to reduce impossible maps.
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


def has_path(grid: Grid, start: Node, goal: Node) -> bool:
    """Fast BFS reachability check, independent of the planners under test."""
    if not is_free(grid, start) or not is_free(grid, goal):
        return False
    q: deque[Node] = deque([start])
    seen = {start}
    while q:
        x, y = q.popleft()
        if (x, y) == goal:
            return True
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nxt = (x + dx, y + dy)
            if nxt not in seen and is_free(grid, nxt):
                seen.add(nxt)
                q.append(nxt)
    return False


def sample_reachable_task(
    size: int,
    obstacle_density: float,
    rng: random.Random,
    min_distance: int,
    max_attempts: int = 500,
) -> tuple[Grid, Node, Node]:
    """Sample a random map and a reachable non-trivial start-goal pair."""
    for _ in range(max_attempts):
        grid = make_random_grid(size, obstacle_density, rng)
        cells = free_cells(grid)
        if len(cells) < 2:
            continue
        for _ in range(100):
            start, goal = rng.sample(cells, 2)
            if manhattan(start, goal) < min_distance:
                continue
            if has_path(grid, start, goal):
                return grid, start, goal
    raise RuntimeError(
        f"Could not sample reachable task: size={size}, density={obstacle_density}, "
        f"min_distance={min_distance}. Try fewer trials or lower density."
    )


def path_len(path: list[Node] | None) -> int:
    return len(path) if path is not None else 0


def run_method(
    name: str,
    grid: Grid,
    start: Node,
    goal: Node,
    planner: Callable[[Grid, Node, Node], tuple[list[Node] | None, int]],
) -> dict[str, float | int | str]:
    t0 = time.perf_counter()
    path, expansions = planner(grid, start, goal)
    runtime_ms = (time.perf_counter() - t0) * 1_000.0
    return {
        "method": name,
        "success": int(path is not None),
        "path_len": path_len(path),
        "path_cost": max(path_len(path) - 1, 0),
        "expansions": expansions,
        "runtime_ms": runtime_ms,
    }


def summarise(values: list[float]) -> dict[str, float]:
    if not values:
        return {"mean": float("nan"), "std": float("nan"), "median": float("nan"), "min": float("nan"), "max": float("nan"), "ci95_low": float("nan"), "ci95_high": float("nan")}
    mu = mean(values)
    sd = stdev(values) if len(values) > 1 else 0.0
    half_width = 1.96 * sd / (len(values) ** 0.5) if len(values) > 1 else 0.0
    return {
        "mean": mu,
        "std": sd,
        "median": median(values),
        "min": min(values),
        "max": max(values),
        "ci95_low": mu - half_width,
        "ci95_high": mu + half_width,
    }


def build_summary(rows: list[dict[str, float | int | str]]) -> list[dict[str, float | int | str]]:
    groups: dict[tuple[str, str], list[dict[str, float | int | str]]] = defaultdict(list)
    for row in rows:
        groups[(str(row["scenario"]), str(row["method"]))].append(row)

    summary_rows: list[dict[str, float | int | str]] = []
    for (scenario, method), group in sorted(groups.items()):
        success_values = [float(r["success"]) for r in group]
        expansions_stats = summarise([float(r["expansions"]) for r in group])
        runtime_stats = summarise([float(r["runtime_ms"]) for r in group])
        cost_stats = summarise([float(r["path_cost"]) for r in group if int(r["success"]) == 1])

        entry: dict[str, float | int | str] = {
            "scenario": scenario,
            "method": method,
            "n": len(group),
            "success_rate": mean(success_values),
            "path_cost_mean": cost_stats["mean"],
            "path_cost_std": cost_stats["std"],
            "expansions_mean": expansions_stats["mean"],
            "expansions_std": expansions_stats["std"],
            "expansions_median": expansions_stats["median"],
            "expansions_ci95_low": expansions_stats["ci95_low"],
            "expansions_ci95_high": expansions_stats["ci95_high"],
            "runtime_ms_mean": runtime_stats["mean"],
            "runtime_ms_std": runtime_stats["std"],
            "runtime_ms_median": runtime_stats["median"],
            "runtime_ms_ci95_low": runtime_stats["ci95_low"],
            "runtime_ms_ci95_high": runtime_stats["ci95_high"],
        }
        summary_rows.append(entry)
    return summary_rows


def write_csv(path: Path, rows: list[dict[str, float | int | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"No rows to write to {path}.")
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="C01 statistical validation benchmark.")
    parser.add_argument("--grid-size", type=int, default=40)
    parser.add_argument("--trials-per-density", type=int, default=100)
    parser.add_argument("--min-distance", type=int, default=20)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--model", type=Path, default=Path("heuristic_net_rich.pt"))
    parser.add_argument("--trials-out", type=Path, default=DEFAULT_TRIALS_OUT)
    parser.add_argument("--summary-out", type=Path, default=DEFAULT_SUMMARY_OUT)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    raw_lh = LearnedHeuristicWrapper(model_path=args.model, mode="raw", allow_missing_model=True)
    clipped_lh = LearnedHeuristicWrapper(model_path=args.model, mode="manhattan_clipped", allow_missing_model=True)

    methods: list[tuple[str, Callable[[Grid, Node, Node], tuple[list[Node] | None, int]]]] = [
        ("dijkstra_h0", lambda grid, start, goal: astar_search(grid, start, goal, lambda *_: 0.0)),
        ("astar_manhattan", lambda grid, start, goal: astar_search(grid, start, goal, lambda node, target, _: manhattan(node, target))),
        ("learned_raw", lambda grid, start, goal: astar_learned(grid, start, goal, raw_lh)),
        ("learned_manhattan_clipped", lambda grid, start, goal: astar_learned(grid, start, goal, clipped_lh)),
    ]

    rows: list[dict[str, float | int | str]] = []
    for scenario in SCENARIOS:
        for trial in range(args.trials_per_density):
            grid, start, goal = sample_reachable_task(
                size=args.grid_size,
                obstacle_density=scenario.obstacle_density,
                rng=rng,
                min_distance=args.min_distance,
            )
            task_id = f"{scenario.label}_{trial:04d}"
            print(f"[{scenario.label}] trial {trial + 1}/{args.trials_per_density}: start={start}, goal={goal}")

            baseline_result = None
            for method_name, planner in methods:
                result = run_method(method_name, grid, start, goal, planner)
                row = {
                    "task_id": task_id,
                    "scenario": scenario.label,
                    "obstacle_density": scenario.obstacle_density,
                    "trial": trial,
                    "grid_size": args.grid_size,
                    "start": str(start),
                    "goal": str(goal),
                    **result,
                }
                if method_name == "astar_manhattan":
                    baseline_result = row
                    row["delta_cost_vs_astar"] = 0
                    row["expansion_reduction_vs_astar_pct"] = 0.0
                elif baseline_result is not None:
                    base_exp = float(baseline_result["expansions"])
                    row["delta_cost_vs_astar"] = int(row["path_cost"]) - int(baseline_result["path_cost"])
                    row["expansion_reduction_vs_astar_pct"] = ((base_exp - float(row["expansions"])) / base_exp * 100.0) if base_exp else float("nan")
                else:
                    row["delta_cost_vs_astar"] = ""
                    row["expansion_reduction_vs_astar_pct"] = ""
                rows.append(row)

    summary_rows = build_summary(rows)
    write_csv(args.trials_out, rows)
    write_csv(args.summary_out, summary_rows)

    print(f"\nSaved trial-level results to {args.trials_out}")
    print(f"Saved summary results to {args.summary_out}")
    print("Use the summary CSV for README/table claims and the trial CSV for auditability.")


if __name__ == "__main__":
    main()
