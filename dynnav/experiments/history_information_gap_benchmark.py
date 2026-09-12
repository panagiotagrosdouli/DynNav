"""Counterfactual benchmark for recoverability information lost by state-only beliefs."""
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
from dynnav.planners.grid_map import GridMap
from dynnav.recoverability_belief import TopologyHazardBelief, exact_safe_return_probability


@dataclass(frozen=True)
class HistoryInformationGapRecord:
    closure_probability: float
    risky_history_return_probability: float
    safe_history_return_probability: float
    state_only_return_probability: float
    history_separation: float
    safe_history_state_only_error: float
    risky_history_state_only_error: float


def _counterfactual_problem(probability: float):
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must be in [0, 1]")
    # Both paths terminate at (3,1). Only the lower route traverses the trigger.
    # Cell (1,1) is the sole bridge back to the safe start region.
    grid = GridMap.from_obstacles(4, 3, obstacles={(1, 0), (1, 2)})
    start = (0, 1)
    endpoint = (3, 1)
    risky_path = (start, (1, 1), (2, 1), endpoint)
    safe_path = (start, (1, 1), (2, 1), (2, 0), (3, 0), endpoint)
    model = CommitmentHazardModel(
        (
            CommitmentClosure(
                trigger=((2, 1), endpoint),
                closure_cell=(1, 1),
                closure_probability=probability,
            ),
        )
    )
    return grid, start, endpoint, risky_path, safe_path, model


def run_history_information_gap_benchmark(
    probabilities: tuple[float, ...] = (0.1, 0.3, 0.5, 0.7, 0.9),
) -> list[HistoryInformationGapRecord]:
    records: list[HistoryInformationGapRecord] = []
    for probability in probabilities:
        grid, start, endpoint, risky_path, safe_path, model = _counterfactual_problem(probability)
        risky = exact_history_conditioned_return_probability(
            grid, risky_path, {start}, model
        )
        safe = exact_history_conditioned_return_probability(
            grid, safe_path, {start}, model
        )
        # A state-only marginal model sees the same current cell and same
        # closure marginal under either history, so it must assign one value.
        state_only = exact_safe_return_probability(
            grid,
            endpoint,
            {start},
            TopologyHazardBelief({(1, 1): probability}),
        )
        records.append(
            HistoryInformationGapRecord(
                closure_probability=probability,
                risky_history_return_probability=risky,
                safe_history_return_probability=safe,
                state_only_return_probability=state_only,
                history_separation=safe - risky,
                safe_history_state_only_error=state_only - safe,
                risky_history_state_only_error=state_only - risky,
            )
        )
    return records


def summarize_history_information_gap(
    records: list[HistoryInformationGapRecord],
) -> dict[str, float | int]:
    if not records:
        raise ValueError("records cannot be empty")
    return {
        "trials": len(records),
        "mean_history_separation": sum(r.history_separation for r in records) / len(records),
        "max_history_separation": max(r.history_separation for r in records),
        "mean_safe_history_state_only_error": sum(r.safe_history_state_only_error for r in records) / len(records),
        "max_absolute_risky_history_state_only_error": max(abs(r.risky_history_state_only_error) for r in records),
    }


def write_history_information_gap_artifacts(
    records: list[HistoryInformationGapRecord], output_dir: str | Path
) -> None:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    with (target / "trials.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(records[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(row) for row in records)
    with (target / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summarize_history_information_gap(records), handle, indent=2, sort_keys=True)
