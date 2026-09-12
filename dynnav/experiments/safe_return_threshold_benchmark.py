"""Sensitivity benchmark for hard safe-return probability constraints."""
from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from dynnav.experiments.multi_commitment_benchmark import multi_commitment_world
from dynnav.planners.commitment_safe_return_astar import (
    SafeReturnConstraintConfig,
    commitment_safe_return_astar,
)


@dataclass(frozen=True)
class SafeReturnThresholdRecord:
    module_count: int
    closure_probability: float
    threshold: float
    success: bool
    geometric_length: int
    activated_closure_count: int
    minimum_return_probability: float
    rejected_transitions: int
    planning_time_ms: float


def run_safe_return_threshold_benchmark(
    *,
    module_count: int = 3,
    closure_probabilities: tuple[float, ...] = (0.1, 0.3, 0.5, 0.7, 0.9),
    thresholds: tuple[float, ...] = (0.1, 0.3, 0.5, 0.7, 0.9, 0.99),
) -> list[SafeReturnThresholdRecord]:
    records: list[SafeReturnThresholdRecord] = []
    for probability in closure_probabilities:
        grid, start, goal, safe, model = multi_commitment_world(
            module_count, probability
        )
        for threshold in thresholds:
            result = commitment_safe_return_astar(
                grid,
                start,
                goal,
                safe_cells=safe,
                hazard_model=model,
                config=SafeReturnConstraintConfig(
                    minimum_return_probability=threshold,
                    max_hazard_cells=max(16, module_count),
                ),
            )
            records.append(
                SafeReturnThresholdRecord(
                    module_count=module_count,
                    closure_probability=probability,
                    threshold=threshold,
                    success=result.success,
                    geometric_length=result.geometric_length,
                    activated_closure_count=result.activated_closure_count,
                    minimum_return_probability=result.minimum_return_probability,
                    rejected_transitions=result.rejected_transitions,
                    planning_time_ms=result.planning_time_ms,
                )
            )
    return records


def summarize_safe_return_threshold(
    records: list[SafeReturnThresholdRecord],
) -> dict[str, object]:
    if not records:
        raise ValueError("records cannot be empty")
    return {
        "trials": len(records),
        "success_rate": sum(row.success for row in records) / len(records),
        "detour_or_rejection_rate": sum(
            row.success and row.activated_closure_count == 0 for row in records
        ) / len(records),
        "per_threshold": {
            str(threshold): {
                "trials": len(rows),
                "success_rate": sum(row.success for row in rows) / len(rows),
                "mean_path_length_successes": (
                    sum(row.geometric_length for row in rows if row.success)
                    / sum(row.success for row in rows)
                    if any(row.success for row in rows)
                    else None
                ),
                "mean_activated_closures_successes": (
                    sum(row.activated_closure_count for row in rows if row.success)
                    / sum(row.success for row in rows)
                    if any(row.success for row in rows)
                    else None
                ),
            }
            for threshold in sorted({row.threshold for row in records})
            for rows in [[row for row in records if row.threshold == threshold]]
        },
    }


def write_safe_return_threshold_artifacts(
    records: list[SafeReturnThresholdRecord], output_dir: str | Path
) -> None:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    with (target / "trials.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(records[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(row) for row in records)
    with (target / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(
            summarize_safe_return_threshold(records), handle, indent=2, sort_keys=True
        )
