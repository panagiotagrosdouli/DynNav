"""Procedural multi-trigger benchmark for decision-dependent return topology."""
from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from dynnav.commitment_hazard import (
    CommitmentClosure,
    CommitmentHazardModel,
    exact_history_conditioned_return_probability,
)
from dynnav.planners.commitment_aware_astar import (
    CommitmentAwareAStarConfig,
    CommitmentPlannerMode,
    commitment_aware_astar,
)
from dynnav.planners.commitment_cut_astar import (
    CommitmentCutAStarConfig,
    commitment_cut_astar,
)
from dynnav.planners.grid_map import GridCell, GridMap


@dataclass(frozen=True)
class MultiCommitmentRecord:
    module_count: int
    closure_probability: float
    recoverability_weight: float
    planner: str
    success: bool
    geometric_length: int
    activated_closure_count: int
    final_exact_return_probability: float
    planning_time_ms: float
    nodes_expanded: int


def multi_commitment_world(
    module_count: int,
    closure_probability: float,
) -> tuple[GridMap, GridCell, GridCell, set[GridCell], CommitmentHazardModel]:
    """Build repeated direct-trigger / safe-detour modules on a corridor.

    Each module contributes one critical bridge followed by a risky direct edge.
    Taking the direct edge activates a future closure probability on that bridge.
    A two-step-longer local detour reaches the same downstream cell without
    activating the event. The detour lies ahead of the bridge, so it does not
    create an alternate route around an activated bridge.
    """
    if module_count < 1:
        raise ValueError("module_count must be positive")
    if not 0.0 <= closure_probability <= 1.0:
        raise ValueError("closure_probability must be in [0, 1]")

    width = 4 * module_count + 1
    height = 3
    main_y = 1
    free: set[GridCell] = {(x, main_y) for x in range(width)}
    closures: list[CommitmentClosure] = []

    for index in range(module_count):
        base = 4 * index
        bridge = (base + 1, main_y)
        trigger_source = (base + 2, main_y)
        trigger_target = (base + 3, main_y)
        # Local upper detour: source -> up -> across -> down -> target.
        free.update({(base + 2, 0), (base + 3, 0)})
        closures.append(
            CommitmentClosure(
                trigger=(trigger_source, trigger_target),
                closure_cell=bridge,
                closure_probability=closure_probability,
            )
        )

    obstacles = {
        (x, y)
        for x in range(width)
        for y in range(height)
        if (x, y) not in free
    }
    grid = GridMap.from_obstacles(width, height, obstacles=obstacles)
    start = (0, main_y)
    goal = (width - 1, main_y)
    return grid, start, goal, {start}, CommitmentHazardModel(tuple(closures))


def _exact_final_probability(
    grid: GridMap,
    path: tuple[GridCell, ...] | list[GridCell],
    safe: set[GridCell],
    model: CommitmentHazardModel,
) -> float:
    return exact_history_conditioned_return_probability(
        grid,
        path,
        safe,
        model,
        max_hazard_cells=max(16, len(model.closures)),
    )


def run_multi_commitment_benchmark(
    *,
    module_counts: tuple[int, ...] = (1, 2, 3, 4, 5),
    closure_probabilities: tuple[float, ...] = (0.2, 0.5, 0.8),
    recoverability_weights: tuple[float, ...] = (1.0, 4.0, 8.0),
) -> list[MultiCommitmentRecord]:
    records: list[MultiCommitmentRecord] = []
    for modules in module_counts:
        for probability in closure_probabilities:
            grid, start, goal, safe, model = multi_commitment_world(modules, probability)
            shortest = commitment_aware_astar(
                grid,
                start,
                goal,
                safe_cells=safe,
                hazard_model=model,
                mode=CommitmentPlannerMode.SHORTEST,
            )
            records.append(
                MultiCommitmentRecord(
                    modules,
                    probability,
                    0.0,
                    "shortest",
                    shortest.success,
                    shortest.geometric_length,
                    shortest.activated_closure_count,
                    _exact_final_probability(grid, shortest.path, safe, model),
                    shortest.planning_time_ms,
                    shortest.nodes_expanded,
                )
            )

            for weight in recoverability_weights:
                exact = commitment_aware_astar(
                    grid,
                    start,
                    goal,
                    safe_cells=safe,
                    hazard_model=model,
                    mode=CommitmentPlannerMode.HISTORY_AWARE,
                    config=CommitmentAwareAStarConfig(
                        recoverability_weight=weight,
                        max_hazard_cells=max(16, modules),
                    ),
                )
                cut = commitment_cut_astar(
                    grid,
                    start,
                    goal,
                    safe_cells=safe,
                    hazard_model=model,
                    config=CommitmentCutAStarConfig(recoverability_weight=weight),
                )
                for name, result in (("history_exact", exact), ("history_cut", cut)):
                    records.append(
                        MultiCommitmentRecord(
                            modules,
                            probability,
                            weight,
                            name,
                            result.success,
                            result.geometric_length,
                            result.activated_closure_count,
                            _exact_final_probability(grid, result.path, safe, model),
                            result.planning_time_ms,
                            result.nodes_expanded,
                        )
                    )
    return records


def summarize_multi_commitment(records: list[MultiCommitmentRecord]) -> dict[str, object]:
    if not records:
        raise ValueError("records cannot be empty")
    grouped: dict[str, list[MultiCommitmentRecord]] = {}
    for row in records:
        grouped.setdefault(row.planner, []).append(row)
    summary: dict[str, object] = {}
    for planner, rows in sorted(grouped.items()):
        summary[planner] = {
            "trials": len(rows),
            "mean_path_length": sum(row.geometric_length for row in rows) / len(rows),
            "mean_activated_closures": sum(row.activated_closure_count for row in rows) / len(rows),
            "mean_final_exact_return_probability": sum(
                row.final_exact_return_probability for row in rows
            ) / len(rows),
            "mean_planning_time_ms": sum(row.planning_time_ms for row in rows) / len(rows),
        }
    paired = [
        (a, b)
        for a in records
        if a.planner == "history_exact"
        for b in records
        if b.planner == "history_cut"
        and (a.module_count, a.closure_probability, a.recoverability_weight)
        == (b.module_count, b.closure_probability, b.recoverability_weight)
    ]
    summary["exact_cut_route_agreement_rate"] = (
        sum(
            a.geometric_length == b.geometric_length
            and a.activated_closure_count == b.activated_closure_count
            for a, b in paired
        )
        / len(paired)
        if paired else 0.0
    )
    return summary


def write_multi_commitment_artifacts(
    records: list[MultiCommitmentRecord], output_dir: str | Path
) -> None:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    with (target / "trials.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(records[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(row) for row in records)
    with (target / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summarize_multi_commitment(records), handle, indent=2, sort_keys=True)
