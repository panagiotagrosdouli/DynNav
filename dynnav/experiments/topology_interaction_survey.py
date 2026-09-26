"""Held-out random-grid survey of two-hazard dependence interaction signs.

The deterministic interaction identity is exact for every two-hazard topology.
This survey asks a different empirical question: do negative, zero and positive
dependence sensitivities occur in a broader family of connected grid maps,
rather than only in hand-constructed parallel and serial examples?
"""

from __future__ import annotations

import itertools
import random
from collections import deque
from dataclasses import dataclass

from dynnav.dependence_connectivity_interaction import (
    connectivity_truth_table,
    dependence_sensitivity,
)
from dynnav.planners.grid_map import GridCell, GridMap


@dataclass(frozen=True)
class TopologyInteractionMapRecord:
    map_index: int
    obstacles: int
    hazard_pairs: int
    negative_interactions: int
    zero_interactions: int
    positive_interactions: int


def _reachable(
    grid: GridMap,
    start: GridCell,
    safe: GridCell,
) -> bool:
    queue: deque[GridCell] = deque([start])
    reached = {start}
    while queue:
        current = queue.popleft()
        if current == safe:
            return True
        for neighbor in grid.neighbors4(current):
            if neighbor not in reached:
                reached.add(neighbor)
                queue.append(neighbor)
    return False


def run_topology_interaction_survey(
    *,
    accepted_maps: int = 40,
    width: int = 6,
    height: int = 5,
    obstacle_probability: float = 0.30,
    seed: int = 20260925,
    max_generation_attempts: int = 10_000,
) -> list[TopologyInteractionMapRecord]:
    """Survey all free-cell hazard pairs in held-out connected random grids."""

    if accepted_maps <= 0:
        raise ValueError("accepted_maps must be positive")
    if width < 3 or height < 3:
        raise ValueError("width and height must be at least 3")
    if not 0.0 <= obstacle_probability < 1.0:
        raise ValueError("obstacle_probability must be in [0, 1)")
    if max_generation_attempts < accepted_maps:
        raise ValueError("max_generation_attempts must be at least accepted_maps")

    rng = random.Random(seed)
    start = (width - 1, height // 2)
    safe = (0, height // 2)
    records: list[TopologyInteractionMapRecord] = []
    attempts = 0

    while len(records) < accepted_maps and attempts < max_generation_attempts:
        attempts += 1
        obstacles: set[GridCell] = set()
        for x in range(width):
            for y in range(height):
                cell = (x, y)
                if cell in (start, safe):
                    continue
                if rng.random() < obstacle_probability:
                    obstacles.add(cell)

        grid = GridMap.from_obstacles(width, height, obstacles=obstacles)
        if not _reachable(grid, start, safe):
            continue

        free = [
            (x, y)
            for x in range(width)
            for y in range(height)
            if grid.passable((x, y)) and (x, y) not in (start, safe)
        ]
        if len(free) < 2:
            continue

        negative = 0
        zero = 0
        positive = 0
        pair_count = 0
        for first, second in itertools.combinations(free, 2):
            table = connectivity_truth_table(
                grid,
                start,
                {safe},
                first,
                second,
            )
            interaction = dependence_sensitivity(table)
            pair_count += 1
            if interaction < 0:
                negative += 1
            elif interaction > 0:
                positive += 1
            else:
                zero += 1

        records.append(
            TopologyInteractionMapRecord(
                map_index=len(records),
                obstacles=len(obstacles),
                hazard_pairs=pair_count,
                negative_interactions=negative,
                zero_interactions=zero,
                positive_interactions=positive,
            )
        )

    if len(records) != accepted_maps:
        raise RuntimeError(
            f"generated only {len(records)} connected maps after {attempts} attempts"
        )
    return records
