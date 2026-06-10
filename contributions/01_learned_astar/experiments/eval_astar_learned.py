"""Evaluate Contribution 01: Learned A* Heuristics.

Run from the repository root:

    python contributions/01_learned_astar/experiments/eval_astar_learned.py \
        --trials 100 \
        --out contributions/01_learned_astar/results/astar_eval_results.csv
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
import time
from pathlib import Path
from statistics import mean, stdev
from typing import Any, Iterable

MODULE_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = MODULE_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from astar_learned_heuristic import (  # noqa: E402
    LearnedHeuristicWrapper,
    astar_classic,
    astar_learned,
    make_grid,
)

DEFAULT_OUT = MODULE_ROOT / "results" / "astar_eval_results.csv"
DEFAULT_MODEL = MODULE_ROOT / "models" / "heuristic_net_rich.pt"


def _grid_shape(grid: Any) -> tuple[int, int]:
    height = len(grid)
    width = len(grid[0]) if height else 0
    return height, width


def _cell_is_free(grid: Any, cell: tuple[int, int]) -> bool:
    x, y = cell
    try:
        return int(grid[y, x]) == 0
    except Exception:
        return int(grid[y][x]) == 0


def _free_cells(grid: Any) -> list[tuple[int, int]]:
    height, width = _grid_shape(grid)
    return [(x, y) for y in range(height) for x in range(width) if _cell_is_free(grid, (x, y))]


def _sample_start_goal(
    grid: Any,
    rng: random.Random,
    min_manhattan_distance: int = 20,
) -> tuple[tuple[int, int], tuple[int, int]]:
    free = _free_cells(grid)
    if len(free) < 2:
        raise ValueError("Grid does not contain enough free cells for planning.")

    for _ in range(2_000):
        start, goal = rng.sample(free, 2)
        dist = abs(start[0] - goal[0]) + abs(start[1] - goal[1])
        if dist >= min_manhattan_distance:
            return start, goal
    return rng.sample(free, 2)


def _safe_len(path: Iterable[Any] | None) -> int:
    return len(path) if path is not None else 0


def run_single(seed: int, model_path: Path, min_goal_distance: int) -> dict[str, float | int | str]:
    rng = random.Random(seed)
    grid = make_grid()
    start, goal = _sample_start_goal(grid, rng, min_goal_distance)

    t0 = time.perf_counter()
    path_c, exp_c = astar_classic(grid, start, goal)
    classic_ms = (time.perf_counter() - t0) * 1_000.0

    lh = LearnedHeuristicWrapper(model_path=str(model_path))
    t1 = time.perf_counter()
    path_l, exp_l = astar_learned(grid, start, goal, lh)
    learned_ms = (time.perf_counter() - t1) * 1_000.0

    classic_path_len = _safe_len(path_c)
    learned_path_len = _safe_len(path_l)

    return {
        "seed": seed,
        "start": str(start),
        "goal": str(goal),
        "classic_success": int(classic_path_len > 0),
        "learned_success": int(learned_path_len > 0),
        "classic_path_len": classic_path_len,
        "classic_expansions": exp_c,
        "classic_runtime_ms": classic_ms,
        "learned_path_len": learned_path_len,
        "learned_expansions": exp_l,
        "learned_runtime_ms": learned_ms,
        "expansion_ratio": exp_l / exp_c if exp_c else float("nan"),
        "runtime_ratio": learned_ms / classic_ms if classic_ms else float("nan"),
        "delta_path": learned_path_len - classic_path_len,
    }


def _summarise(rows: list[dict[str, float | int | str]]) -> None:
    def numeric(name: str) -> list[float]:
        return [float(row[name]) for row in rows]

    def mean_std(name: str) -> str:
        values = numeric(name)
        if len(values) == 1:
            return f"{values[0]:.4f}"
        return f"{mean(values):.4f} ± {stdev(values):.4f}"

    print("\n=== Contribution 01 summary ===")
    print(f"Trials: {len(rows)}")
    print(f"Classic success rate: {mean(numeric('classic_success')):.3f}")
    print(f"Learned success rate: {mean(numeric('learned_success')):.3f}")
    print(f"Classic path length: {mean_std('classic_path_len')}")
    print(f"Learned path length: {mean_std('learned_path_len')}")
    print(f"Classic expansions: {mean_std('classic_expansions')}")
    print(f"Learned expansions: {mean_std('learned_expansions')}")
    print(f"Expansion ratio: {mean_std('expansion_ratio')}")
    print(f"Classic runtime ms: {mean_std('classic_runtime_ms')}")
    print(f"Learned runtime ms: {mean_std('learned_runtime_ms')}")
    print(f"Runtime ratio: {mean_std('runtime_ratio')}")
    print(f"Delta path length: {mean_std('delta_path')}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate learned A* against classical A*.")
    parser.add_argument("--trials", type=int, default=100)
    parser.add_argument("--seed-offset", type=int, default=0)
    parser.add_argument("--min-goal-distance", type=int, default=20)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    rows = []
    for i in range(args.trials):
        seed = args.seed_offset + i
        print(f"Running trial {i + 1}/{args.trials} with seed {seed}...")
        rows.append(run_single(seed, args.model, args.min_goal_distance))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved per-trial results to {args.out}")
    _summarise(rows)


if __name__ == "__main__":
    main()
