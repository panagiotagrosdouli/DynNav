"""Benchmark runner for deterministic DynNav experiments."""

from __future__ import annotations

import argparse
import csv
import statistics
from pathlib import Path

from dynnav.config import DynNavConfig
from dynnav.planning import RiskAwareAStar
from dynnav.scenarios import generate_scenario


CSV_FIELDS = [
    "seed",
    "path_found",
    "path_length",
    "cost",
    "risk",
    "recoverability",
    "expanded_nodes",
]


def run_benchmark(config: DynNavConfig) -> list[dict[str, float | int | bool]]:
    """Run deterministic benchmark scenarios and return row dictionaries."""
    planner = RiskAwareAStar(
        risk_weight=config.risk_weight,
        returnability_weight=config.returnability_weight,
        alpha=config.cvar_alpha,
        max_expansions=config.max_expansions,
    )
    rows: list[dict[str, float | int | bool]] = []
    for offset in range(config.n_scenarios):
        seed = config.seed + offset
        scenario = generate_scenario(
            config.width,
            config.height,
            config.obstacle_density,
            config.unknown_fraction,
            seed,
        )
        trajectory, metrics = planner.plan(scenario.grid, scenario.start, scenario.goal)
        rows.append(
            {
                "seed": seed,
                "path_found": metrics.path_found,
                "path_length": trajectory.length,
                "cost": trajectory.cost,
                "risk": trajectory.risk,
                "recoverability": trajectory.recoverability,
                "expanded_nodes": metrics.expanded_nodes,
            }
        )
    return rows


def write_csv(rows: list[dict[str, float | int | bool]], path: Path) -> None:
    """Write benchmark rows to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(rows: list[dict[str, float | int | bool]], path: Path) -> None:
    """Write a Markdown benchmark summary table."""
    path.parent.mkdir(parents=True, exist_ok=True)
    found = [row for row in rows if bool(row["path_found"])]
    success_rate = len(found) / max(len(rows), 1)
    mean_risk = statistics.fmean(float(row["risk"]) for row in found) if found else 1.0
    mean_length = statistics.fmean(float(row["path_length"]) for row in found) if found else 0.0
    mean_expansions = statistics.fmean(float(row["expanded_nodes"]) for row in rows) if rows else 0.0
    path.write_text(
        "# DynNav Benchmark Summary\n\n"
        "| Metric | Value |\n|---|---:|\n"
        f"| Scenarios | {len(rows)} |\n"
        f"| Success rate | {success_rate:.3f} |\n"
        f"| Mean path length | {mean_length:.2f} |\n"
        f"| Mean terminal risk | {mean_risk:.3f} |\n"
        f"| Mean expanded nodes | {mean_expansions:.1f} |\n",
        encoding="utf-8",
    )


def main() -> None:
    """Command-line benchmark entry point."""
    parser = argparse.ArgumentParser(description="Run DynNav deterministic benchmarks")
    parser.add_argument("--config", default="configs/benchmark.yaml")
    parser.add_argument("--out-csv", default="results/benchmarks/dynnav_benchmark.csv")
    parser.add_argument("--summary", default="results/benchmarks/summary.md")
    args = parser.parse_args()
    config = DynNavConfig.from_yaml(args.config)
    rows = run_benchmark(config)
    write_csv(rows, Path(args.out_csv))
    write_summary(rows, Path(args.summary))


if __name__ == "__main__":
    main()
