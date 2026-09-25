"""Search-level benchmark for exact closure-event history compression."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.planners.commitment_aware_astar import (
    CommitmentAwareAStarConfig,
    CommitmentPlannerMode,
    commitment_aware_astar,
)
from dynnav.planners.compressed_commitment_astar import (
    CompressedCommitmentAStarConfig,
    compressed_commitment_astar,
)
from dynnav.planners.grid_map import GridMap


@dataclass(frozen=True)
class CompressionScalingRecord:
    modules: int
    raw_hazard_count: int
    quotient_event_count: int
    raw_nodes_expanded: int
    compressed_nodes_expanded: int
    raw_planning_ms: float
    compressed_planning_ms: float
    path_length: int
    raw_final_return: float
    compressed_final_return: float


def _diamond_chain(
    modules: int,
) -> tuple[GridMap, tuple[int, int], tuple[int, int], CommitmentHazardModel]:
    if modules <= 0:
        raise ValueError("modules must be positive")
    width = 2 * modules + 1
    free: set[tuple[int, int]] = set()
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
    return (
        grid,
        (0, 1),
        (2 * modules, 1),
        CommitmentHazardModel(tuple(closures)),
    )


def run_history_compression_scaling(
    *,
    module_counts: tuple[int, ...] = (1, 2, 3, 4, 5),
) -> list[CompressionScalingRecord]:
    """Compare raw trigger-state search with the exact event quotient."""

    records: list[CompressionScalingRecord] = []
    for modules in module_counts:
        grid, start, goal, model = _diamond_chain(modules)
        raw = commitment_aware_astar(
            grid,
            start,
            goal,
            safe_cells={start},
            hazard_model=model,
            mode=CommitmentPlannerMode.SHORTEST,
            config=CommitmentAwareAStarConfig(recoverability_weight=0.0),
        )
        compressed = compressed_commitment_astar(
            grid,
            start,
            goal,
            safe_cells={start},
            hazard_model=model,
            config=CompressedCommitmentAStarConfig(recoverability_weight=0.0),
        )
        if not raw.success or not compressed.success:
            raise RuntimeError("compression benchmark planner failed")
        if raw.geometric_length != compressed.geometric_length:
            raise RuntimeError("quotient changed shortest path length")
        if abs(raw.final_return_probability - compressed.final_return_probability) > 1e-12:
            raise RuntimeError("quotient changed final return probability")

        records.append(
            CompressionScalingRecord(
                modules=modules,
                raw_hazard_count=2 * modules,
                quotient_event_count=modules,
                raw_nodes_expanded=raw.nodes_expanded,
                compressed_nodes_expanded=compressed.nodes_expanded,
                raw_planning_ms=raw.planning_time_ms,
                compressed_planning_ms=compressed.planning_time_ms,
                path_length=raw.geometric_length,
                raw_final_return=raw.final_return_probability,
                compressed_final_return=compressed.final_return_probability,
            )
        )
    return records


def records_as_dicts(
    records: list[CompressionScalingRecord],
) -> list[dict[str, object]]:
    return [asdict(record) for record in records]
