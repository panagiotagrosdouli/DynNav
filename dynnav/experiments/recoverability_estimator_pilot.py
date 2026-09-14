"""Development pilot for safe-return reliability estimators.

The pilot uses deterministic random small grids and exact future-closure
enumeration as ground truth. Seeds 0--49 are development-only and must not be
reused as final held-out evidence after estimator design decisions are made.
"""

from __future__ import annotations

import csv
import json
import random
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path

from dynnav.planners.grid_map import GridCell, GridMap
from dynnav.recoverability_belief import TopologyHazardBelief, exact_safe_return_probability
from dynnav.recoverability_estimation import (
    most_reliable_return_path,
    two_hazard_disjoint_return_paths,
)


@dataclass(frozen=True)
class EstimatorPilotRecord:
    seed: int
    generation_attempt: int
    obstacle_cells: str
    hazard_cells: str
    exact_return_probability: float
    single_path_probability: float
    two_path_probability: float
    single_path_absolute_error: float
    two_path_absolute_error: float


def _connected(grid: GridMap, start: GridCell, goal: GridCell) -> bool:
    queue: deque[GridCell] = deque([start])
    reached = {start}
    while queue:
        current = queue.popleft()
        if current == goal:
            return True
        for neighbor in grid.neighbors4(current):
            if neighbor not in reached:
                reached.add(neighbor)
                queue.append(neighbor)
    return False


def _scenario(seed: int, *, hazard_count: int = 6) -> tuple[GridMap, TopologyHazardBelief, int]:
    rng = random.Random(seed)
    width = height = 6
    safe = (0, 0)
    start = (5, 5)

    for attempt in range(100):
        obstacles: set[GridCell] = set()
        for x in range(width):
            for y in range(height):
                cell = (x, y)
                if cell in {safe, start}:
                    continue
                if rng.random() < 0.15:
                    obstacles.add(cell)
        grid = GridMap.from_obstacles(width, height, obstacles=obstacles)
        if not _connected(grid, start, safe):
            continue

        candidates = [
            (x, y)
            for x in range(width)
            for y in range(height)
            if (x, y) not in obstacles and (x, y) not in {safe, start}
        ]
        rng.shuffle(candidates)
        selected = candidates[: min(hazard_count, len(candidates))]
        if not selected:
            continue
        hazard = TopologyHazardBelief(
            {cell: rng.choice((0.1, 0.2, 0.3, 0.4, 0.5, 0.6)) for cell in selected}
        )
        return grid, hazard, attempt

    raise RuntimeError(f"could not generate connected pilot scenario for seed {seed}")


def run_estimator_pilot(
    seeds: tuple[int, ...] = tuple(range(50)),
    *,
    hazard_count: int = 6,
) -> list[EstimatorPilotRecord]:
    if not seeds:
        raise ValueError("at least one development seed is required")
    if len(set(seeds)) != len(seeds):
        raise ValueError("development seeds must be unique")
    if not 1 <= hazard_count <= 12:
        raise ValueError("hazard_count must be between 1 and 12")

    records: list[EstimatorPilotRecord] = []
    start = (5, 5)
    safe = {(0, 0)}
    for seed in seeds:
        grid, hazard, attempt = _scenario(seed, hazard_count=hazard_count)
        exact = exact_safe_return_probability(
            grid,
            start,
            safe,
            hazard,
            max_hazard_cells=hazard_count,
        )
        single = most_reliable_return_path(grid, start, safe, hazard).probability
        redundant = two_hazard_disjoint_return_paths(grid, start, safe, hazard).probability
        records.append(
            EstimatorPilotRecord(
                seed=seed,
                generation_attempt=attempt,
                obstacle_cells=json.dumps(sorted(grid.obstacles)),
                hazard_cells=json.dumps(
                    sorted((cell[0], cell[1], probability) for cell, probability in hazard.closure_probability.items())
                ),
                exact_return_probability=exact,
                single_path_probability=single,
                two_path_probability=redundant,
                single_path_absolute_error=abs(exact - single),
                two_path_absolute_error=abs(exact - redundant),
            )
        )
    return records


def summarize_estimator_pilot(records: list[EstimatorPilotRecord]) -> dict[str, float | int]:
    if not records:
        raise ValueError("records cannot be empty")
    tolerance = 1e-12
    single_errors = [row.single_path_absolute_error for row in records]
    two_errors = [row.two_path_absolute_error for row in records]
    return {
        "trials": len(records),
        "exact_mean": sum(row.exact_return_probability for row in records) / len(records),
        "single_path_mae": sum(single_errors) / len(single_errors),
        "two_path_mae": sum(two_errors) / len(two_errors),
        "single_path_max_error": max(single_errors),
        "two_path_max_error": max(two_errors),
        "single_path_overestimate_count": sum(
            row.single_path_probability > row.exact_return_probability + tolerance for row in records
        ),
        "two_path_overestimate_count": sum(
            row.two_path_probability > row.exact_return_probability + tolerance for row in records
        ),
        "two_path_better_count": sum(
            row.two_path_absolute_error + tolerance < row.single_path_absolute_error for row in records
        ),
        "two_path_tied_count": sum(
            abs(row.two_path_absolute_error - row.single_path_absolute_error) <= tolerance
            for row in records
        ),
    }


def write_estimator_pilot_artifacts(
    records: list[EstimatorPilotRecord], output_dir: str | Path
) -> None:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    with (target / "trials.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(records[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(record) for record in records)
    with (target / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summarize_estimator_pilot(records), handle, indent=2, sort_keys=True)
