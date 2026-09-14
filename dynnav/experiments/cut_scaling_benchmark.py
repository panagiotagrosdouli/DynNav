"""Scaling benchmark for exact versus critical-cut return reliability."""
from __future__ import annotations

import csv
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from dynnav.planners.grid_map import GridMap
from dynnav.recoverability_belief import TopologyHazardBelief, exact_safe_return_probability
from dynnav.recoverability_cut import critical_return_cut_upper_bound


@dataclass(frozen=True)
class CutScalingRecord:
    hazard_count: int
    method: str
    probability: float
    elapsed_ms: float
    absolute_error: float


def _series_problem(hazard_count: int, probability: float):
    if hazard_count < 1:
        raise ValueError("hazard_count must be positive")
    width = 2 * hazard_count + 3
    grid = GridMap.from_obstacles(width, 1)
    start = (0, 0)
    cell = (width - 1, 0)
    hazards = {
        (2 * index + 1, 0): probability
        for index in range(hazard_count)
    }
    return grid, cell, {start}, TopologyHazardBelief(hazards)


def run_cut_scaling_benchmark(
    hazard_counts: tuple[int, ...] = (1, 2, 4, 6, 8, 10, 12),
    closure_probability: float = 0.2,
) -> list[CutScalingRecord]:
    if not 0.0 <= closure_probability <= 1.0:
        raise ValueError("closure_probability must be in [0, 1]")
    records: list[CutScalingRecord] = []
    for count in hazard_counts:
        grid, cell, safe, hazard = _series_problem(count, closure_probability)

        t0 = time.perf_counter()
        exact = exact_safe_return_probability(
            grid, cell, safe, hazard, max_hazard_cells=max(hazard_counts)
        )
        exact_ms = (time.perf_counter() - t0) * 1000.0

        t1 = time.perf_counter()
        estimate = critical_return_cut_upper_bound(grid, cell, safe, hazard)
        cut_ms = (time.perf_counter() - t1) * 1000.0

        records.append(CutScalingRecord(count, "exact", exact, exact_ms, 0.0))
        records.append(
            CutScalingRecord(
                count,
                "critical_cut",
                estimate.probability_upper_bound,
                cut_ms,
                abs(estimate.probability_upper_bound - exact),
            )
        )
    return records


def summarize_cut_scaling(records: list[CutScalingRecord]) -> dict[str, object]:
    if not records:
        raise ValueError("records cannot be empty")
    exact = {row.hazard_count: row for row in records if row.method == "exact"}
    cut = {row.hazard_count: row for row in records if row.method == "critical_cut"}
    common = sorted(set(exact) & set(cut))
    return {
        "hazard_counts": common,
        "max_cut_absolute_error": max(cut[count].absolute_error for count in common),
        "per_hazard_count": {
            str(count): {
                "exact_ms": exact[count].elapsed_ms,
                "critical_cut_ms": cut[count].elapsed_ms,
                "speedup_exact_over_cut": (
                    exact[count].elapsed_ms / cut[count].elapsed_ms
                    if cut[count].elapsed_ms > 0.0
                    else None
                ),
                "probability": exact[count].probability,
                "absolute_error": cut[count].absolute_error,
            }
            for count in common
        },
    }


def write_cut_scaling_artifacts(records: list[CutScalingRecord], output_dir: str | Path) -> None:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    with (target / "trials.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(records[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(row) for row in records)
    with (target / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summarize_cut_scaling(records), handle, indent=2, sort_keys=True)
