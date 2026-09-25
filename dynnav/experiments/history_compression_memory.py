"""Peak-memory and full-state scaling for G5 exact history compression."""

from __future__ import annotations

import gc
import tracemalloc
from dataclasses import dataclass
from typing import Callable, TypeVar

from dynnav.experiments.history_compression_state_space import (
    diamond_chain_problem,
    enumerate_compressed_reachable_states,
    enumerate_raw_reachable_states,
)
from dynnav.planners.commitment_aware_astar import (
    CommitmentAwareAStarConfig,
    CommitmentPlannerMode,
    commitment_aware_astar,
)
from dynnav.planners.compressed_commitment_astar import (
    CompressedCommitmentAStarConfig,
    compressed_commitment_astar,
)

T = TypeVar("T")


@dataclass(frozen=True)
class CompressionMemoryRecord:
    modules: int
    raw_hazard_count: int
    quotient_event_count: int
    raw_reachable_states: int
    compressed_reachable_states: int
    reachable_state_ratio: float
    raw_enumeration_peak_bytes: int
    compressed_enumeration_peak_bytes: int
    raw_planner_peak_bytes: int
    compressed_planner_peak_bytes: int
    raw_nodes_expanded: int
    compressed_nodes_expanded: int
    raw_objective: float
    compressed_objective: float
    raw_final_return: float
    compressed_final_return: float


def _peak_memory(call: Callable[[], T]) -> tuple[T, int]:
    gc.collect()
    tracemalloc.start()
    try:
        result = call()
        _current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return result, int(peak)


def run_history_compression_memory_scaling(
    *,
    module_counts: tuple[int, ...] = (2, 3, 4, 5, 6),
    recoverability_weight: float = 2.0,
) -> list[CompressionMemoryRecord]:
    """Compare raw and quotient memory while preserving planner objective."""

    if any(value <= 0 for value in module_counts):
        raise ValueError("module counts must be positive")
    if recoverability_weight < 0.0:
        raise ValueError("recoverability_weight must be non-negative")

    records: list[CompressionMemoryRecord] = []
    for modules in module_counts:
        grid, start, model = diamond_chain_problem(modules)
        goal = (2 * modules, 1)

        raw_states, raw_state_peak = _peak_memory(
            lambda: enumerate_raw_reachable_states(grid, start, model)
        )
        compressed_states, compressed_state_peak = _peak_memory(
            lambda: enumerate_compressed_reachable_states(
                grid,
                start,
                model,
            )
        )

        raw, raw_planner_peak = _peak_memory(
            lambda: commitment_aware_astar(
                grid,
                start,
                goal,
                safe_cells={start},
                hazard_model=model,
                mode=CommitmentPlannerMode.HISTORY_AWARE,
                config=CommitmentAwareAStarConfig(
                    recoverability_weight=recoverability_weight,
                    heuristic_weight=1.0,
                ),
            )
        )
        compressed, compressed_planner_peak = _peak_memory(
            lambda: compressed_commitment_astar(
                grid,
                start,
                goal,
                safe_cells={start},
                hazard_model=model,
                config=CompressedCommitmentAStarConfig(
                    recoverability_weight=recoverability_weight,
                    heuristic_weight=1.0,
                ),
            )
        )

        if not raw.success or not compressed.success:
            raise RuntimeError("G5 memory benchmark planner failed")
        if abs(raw.cost - compressed.cost) > 1.0e-12:
            raise RuntimeError("quotient changed optimal planning objective")
        if (
            abs(
                raw.final_return_probability
                - compressed.final_return_probability
            )
            > 1.0e-12
        ):
            raise RuntimeError("quotient changed final return probability")
        if len(compressed_states) > len(raw_states):
            raise RuntimeError("quotient increased reachable state count")

        records.append(
            CompressionMemoryRecord(
                modules=modules,
                raw_hazard_count=len(model.closures),
                quotient_event_count=modules,
                raw_reachable_states=len(raw_states),
                compressed_reachable_states=len(compressed_states),
                reachable_state_ratio=(
                    len(raw_states) / len(compressed_states)
                    if compressed_states
                    else float("inf")
                ),
                raw_enumeration_peak_bytes=raw_state_peak,
                compressed_enumeration_peak_bytes=compressed_state_peak,
                raw_planner_peak_bytes=raw_planner_peak,
                compressed_planner_peak_bytes=compressed_planner_peak,
                raw_nodes_expanded=raw.nodes_expanded,
                compressed_nodes_expanded=compressed.nodes_expanded,
                raw_objective=raw.cost,
                compressed_objective=compressed.cost,
                raw_final_return=raw.final_return_probability,
                compressed_final_return=compressed.final_return_probability,
            )
        )
    return records
