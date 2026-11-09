"""C01 offline path planning on an independently recorded ROS occupancy map.

The real occupancy grid supplies geometry; generated map-valid start/goal queries
are evaluation tasks, not trajectories actually driven by the recorded robot.
This experiment is NOT closed-loop or action-triggered efficacy evidence.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import sys
import time
from collections import defaultdict, deque
from pathlib import Path
from statistics import mean

import numpy as np
import yaml

from dynnav.mapping.ros_map import load_ros_map

C01_EXPERIMENTS = Path(__file__).resolve().parent
if str(C01_EXPERIMENTS) not in sys.path:
    sys.path.insert(0, str(C01_EXPERIMENTS))

from astar_learned_heuristic import (  # noqa: E402
    LearnedHeuristicWrapper,
    astar_classic,
    astar_learned,
    astar_search,
)

Node = tuple[int, int]
NEIGHBORS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def map_to_array(ros_map: object) -> np.ndarray:
    """Convert DynNav's ROS-map grid into C01's [row, column] binary convention."""
    source = ros_map.grid
    grid = np.zeros((source.height, source.width), dtype=np.uint8)
    for x, y in source.obstacles:
        grid[y, x] = 1
    return grid


def free_components(grid: np.ndarray) -> list[list[Node]]:
    """Four-connected free-space components, deterministically ordered."""
    height, width = grid.shape
    seen: set[Node] = set()
    components: list[list[Node]] = []
    for y in range(height):
        for x in range(width):
            start = (x, y)
            if grid[y, x] or start in seen:
                continue
            component = [start]
            seen.add(start)
            queue = deque([start])
            while queue:
                cx, cy = queue.popleft()
                for dx, dy in NEIGHBORS:
                    nx, ny = cx + dx, cy + dy
                    other = (nx, ny)
                    if 0 <= nx < width and 0 <= ny < height and not grid[ny, nx] and other not in seen:
                        seen.add(other)
                        component.append(other)
                        queue.append(other)
            components.append(component)
    return sorted(components, key=lambda cells: (-len(cells), min(cells)))


def sample_tasks(
    components: list[list[Node]], count: int, min_distance: int, seed: int
) -> list[tuple[Node, Node]]:
    """Sample pairs from the same free connected component with exact reachability."""
    if count < 1 or min_distance < 1:
        raise ValueError("count and min_distance must be positive")
    candidates = [cells for cells in components if len(cells) > 1]
    if not candidates:
        raise ValueError("No connected free-space component contains two cells")
    rng = random.Random(seed)
    weights = [len(cells) for cells in candidates]
    tasks: list[tuple[Node, Node]] = []
    used: set[tuple[Node, Node]] = set()
    for _ in range(count):
        selected: tuple[Node, Node] | None = None
        for _attempt in range(5000):
            cells = rng.choices(candidates, weights=weights, k=1)[0]
            start, goal = rng.sample(cells, 2)
            distance = abs(start[0] - goal[0]) + abs(start[1] - goal[1])
            if distance >= min_distance and (start, goal) not in used:
                selected = (start, goal)
                break
        if selected is None:
            raise ValueError(f"Insufficient unique connected tasks with Manhattan distance >= {min_distance}")
        used.add(selected)
        tasks.append(selected)
    return tasks


def validate_path(grid: np.ndarray, path: list[Node] | None, start: Node, goal: Node) -> bool:
    if not path or path[0] != start or path[-1] != goal:
        return False
    for x, y in path:
        if not (0 <= x < grid.shape[1] and 0 <= y < grid.shape[0]) or grid[y, x]:
            return False
    return all(abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1 for a, b in zip(path, path[1:]))


def run_query(
    grid: np.ndarray, start: Node, goal: Node, methods: dict, resolution: float, seed: int
) -> list[dict]:
    rows = []
    reference_cost = None
    for method, search in methods.items():
        begin = time.perf_counter()
        path, expansions = search(grid, start, goal)
        elapsed_ms = (time.perf_counter() - begin) * 1000
        if not validate_path(grid, path, start, goal):
            raise AssertionError(f"Invalid or missing path in {method}: start={start}, goal={goal}")
        cost = len(path) - 1
        if method == "astar_manhattan":
            reference_cost = cost
        rows.append(
            {
                "task_seed": seed,
                "start_x": start[0], "start_y": start[1],
                "goal_x": goal[0], "goal_y": goal[1],
                "method": method,
                "path_cost_cells": cost,
                "path_length_m": cost * resolution,
                "expansions": expansions,
                "runtime_ms_warm": elapsed_ms,
                "path_valid": True,
            }
        )
    if reference_cost is None:
        raise AssertionError("Manhattan baseline is mandatory")
    for row in rows:
        row["cost_gap_vs_astar_cells"] = row["path_cost_cells"] - reference_cost
        if row["method"] in {"dijkstra_h0", "learned_manhattan_clipped"}:
            if row["cost_gap_vs_astar_cells"] != 0:
                raise AssertionError(f"Expected optimal method returned suboptimal cost: {row}")
    return rows


def evaluate(map_yaml: Path, out: Path, model: Path | None, n_tasks: int, seed: int, min_distance: int) -> dict:
    map_yaml = map_yaml.resolve()
    metadata = yaml.safe_load(map_yaml.read_text(encoding="utf-8"))
    image_path = (map_yaml.parent / metadata["image"]).resolve()
    ros_map = load_ros_map(map_yaml, unknown_as_obstacle=True)
    grid = map_to_array(ros_map)
    components = free_components(grid)
    tasks = sample_tasks(components, n_tasks, min_distance, seed)

    methods = {
        "astar_manhattan": astar_classic,
        "dijkstra_h0": lambda g, s, t: astar_search(g, s, t, lambda *_: 0.0),
    }
    model_digest = None
    if model is not None:
        if not model.is_file():
            raise FileNotFoundError(f"Neural checkpoint unavailable: {model}")
        model_digest = hashlib.sha256(model.read_bytes()).hexdigest()
        load_begin = time.perf_counter()
        raw = LearnedHeuristicWrapper(model_path=model, mode="raw", allow_missing_model=False)
        clipped = LearnedHeuristicWrapper(model_path=model, mode="manhattan_clipped", allow_missing_model=False)
        model_load_ms = (time.perf_counter() - load_begin) * 1000
        if raw.model is None or clipped.model is None:
            raise AssertionError("Neural models did not load; never silently substitute Manhattan")
        methods["learned_raw"] = lambda g, s, t: astar_learned(g, s, t, raw)
        methods["learned_manhattan_clipped"] = lambda g, s, t: astar_learned(g, s, t, clipped)
    else:
        model_load_ms = None

    rows = []
    for index, (start, goal) in enumerate(tasks):
        rows.extend(run_query(grid, start, goal, methods, ros_map.resolution, seed + index))

    out.mkdir(parents=True, exist_ok=True)
    with (out / "trials.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    averages = {
        name: {
            "n": len(method_rows),
            "mean_expansions": mean(r["expansions"] for r in method_rows),
            "mean_runtime_ms_warm": mean(r["runtime_ms_warm"] for r in method_rows),
            "mean_path_cost_cells": mean(r["path_cost_cells"] for r in method_rows),
            "suboptimal_task_count": sum(int(r["cost_gap_vs_astar_cells"] > 0) for r in method_rows),
        }
        for name, method_rows in (
            (name, [r for r in rows if r["method"] == name]) for name in methods
        )
    }
    report = {
        "evidence_type": "real_map_offline_generated_queries",
        "not_evidence_of": [
            "executed robot route",
            "closed-loop success",
            "robot action-triggered hazard efficacy",
            "real-world neural training or domain generalization",
        ],
        "dataset": "ROS occupancy map supplied by operator; attribute based on actual map source",
        "map_yaml_sha256": hashlib.sha256(map_yaml.read_bytes()).hexdigest(),
        "map_image_sha256": hashlib.sha256(image_path.read_bytes()).hexdigest(),
        "model_sha256": model_digest,
        "neural_model_loaded": model is not None,
        "model_initialization_ms": model_load_ms,
        "map_resolution_m": ros_map.resolution,
        "map_size_cells": list(grid.shape[::-1]),
        "unknown_policy": "blocked",
        "number_free_components": len(components),
        "number_tasks": len(tasks),
        "random_seed": seed,
        "min_manhattan_distance": min_distance,
        "methods": averages,
    }
    (out / "summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map_yaml", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=None, help="C01 checkpoint; omit for map-baseline-only validation")
    parser.add_argument("--n-tasks", type=int, default=8)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--min-distance", type=int, default=8)
    args = parser.parse_args()
    report = evaluate(args.map_yaml, args.output_dir, args.model, args.n_tasks, args.seed, args.min_distance)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
