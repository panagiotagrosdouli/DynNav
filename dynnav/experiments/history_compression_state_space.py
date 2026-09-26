"""Exploratory full reachable-state benchmark for G5 history compression.

The frozen V1 search benchmark stops when A* reaches the goal, so it may expose
only a small fraction of the raw augmented state space. This module separately
enumerates every reachable augmented state under the same monotone trigger
semantics and records both state-count and traversal-cost proxies.

The quotient remains exact; timing is descriptive and machine-dependent.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import time

from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.history_compression import build_hazard_event_quotient
from dynnav.planners.grid_map import GridCell, GridMap

RawState = tuple[GridCell, frozenset[int]]
CompressedState = tuple[GridCell, frozenset[int]]


@dataclass(frozen=True)
class ReachableStateSpaceRecord:
    modules: int
    raw_hazard_count: int
    quotient_event_count: int
    raw_reachable_states: int
    compressed_reachable_states: int
    reduction_fraction: float
    compression_ratio: float
    raw_peak_frontier: int
    compressed_peak_frontier: int
    raw_enumeration_ms: float
    compressed_enumeration_ms: float


def diamond_chain_problem(
    modules: int,
) -> tuple[GridMap, GridCell, CommitmentHazardModel]:
    """Return the same duplicated-trigger diamond family used by G5."""

    if modules <= 0:
        raise ValueError("modules must be positive")
    width = 2 * modules + 1
    free: set[GridCell] = set()
    for x in range(width):
        if x % 2 == 0:
            free.update({(x, 0), (x, 1), (x, 2)})
        else:
            free.update({(x, 0), (x, 2)})
    obstacles = {
        (x, y)
        for x in range(width)
        for y in range(3)
        if (x, y) not in free
    }
    grid = GridMap.from_obstacles(width, 3, obstacles=obstacles)
    closures: list[CommitmentClosure] = []
    for module in range(modules):
        left = 2 * module
        right = left + 1
        closure_cell = (left, 1)
        closures.extend(
            (
                CommitmentClosure(
                    trigger=((left, 0), (right, 0)),
                    closure_cell=closure_cell,
                    closure_probability=0.2,
                ),
                CommitmentClosure(
                    trigger=((left, 2), (right, 2)),
                    closure_cell=closure_cell,
                    closure_probability=0.2,
                ),
            )
        )
    return grid, (0, 1), CommitmentHazardModel(tuple(closures))


def _raw_next_active(
    model: CommitmentHazardModel,
    current: GridCell,
    neighbor: GridCell,
    active: frozenset[int],
) -> frozenset[int]:
    additions = frozenset(
        index
        for index, closure in enumerate(model.closures)
        if closure.trigger == (current, neighbor)
    )
    return active | additions


def _enumerate_raw_reachable_state_stats(
    grid: GridMap,
    start: GridCell,
    model: CommitmentHazardModel,
) -> tuple[frozenset[RawState], int]:
    model.validate(grid)
    initial: RawState = (start, frozenset())
    queue: deque[RawState] = deque([initial])
    reached: set[RawState] = {initial}
    peak_frontier = len(queue)
    while queue:
        cell, active = queue.popleft()
        for neighbor in grid.neighbors4(cell):
            state = (
                neighbor,
                _raw_next_active(model, cell, neighbor, active),
            )
            if state not in reached:
                reached.add(state)
                queue.append(state)
        peak_frontier = max(peak_frontier, len(queue))
    return frozenset(reached), peak_frontier


def enumerate_raw_reachable_states(
    grid: GridMap,
    start: GridCell,
    model: CommitmentHazardModel,
) -> frozenset[RawState]:
    """Enumerate the complete finite raw position x trigger-history graph."""

    reached, _ = _enumerate_raw_reachable_state_stats(grid, start, model)
    return reached


def _enumerate_compressed_reachable_state_stats(
    grid: GridMap,
    start: GridCell,
    model: CommitmentHazardModel,
) -> tuple[frozenset[CompressedState], int]:
    model.validate(grid)
    quotient = build_hazard_event_quotient(model)
    initial: CompressedState = (start, frozenset())
    queue: deque[CompressedState] = deque([initial])
    reached: set[CompressedState] = {initial}
    peak_frontier = len(queue)

    while queue:
        cell, active_events = queue.popleft()
        for neighbor in grid.neighbors4(cell):
            additions = frozenset(
                quotient.event_by_hazard_index[index]
                for index, closure in enumerate(model.closures)
                if closure.trigger == (cell, neighbor)
            )
            state = (neighbor, active_events | additions)
            if state not in reached:
                reached.add(state)
                queue.append(state)
        peak_frontier = max(peak_frontier, len(queue))
    return frozenset(reached), peak_frontier


def enumerate_compressed_reachable_states(
    grid: GridMap,
    start: GridCell,
    model: CommitmentHazardModel,
) -> frozenset[CompressedState]:
    """Enumerate the exact quotient position x closure-event history graph."""

    reached, _ = _enumerate_compressed_reachable_state_stats(
        grid,
        start,
        model,
    )
    return reached


def run_reachable_state_space_scaling(
    *,
    module_counts: tuple[int, ...] = (1, 2, 3, 4, 5, 6, 7, 8),
) -> list[ReachableStateSpaceRecord]:
    """Measure exact reachable-state reduction independently of goal stopping."""

    records: list[ReachableStateSpaceRecord] = []
    for modules in module_counts:
        grid, start, model = diamond_chain_problem(modules)

        raw_start = time.perf_counter()
        raw, raw_peak = _enumerate_raw_reachable_state_stats(
            grid,
            start,
            model,
        )
        raw_ms = (time.perf_counter() - raw_start) * 1000.0

        compressed_start = time.perf_counter()
        compressed, compressed_peak = _enumerate_compressed_reachable_state_stats(
            grid,
            start,
            model,
        )
        compressed_ms = (time.perf_counter() - compressed_start) * 1000.0

        raw_count = len(raw)
        compressed_count = len(compressed)
        if compressed_count > raw_count:
            raise RuntimeError("event quotient increased the reachable state count")
        records.append(
            ReachableStateSpaceRecord(
                modules=modules,
                raw_hazard_count=len(model.closures),
                quotient_event_count=modules,
                raw_reachable_states=raw_count,
                compressed_reachable_states=compressed_count,
                reduction_fraction=(
                    (raw_count - compressed_count) / raw_count
                    if raw_count
                    else 0.0
                ),
                compression_ratio=(
                    raw_count / compressed_count
                    if compressed_count
                    else float("inf")
                ),
                raw_peak_frontier=raw_peak,
                compressed_peak_frontier=compressed_peak,
                raw_enumeration_ms=raw_ms,
                compressed_enumeration_ms=compressed_ms,
            )
        )
    return records
