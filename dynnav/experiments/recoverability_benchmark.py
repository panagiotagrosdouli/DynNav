"""Controlled multi-seed benchmark for recoverability-aware planning."""

from __future__ import annotations

import csv
import random
from dataclasses import asdict, dataclass
from pathlib import Path

from dynnav.planners.grid_map import GridCell, GridMap
from dynnav.planners.recoverability_astar import PlannerMode, RecoverabilityAStarConfig, recoverability_astar
from dynnav.recoverability import return_failure_probability


@dataclass(frozen=True)
class BenchmarkRecord:
    seed: int
    mode: str
    success: bool
    irreversible_failure: bool
    geometric_length: int
    path_length_overhead: float
    cumulative_risk: float
    cumulative_irreversibility: float
    minimum_escape_options: int
    nodes_expanded: int
    planning_time_ms: float


def dynamic_bottleneck_scenario(seed: int) -> tuple[GridMap, GridCell, GridCell, GridCell]:
    """Create two corridors where the short corridor can be invalidated."""

    rng = random.Random(seed)
    width, height = 15, 9
    obstacles: set[GridCell] = set()

    # Central wall with two passages: a short narrow passage and a longer open one.
    for y in range(height):
        if y not in {2, 6}:
            obstacles.add((7, y))

    # Make the upper route structurally fragile by narrowing its approaches.
    obstacles.update({(6, 1), (6, 3), (8, 1), (8, 3)})
    risk = {(x, 2): 0.15 + 0.1 * rng.random() for x in range(5, 10)}
    grid = GridMap.from_obstacles(width, height, obstacles, risk=risk)
    return grid, (1, 2), (13, 2), (7, 2)


def evaluate_dynamic_invalidation(
    grid: GridMap,
    start: GridCell,
    goal: GridCell,
    invalidated_cell: GridCell,
    mode: PlannerMode,
    config: RecoverabilityAStarConfig,
) -> tuple[bool, bool, object]:
    """Plan, invalidate a route cell, and evaluate mission and recovery feasibility."""

    initial = recoverability_astar(grid, start, goal, safe_cells={start}, mode=mode, config=config)
    if not initial.success:
        return False, True, initial

    # Invalidate only when the selected path commits to the fragile passage.
    if invalidated_cell not in initial.path:
        return True, False, initial

    index = initial.path.index(invalidated_cell)
    current = initial.path[max(0, index - 1)]
    updated = GridMap.from_obstacles(
        grid.width,
        grid.height,
        obstacles=set(grid.obstacles) | {invalidated_cell},
        risk=grid.risk,
        uncertainty=grid.uncertainty,
    )
    continuation = recoverability_astar(
        updated,
        current,
        goal,
        safe_cells={start},
        mode=mode,
        config=config,
    )
    mission_success = continuation.success
    recovery_infeasible = return_failure_probability(updated, current, {start}) >= 1.0
    irreversible_failure = (not mission_success) and recovery_infeasible
    return mission_success, irreversible_failure, initial


def run_benchmark(
    seeds: range | list[int],
    output_csv: str | Path | None = None,
    config: RecoverabilityAStarConfig | None = None,
) -> list[BenchmarkRecord]:
    config = config or RecoverabilityAStarConfig()
    records: list[BenchmarkRecord] = []

    for seed in seeds:
        grid, start, goal, invalidated_cell = dynamic_bottleneck_scenario(seed)
        shortest = recoverability_astar(grid, start, goal, mode=PlannerMode.SHORTEST, config=config)
        baseline_length = max(1, shortest.geometric_length)

        for mode in PlannerMode:
            success, irreversible_failure, initial = evaluate_dynamic_invalidation(
                grid, start, goal, invalidated_cell, mode, config
            )
            records.append(
                BenchmarkRecord(
                    seed=seed,
                    mode=mode.value,
                    success=success,
                    irreversible_failure=irreversible_failure,
                    geometric_length=initial.geometric_length,
                    path_length_overhead=(initial.geometric_length - baseline_length) / baseline_length,
                    cumulative_risk=initial.cumulative_risk,
                    cumulative_irreversibility=initial.cumulative_irreversibility,
                    minimum_escape_options=initial.minimum_escape_options,
                    nodes_expanded=initial.nodes_expanded,
                    planning_time_ms=initial.planning_time_ms,
                )
            )

    if output_csv is not None:
        path = Path(output_csv)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(asdict(records[0]).keys()))
            writer.writeheader()
            writer.writerows(asdict(record) for record in records)

    return records
