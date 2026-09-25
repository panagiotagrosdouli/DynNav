"""Repeated timing distributions for publication-facing DynNav components.

These measurements are descriptive and runner-specific.  They are intended to
replace single-shot latency values with distributions (median, IQR, p95) while
keeping correctness outputs fixed across repetitions.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from dynnav.experiments.cut_scaling_benchmark import _series_problem
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
from dynnav.recoverability_belief import exact_safe_return_probability
from dynnav.recoverability_cut import critical_return_cut_upper_bound


@dataclass(frozen=True)
class TimingRecord:
    benchmark: str
    method: str
    repetition: int
    elapsed_ms: float
    result_value: float
    nodes_expanded: int | None = None
    geometric_length: int | None = None


def _percentile(values: list[float], q: float) -> float:
    if not values:
        raise ValueError("values cannot be empty")
    if not 0.0 <= q <= 1.0:
        raise ValueError("q must be in [0, 1]")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = q * (len(ordered) - 1)
    lo = math.floor(position)
    hi = math.ceil(position)
    if lo == hi:
        return ordered[lo]
    weight = position - lo
    return ordered[lo] * (1.0 - weight) + ordered[hi] * weight


def _summary(values: list[float]) -> dict[str, float | int]:
    return {
        "n": len(values),
        "median_ms": statistics.median(values),
        "q1_ms": _percentile(values, 0.25),
        "q3_ms": _percentile(values, 0.75),
        "iqr_ms": _percentile(values, 0.75) - _percentile(values, 0.25),
        "p95_ms": _percentile(values, 0.95),
        "mean_ms": statistics.fmean(values),
        "min_ms": min(values),
        "max_ms": max(values),
    }


def run_repeated_timing_benchmark(
    *,
    repetitions: int = 100,
    warmups: int = 10,
    oracle_hazard_count: int = 12,
    planner_modules: int = 6,
    closure_probability: float = 0.2,
    planner_closure_probability: float = 0.5,
    recoverability_weight: float = 4.0,
) -> list[TimingRecord]:
    if repetitions < 2:
        raise ValueError("repetitions must be at least 2")
    if warmups < 0:
        raise ValueError("warmups must be non-negative")

    records: list[TimingRecord] = []

    grid, cell, safe, hazard = _series_problem(
        oracle_hazard_count, closure_probability
    )
    expected_exact: float | None = None
    expected_cut: float | None = None
    for repetition in range(-warmups, repetitions):
        start = time.perf_counter_ns()
        exact = exact_safe_return_probability(
            grid,
            cell,
            safe,
            hazard,
            max_hazard_cells=oracle_hazard_count,
        )
        elapsed = (time.perf_counter_ns() - start) / 1_000_000.0
        if expected_exact is None:
            expected_exact = exact
        elif exact != expected_exact:
            raise RuntimeError("exact oracle result changed across repetitions")
        if repetition >= 0:
            records.append(
                TimingRecord(
                    benchmark=f"oracle_h{oracle_hazard_count}",
                    method="exact",
                    repetition=repetition,
                    elapsed_ms=elapsed,
                    result_value=exact,
                )
            )

        start = time.perf_counter_ns()
        cut = critical_return_cut_upper_bound(grid, cell, safe, hazard)
        elapsed = (time.perf_counter_ns() - start) / 1_000_000.0
        if expected_cut is None:
            expected_cut = cut.probability_upper_bound
        elif cut.probability_upper_bound != expected_cut:
            raise RuntimeError("critical-cut result changed across repetitions")
        if repetition >= 0:
            records.append(
                TimingRecord(
                    benchmark=f"oracle_h{oracle_hazard_count}",
                    method="critical_cut",
                    repetition=repetition,
                    elapsed_ms=elapsed,
                    result_value=cut.probability_upper_bound,
                )
            )

    grid, start_cell, goal, safe_cells, model = multi_commitment_world(
        planner_modules, planner_closure_probability
    )

    def run_planner(method: str):
        if method == "shortest_augmented":
            return commitment_aware_astar(
                grid,
                start_cell,
                goal,
                safe_cells=safe_cells,
                hazard_model=model,
                mode=CommitmentPlannerMode.SHORTEST,
            )
        if method == "history_exact":
            return commitment_aware_astar(
                grid,
                start_cell,
                goal,
                safe_cells=safe_cells,
                hazard_model=model,
                mode=CommitmentPlannerMode.HISTORY_AWARE,
                config=CommitmentAwareAStarConfig(
                    recoverability_weight=recoverability_weight,
                    max_hazard_cells=max(16, len(model.closures)),
                ),
            )
        return commitment_cut_astar(
            grid,
            start_cell,
            goal,
            safe_cells=safe_cells,
            hazard_model=model,
            config=CommitmentCutAStarConfig(
                recoverability_weight=recoverability_weight
            ),
        )

    expected: dict[str, tuple[int, int, int]] = {}
    for method in ("shortest_augmented", "history_cut", "history_exact"):
        for repetition in range(-warmups, repetitions):
            start = time.perf_counter_ns()
            result = run_planner(method)
            elapsed = (time.perf_counter_ns() - start) / 1_000_000.0
            if not result.success:
                raise RuntimeError(f"{method} failed during timing benchmark")
            signature = (
                result.geometric_length,
                result.activated_closure_count,
                result.nodes_expanded,
            )
            if method not in expected:
                expected[method] = signature
            elif signature != expected[method]:
                raise RuntimeError(f"{method} result changed across repetitions")
            if repetition >= 0:
                result_value = (
                    float(result.final_return_upper_bound)
                    if method == "history_cut"
                    else float(result.final_return_probability)
                )
                records.append(
                    TimingRecord(
                        benchmark=f"planner_m{planner_modules}",
                        method=method,
                        repetition=repetition,
                        elapsed_ms=elapsed,
                        result_value=result_value,
                        nodes_expanded=result.nodes_expanded,
                        geometric_length=result.geometric_length,
                    )
                )

    return records


def summarize_repeated_timings(records: list[TimingRecord]) -> dict[str, object]:
    if not records:
        raise ValueError("records cannot be empty")
    summary: dict[str, object] = {}
    for benchmark in sorted({row.benchmark for row in records}):
        summary[benchmark] = {}
        methods = sorted(
            {row.method for row in records if row.benchmark == benchmark}
        )
        for method in methods:
            rows = [
                row
                for row in records
                if row.benchmark == benchmark and row.method == method
            ]
            block = _summary([row.elapsed_ms for row in rows])
            block["result_value"] = rows[0].result_value
            if rows[0].nodes_expanded is not None:
                block["nodes_expanded"] = rows[0].nodes_expanded
            if rows[0].geometric_length is not None:
                block["geometric_length"] = rows[0].geometric_length
            summary[benchmark][method] = block

    oracle_keys = [key for key in summary if key.startswith("oracle_h")]
    for key in oracle_keys:
        exact = summary[key]["exact"]["median_ms"]
        cut = summary[key]["critical_cut"]["median_ms"]
        summary[key]["median_speedup_exact_over_cut"] = exact / cut if cut > 0 else None
    return summary


def write_repeated_timing_artifacts(
    records: list[TimingRecord], output_dir: str | Path
) -> None:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    with (target / "trials.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(records[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(row) for row in records)
    with (target / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(
            summarize_repeated_timings(records),
            handle,
            indent=2,
            sort_keys=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="results/repeated_timings")
    parser.add_argument("--repetitions", type=int, default=100)
    parser.add_argument("--warmups", type=int, default=10)
    args = parser.parse_args()
    records = run_repeated_timing_benchmark(
        repetitions=args.repetitions,
        warmups=args.warmups,
    )
    write_repeated_timing_artifacts(records, args.output_dir)


if __name__ == "__main__":
    main()
