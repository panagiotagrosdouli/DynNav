"""Monte Carlo execution benchmark for action-triggered future closures."""
from __future__ import annotations

import csv
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path

from dynnav.commitment_hazard import CommitmentHazardModel
from dynnav.experiments.multi_commitment_benchmark import multi_commitment_world
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
from dynnav.recoverability import return_failure_probability


@dataclass(frozen=True)
class CommitmentExecutionRecord:
    seed: int
    module_count: int
    closure_probability: float
    recoverability_weight: float
    planner: str
    path_length: int
    activated_closure_count: int
    realized_closure_count: int
    recovery_feasible: bool
    irreversible_failure: bool


def _activated_indices(model: CommitmentHazardModel, path: tuple[GridCell, ...]) -> set[int]:
    traversed = set(zip(path, path[1:], strict=False))
    return {
        index
        for index, closure in enumerate(model.closures)
        if closure.trigger in traversed
    }


def _realize_after_commitment(
    grid: GridMap,
    current: GridCell,
    model: CommitmentHazardModel,
    active: set[int],
    seed: int,
) -> tuple[GridMap, int]:
    rng = random.Random(seed)
    obstacles = set(grid.obstacles)
    realized = 0
    for index in sorted(active):
        closure = model.closures[index]
        if closure.closure_cell == current:
            continue
        if rng.random() < closure.closure_probability:
            obstacles.add(closure.closure_cell)
            realized += 1
    updated = GridMap.from_obstacles(
        grid.width,
        grid.height,
        obstacles=obstacles,
        risk=grid.risk,
        uncertainty=grid.uncertainty,
    )
    return updated, realized


def run_commitment_execution_benchmark(
    *,
    seeds: tuple[int, ...] = tuple(range(1000)),
    module_count: int = 3,
    closure_probabilities: tuple[float, ...] = (0.2, 0.5, 0.8),
    recoverability_weight: float = 8.0,
) -> list[CommitmentExecutionRecord]:
    if not seeds:
        raise ValueError("seeds cannot be empty")
    records: list[CommitmentExecutionRecord] = []

    for probability in closure_probabilities:
        grid, start, goal, safe, model = multi_commitment_world(module_count, probability)
        shortest = commitment_aware_astar(
            grid,
            start,
            goal,
            safe_cells=safe,
            hazard_model=model,
            mode=CommitmentPlannerMode.SHORTEST,
        )
        exact = commitment_aware_astar(
            grid,
            start,
            goal,
            safe_cells=safe,
            hazard_model=model,
            mode=CommitmentPlannerMode.HISTORY_AWARE,
            config=CommitmentAwareAStarConfig(
                recoverability_weight=recoverability_weight,
                max_hazard_cells=max(16, module_count),
            ),
        )
        cut = commitment_cut_astar(
            grid,
            start,
            goal,
            safe_cells=safe,
            hazard_model=model,
            config=CommitmentCutAStarConfig(recoverability_weight=recoverability_weight),
        )

        plans = {
            "shortest": shortest,
            "history_exact": exact,
            "history_cut": cut,
        }
        for planner, result in plans.items():
            if not result.success:
                raise RuntimeError(f"planner {planner} failed in controlled execution benchmark")
            path = tuple(result.path)
            active = _activated_indices(model, path)
            for seed in seeds:
                updated, realized = _realize_after_commitment(
                    grid, goal, model, active, seed
                )
                recovery_infeasible = return_failure_probability(updated, goal, safe) >= 1.0
                records.append(
                    CommitmentExecutionRecord(
                        seed=seed,
                        module_count=module_count,
                        closure_probability=probability,
                        recoverability_weight=recoverability_weight,
                        planner=planner,
                        path_length=result.geometric_length,
                        activated_closure_count=len(active),
                        realized_closure_count=realized,
                        recovery_feasible=not recovery_infeasible,
                        irreversible_failure=recovery_infeasible,
                    )
                )
    return records


def summarize_commitment_execution(records: list[CommitmentExecutionRecord]) -> dict[str, object]:
    if not records:
        raise ValueError("records cannot be empty")
    grouped: dict[str, list[CommitmentExecutionRecord]] = {}
    for row in records:
        key = f"{row.planner}:p={row.closure_probability}"
        grouped.setdefault(key, []).append(row)
    result: dict[str, object] = {}
    for key, rows in sorted(grouped.items()):
        result[key] = {
            "trials": len(rows),
            "irreversible_failure_rate": sum(row.irreversible_failure for row in rows) / len(rows),
            "recovery_feasible_rate": sum(row.recovery_feasible for row in rows) / len(rows),
            "mean_realized_closures": sum(row.realized_closure_count for row in rows) / len(rows),
            "path_length": rows[0].path_length,
            "activated_closure_count": rows[0].activated_closure_count,
        }
    return result


def write_commitment_execution_artifacts(
    records: list[CommitmentExecutionRecord], output_dir: str | Path
) -> None:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    with (target / "trials.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(records[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(row) for row in records)
    with (target / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summarize_commitment_execution(records), handle, indent=2, sort_keys=True)
