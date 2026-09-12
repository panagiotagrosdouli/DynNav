"""Scaling benchmark for augmented history-conditioned search state."""
from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

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


@dataclass(frozen=True)
class HistoryStateScalingRecord:
    module_count: int
    closure_probability: float
    recoverability_weight: float
    planner: str
    success: bool
    geometric_length: int
    activated_closure_count: int
    nodes_expanded: int
    planning_time_ms: float


def run_history_state_scaling_benchmark(
    *,
    module_counts: tuple[int, ...] = (1, 2, 3, 4, 5, 6),
    closure_probability: float = 0.5,
    recoverability_weight: float = 4.0,
) -> list[HistoryStateScalingRecord]:
    records: list[HistoryStateScalingRecord] = []
    for modules in module_counts:
        grid, start, goal, safe, model = multi_commitment_world(
            modules, closure_probability
        )
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
                max_hazard_cells=max(16, modules),
            ),
        )
        cut = commitment_cut_astar(
            grid,
            start,
            goal,
            safe_cells=safe,
            hazard_model=model,
            config=CommitmentCutAStarConfig(
                recoverability_weight=recoverability_weight
            ),
        )
        for planner, result in (
            ("shortest_augmented", shortest),
            ("history_exact", exact),
            ("history_cut", cut),
        ):
            records.append(
                HistoryStateScalingRecord(
                    module_count=modules,
                    closure_probability=closure_probability,
                    recoverability_weight=(
                        0.0 if planner == "shortest_augmented" else recoverability_weight
                    ),
                    planner=planner,
                    success=result.success,
                    geometric_length=result.geometric_length,
                    activated_closure_count=result.activated_closure_count,
                    nodes_expanded=result.nodes_expanded,
                    planning_time_ms=result.planning_time_ms,
                )
            )
    return records


def summarize_history_state_scaling(
    records: list[HistoryStateScalingRecord],
) -> dict[str, object]:
    if not records:
        raise ValueError("records cannot be empty")
    grouped: dict[str, list[HistoryStateScalingRecord]] = {}
    for row in records:
        grouped.setdefault(row.planner, []).append(row)
    return {
        planner: {
            "trials": len(rows),
            "max_modules": max(row.module_count for row in rows),
            "max_nodes_expanded": max(row.nodes_expanded for row in rows),
            "max_planning_time_ms": max(row.planning_time_ms for row in rows),
            "per_module": {
                str(row.module_count): {
                    "nodes_expanded": row.nodes_expanded,
                    "planning_time_ms": row.planning_time_ms,
                    "geometric_length": row.geometric_length,
                    "activated_closure_count": row.activated_closure_count,
                }
                for row in sorted(rows, key=lambda item: item.module_count)
            },
        }
        for planner, rows in sorted(grouped.items())
    }


def write_history_state_scaling_artifacts(
    records: list[HistoryStateScalingRecord], output_dir: str | Path
) -> None:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    with (target / "trials.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(records[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(row) for row in records)
    with (target / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(
            summarize_history_state_scaling(records),
            handle,
            indent=2,
            sort_keys=True,
        )
