"""Development V4 study of equal-marginal correlated topology closures.

Two topology classes are deliberately included:
- parallel redundant corridors, where positive common-cause dependence makes an
  independence model optimistic about return connectivity;
- serial critical cells, where the same positive dependence can make the
  independence model pessimistic.

The purpose is to demonstrate that equal marginals do not determine network
reliability, not to claim a universal direction of correlation error.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from dynnav.planners.grid_map import GridCell, GridMap
from dynnav.recoverability_belief import (
    TopologyHazardBelief,
    exact_safe_return_probability,
)
from dynnav.recoverability_scenarios import (
    equal_marginal_common_cause_belief,
    exact_scenario_safe_return_probability,
)


@dataclass(frozen=True)
class CorrelationReliabilityRecord:
    topology: str
    marginal_probability: float
    correlation: float
    independent_return_probability: float
    joint_return_probability: float
    signed_independence_error: float
    absolute_independence_error: float


def _parallel_corridors() -> tuple[
    GridMap,
    GridCell,
    set[GridCell],
    tuple[GridCell, ...],
]:
    free = {
        (0, 0),
        (1, 0),
        (2, 0),
        (0, 2),
        (1, 2),
        (2, 2),
        (0, 1),
        (2, 1),
    }
    obstacles = {
        (x, y)
        for x in range(3)
        for y in range(3)
        if (x, y) not in free
    }
    return (
        GridMap.from_obstacles(3, 3, obstacles=obstacles),
        (2, 1),
        {(0, 1)},
        ((1, 0), (1, 2)),
    )


def _serial_corridor() -> tuple[
    GridMap,
    GridCell,
    set[GridCell],
    tuple[GridCell, ...],
]:
    grid = GridMap.from_obstacles(5, 1)
    return grid, (4, 0), {(0, 0)}, ((1, 0), (3, 0))


def run_correlation_reliability_benchmark(
    *,
    marginal_probabilities: tuple[float, ...] = (0.25, 0.50, 0.80),
    correlations: tuple[float, ...] = (0.0, 0.25, 0.50, 0.75, 1.0),
) -> list[CorrelationReliabilityRecord]:
    worlds = {
        "parallel_joint_cut": _parallel_corridors(),
        "serial_any_cut": _serial_corridor(),
    }
    records: list[CorrelationReliabilityRecord] = []

    for topology, (grid, current, safe, closure_cells) in worlds.items():
        for p in marginal_probabilities:
            for rho in correlations:
                independent = exact_safe_return_probability(
                    grid,
                    current,
                    safe,
                    TopologyHazardBelief(
                        {cell: float(p) for cell in closure_cells}
                    ),
                    max_hazard_cells=len(closure_cells),
                )
                joint = exact_scenario_safe_return_probability(
                    grid,
                    current,
                    safe,
                    equal_marginal_common_cause_belief(
                        closure_cells,
                        marginal_probability=float(p),
                        correlation=float(rho),
                    ),
                )
                error = independent - joint
                records.append(
                    CorrelationReliabilityRecord(
                        topology=topology,
                        marginal_probability=float(p),
                        correlation=float(rho),
                        independent_return_probability=independent,
                        joint_return_probability=joint,
                        signed_independence_error=error,
                        absolute_independence_error=abs(error),
                    )
                )
    return records


def summarize_correlation_reliability(
    records: list[CorrelationReliabilityRecord],
) -> dict[str, object]:
    if not records:
        raise ValueError("records cannot be empty")
    by_topology: dict[str, list[CorrelationReliabilityRecord]] = {}
    for row in records:
        by_topology.setdefault(row.topology, []).append(row)

    summary: dict[str, object] = {
        "status": "development_only_not_publication_evidence",
        "record_count": len(records),
        "topologies": {},
    }
    topologies = summary["topologies"]
    assert isinstance(topologies, dict)
    for topology, rows in sorted(by_topology.items()):
        topologies[topology] = {
            "max_absolute_independence_error": max(
                row.absolute_independence_error for row in rows
            ),
            "min_signed_independence_error": min(
                row.signed_independence_error for row in rows
            ),
            "max_signed_independence_error": max(
                row.signed_independence_error for row in rows
            ),
        }
    return summary


def write_correlation_reliability_artifacts(
    records: list[CorrelationReliabilityRecord],
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
            summarize_correlation_reliability(records),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
