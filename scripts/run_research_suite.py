#!/usr/bin/env python3
"""Run a deterministic DynNav research-suite smoke experiment.

The runner intentionally generates modest, reproducible prototype outputs. It is
not a benchmark-results claim; it is a CI-friendly mechanism for producing
traceable metrics from fixed seeds.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from dynnav.core import GridMap, Pose
from dynnav.lab_grade import PlanningRequest, run_single_research_episode


def make_static_maze() -> GridMap:
    """Return a small deterministic maze-like occupancy grid."""
    grid = np.zeros((8, 8), dtype=float)
    grid[3, 1:7] = 1.0
    grid[3, 4] = 0.0
    grid[5, 0:5] = 1.0
    grid[5, 2] = 0.0
    grid[1, 5] = 0.45
    grid[2, 5] = 0.50
    return GridMap(grid)


def run(out_dir: Path) -> dict[str, object]:
    """Run deterministic smoke experiments and write metrics."""
    out_dir.mkdir(parents=True, exist_ok=True)
    episodes = [
        PlanningRequest(start=Pose(0, 0), goal=Pose(7, 7), occupancy=make_static_maze(), seed=7),
        PlanningRequest(start=Pose(0, 7), goal=Pose(7, 0), occupancy=make_static_maze(), seed=11),
    ]
    rows = [run_single_research_episode(request) for request in episodes]

    metrics_path = out_dir / "metrics.csv"
    with metrics_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "status": "Prototype",
        "claim_policy": "Do not cite as benchmark evidence without independent review.",
        "episodes": len(rows),
        "successes": sum(1 for row in rows if row["path_found"]),
        "metrics_csv": str(metrics_path),
    }
    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=Path("results/research_suite"))
    args = parser.parse_args()
    summary = run(args.out_dir)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
