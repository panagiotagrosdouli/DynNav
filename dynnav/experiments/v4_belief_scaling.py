"""Development and publication scaling benchmark for exact V4 belief planning.

The benchmark uses a deliberately simple one-dimensional mission graph so
topology/search branching does not hide the cost of the exact categorical
belief and posterior-predictive return-connectivity oracle.

Hazard count m produces a final predictive armed-set support of 2**m when
q=0.5. Each armed set is evaluated with the exact independent-closure oracle.
The benchmark records the first configuration that exceeds a declared runtime
budget rather than silently omitting it.
"""

from __future__ import annotations

import csv
import json
import math
import statistics
import time
import tracemalloc
from dataclasses import asdict, dataclass
from pathlib import Path

from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.planners.belief_commitment_astar import (
    BeliefCommitmentAStarConfig,
    belief_commitment_astar,
)
from dynnav.planners.grid_map import GridMap


@dataclass(frozen=True)
class BeliefScalingRecord:
    hazard_count: int
    repetition: int
    success: bool
    wall_time_ms: float
    planner_reported_time_ms: float
    peak_memory_bytes: int
    nodes_expanded: int
    oracle_calls: int
    final_belief_support_size: int
    expected_support_size: int
    geometric_length: int
    budget_exceeded: bool


@dataclass(frozen=True)
class BeliefScalingSummary:
    hazard_count: int
    repetitions: int
    completed: bool
    median_wall_time_ms: float
    iqr_wall_time_ms: float
    p95_wall_time_ms: float
    median_peak_memory_bytes: float
    median_nodes_expanded: float
    median_oracle_calls: float
    final_belief_support_size: int
    expected_support_size: int


def scaling_world(
    hazard_count: int,
) -> tuple[
    GridMap,
    tuple[int, int],
    tuple[int, int],
    set[tuple[int, int]],
    CommitmentHazardModel,
]:
    """Return a serial-return world with exactly hazard_count triggers."""

    if hazard_count < 0:
        raise ValueError("hazard_count must be non-negative")

    width = hazard_count + 2
    height = 2
    start = (0, 0)
    safe = {(0, 1)}
    goal = (hazard_count + 1, 0)

    obstacles = {(x, 1) for x in range(1, width)}
    grid = GridMap.from_obstacles(
        width,
        height,
        obstacles=obstacles,
    )

    model = CommitmentHazardModel(
        tuple(
            CommitmentClosure(
                trigger=((index, 0), (index + 1, 0)),
                closure_cell=(index + 1, 0),
                closure_probability=0.5,
            )
            for index in range(hazard_count)
        )
    )
    model.validate(grid)
    return grid, start, goal, safe, model


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return float("nan")
    if not 0.0 <= q <= 1.0:
        raise ValueError("q must be in [0, 1]")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = q * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _iqr(values: list[float]) -> float:
    return _percentile(values, 0.75) - _percentile(values, 0.25)


def _run_one(hazard_count: int, repetition: int) -> BeliefScalingRecord:
    grid, start, goal, safe, model = scaling_world(hazard_count)
    q = (0.5,) * hazard_count

    tracemalloc.start()
    t0 = time.perf_counter()
    try:
        result = belief_commitment_astar(
            grid,
            start,
            goal,
            safe_cells=safe,
            hazard_model=model,
            arming_probabilities=q,
            config=BeliefCommitmentAStarConfig(
                recoverability_weight=8.0,
                max_hazard_cells=max(16, hazard_count),
            ),
        )
        wall_ms = (time.perf_counter() - t0) * 1000.0
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    return BeliefScalingRecord(
        hazard_count=hazard_count,
        repetition=repetition,
        success=result.success,
        wall_time_ms=wall_ms,
        planner_reported_time_ms=result.planning_time_ms,
        peak_memory_bytes=int(peak),
        nodes_expanded=result.nodes_expanded,
        oracle_calls=result.return_oracle_calls,
        final_belief_support_size=result.final_belief_support_size,
        expected_support_size=2**hazard_count,
        geometric_length=result.geometric_length,
        budget_exceeded=False,
    )


def run_belief_scaling_benchmark(
    *,
    hazard_counts: tuple[int, ...] = (1, 2, 4, 6, 8, 10, 12),
    warmups: int = 1,
    repetitions: int = 3,
    per_call_budget_s: float = 10.0,
) -> list[BeliefScalingRecord]:
    if not hazard_counts:
        raise ValueError("hazard_counts cannot be empty")
    if any(count < 0 for count in hazard_counts):
        raise ValueError("hazard counts must be non-negative")
    if warmups < 0:
        raise ValueError("warmups must be non-negative")
    if repetitions <= 0:
        raise ValueError("repetitions must be positive")
    if per_call_budget_s <= 0.0:
        raise ValueError("per_call_budget_s must be positive")

    records: list[BeliefScalingRecord] = []
    stop_after_budget = False

    for hazard_count in hazard_counts:
        if stop_after_budget:
            break

        for _ in range(warmups):
            warmup = _run_one(hazard_count, -1)
            if warmup.wall_time_ms > per_call_budget_s * 1000.0:
                records.append(
                    BeliefScalingRecord(
                        **{
                            **asdict(warmup),
                            "repetition": 0,
                            "budget_exceeded": True,
                        }
                    )
                )
                stop_after_budget = True
                break

        if stop_after_budget:
            break

        for repetition in range(repetitions):
            row = _run_one(hazard_count, repetition)
            exceeded = row.wall_time_ms > per_call_budget_s * 1000.0
            if exceeded:
                row = BeliefScalingRecord(
                    **{
                        **asdict(row),
                        "budget_exceeded": True,
                    }
                )
            records.append(row)
            if exceeded:
                stop_after_budget = True
                break

    return records


def summarize_belief_scaling(
    records: list[BeliefScalingRecord],
) -> dict[str, object]:
    if not records:
        raise ValueError("records cannot be empty")

    groups: dict[int, list[BeliefScalingRecord]] = {}
    for row in records:
        groups.setdefault(row.hazard_count, []).append(row)

    summaries: list[BeliefScalingSummary] = []
    first_budget_exceeded: int | None = None
    for hazard_count, group in sorted(groups.items()):
        measured = [row for row in group if row.repetition >= 0]
        if not measured:
            continue
        times = [row.wall_time_ms for row in measured]
        peaks = [float(row.peak_memory_bytes) for row in measured]
        nodes = [float(row.nodes_expanded) for row in measured]
        calls = [float(row.oracle_calls) for row in measured]
        exceeded = any(row.budget_exceeded for row in measured)
        if exceeded and first_budget_exceeded is None:
            first_budget_exceeded = hazard_count

        last = measured[-1]
        summaries.append(
            BeliefScalingSummary(
                hazard_count=hazard_count,
                repetitions=len(measured),
                completed=not exceeded,
                median_wall_time_ms=statistics.median(times),
                iqr_wall_time_ms=_iqr(times),
                p95_wall_time_ms=_percentile(times, 0.95),
                median_peak_memory_bytes=statistics.median(peaks),
                median_nodes_expanded=statistics.median(nodes),
                median_oracle_calls=statistics.median(calls),
                final_belief_support_size=last.final_belief_support_size,
                expected_support_size=last.expected_support_size,
            )
        )

    return {
        "status": "development_only_not_publication_evidence",
        "first_budget_exceeded_hazard_count": first_budget_exceeded,
        "summaries": [asdict(item) for item in summaries],
    }


def write_belief_scaling_artifacts(
    records: list[BeliefScalingRecord],
    output_dir: str | Path,
) -> None:
    if not records:
        raise ValueError("records cannot be empty")

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    rows = [asdict(record) for record in records]

    with (destination / "trials.csv").open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    (destination / "summary.json").write_text(
        json.dumps(
            summarize_belief_scaling(records),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
