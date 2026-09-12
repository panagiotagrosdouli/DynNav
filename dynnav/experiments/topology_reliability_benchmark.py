"""Controlled benchmark for belief-conditioned safe-return reliability estimators."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from dynnav.planners.grid_map import GridMap
from dynnav.recoverability import analyze_recoverability
from dynnav.recoverability_belief import TopologyBelief, exact_safe_return_probability
from dynnav.recoverability_estimation import most_reliable_return_path


@dataclass(frozen=True)
class TopologyReliabilityRecord:
    topology: str
    blocked_probability: float
    exact_return_probability: float
    most_reliable_path_probability: float
    estimator_absolute_error: float
    structural_irreversibility: float


def _series_bridge(probability: float) -> TopologyReliabilityRecord:
    grid = GridMap.from_obstacles(5, 1)
    start = (4, 0)
    safe = {(0, 0)}
    belief = TopologyBelief({(2, 0): probability})
    exact = exact_safe_return_probability(grid, start, safe, belief)
    estimate = most_reliable_return_path(grid, start, safe, belief).probability
    structural = analyze_recoverability(grid, start, safe).irreversibility
    return TopologyReliabilityRecord(
        topology="series_bridge",
        blocked_probability=probability,
        exact_return_probability=exact,
        most_reliable_path_probability=estimate,
        estimator_absolute_error=abs(exact - estimate),
        structural_irreversibility=structural,
    )


def _parallel_bridges(probability: float) -> TopologyReliabilityRecord:
    grid = GridMap.from_obstacles(3, 3, obstacles={(1, 1)})
    start = (2, 1)
    safe = {(0, 1)}
    belief = TopologyBelief({(1, 0): probability, (1, 2): probability})
    exact = exact_safe_return_probability(grid, start, safe, belief)
    estimate = most_reliable_return_path(grid, start, safe, belief).probability
    structural = analyze_recoverability(grid, start, safe).irreversibility
    return TopologyReliabilityRecord(
        topology="parallel_bridges",
        blocked_probability=probability,
        exact_return_probability=exact,
        most_reliable_path_probability=estimate,
        estimator_absolute_error=abs(exact - estimate),
        structural_irreversibility=structural,
    )


def run_topology_reliability_benchmark(
    probabilities: tuple[float, ...] = (0.1, 0.3, 0.5, 0.7, 0.9),
) -> list[TopologyReliabilityRecord]:
    if not probabilities:
        raise ValueError("at least one blockage probability is required")
    for probability in probabilities:
        if not 0.0 <= probability <= 1.0:
            raise ValueError("blockage probabilities must be in [0, 1]")

    records: list[TopologyReliabilityRecord] = []
    for probability in probabilities:
        records.append(_series_bridge(float(probability)))
        records.append(_parallel_bridges(float(probability)))
    return records


def summarize_topology_reliability(
    records: list[TopologyReliabilityRecord],
) -> dict[str, dict[str, float | int]]:
    if not records:
        raise ValueError("records cannot be empty")
    grouped: dict[str, list[TopologyReliabilityRecord]] = {}
    for record in records:
        grouped.setdefault(record.topology, []).append(record)

    summary: dict[str, dict[str, float | int]] = {}
    for topology, rows in sorted(grouped.items()):
        errors = [row.estimator_absolute_error for row in rows]
        structural_values = [row.structural_irreversibility for row in rows]
        summary[topology] = {
            "trials": len(rows),
            "estimator_mae": sum(errors) / len(errors),
            "structural_score_range": max(structural_values) - min(structural_values),
            "exact_probability_range": max(row.exact_return_probability for row in rows)
            - min(row.exact_return_probability for row in rows),
        }
    return summary


def write_topology_reliability_artifacts(
    records: list[TopologyReliabilityRecord], output_dir: str | Path
) -> None:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    with (target / "trials.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(records[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(record) for record in records)
    with (target / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summarize_topology_reliability(records), handle, indent=2, sort_keys=True)
