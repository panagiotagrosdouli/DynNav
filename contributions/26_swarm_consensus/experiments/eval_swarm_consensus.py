"""Swarm consensus benchmark for Contribution 26.

This benchmark evaluates Byzantine-fault-tolerant swarm consensus under scaling,
Byzantine faults, silent robots, and packet-loss conditions.

Run from the repository root:

    python contributions/26_swarm_consensus/experiments/eval_swarm_consensus.py

Output:

    contributions/26_swarm_consensus/results/c26_swarm_consensus.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[1]
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

from swarm_consensus_evaluator import (  # noqa: E402
    benchmark_cases,
    evaluate_swarm_consensus_case,
    summarize_swarm_results,
)

RESULTS_DIR = Path("contributions/26_swarm_consensus/results")
DEFAULT_OUT = RESULTS_DIR / "c26_swarm_consensus.csv"


def write_csv(path: Path, rows: list[dict[str, float | int | bool | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="C26 swarm consensus benchmark.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    results = [
        evaluate_swarm_consensus_case(
            scenario=str(case["scenario"]),
            n_robots=int(case["n_robots"]),
            n_byzantine=int(case["n_byzantine"]),
            fault_type=str(case["fault_type"]),
            packet_loss_rate=float(case["packet_loss_rate"]),
        )
        for case in benchmark_cases()
    ]
    rows = [r.to_dict() for r in results]
    write_csv(args.out, rows)
    summary = summarize_swarm_results(results)

    print(f"Saved C26 swarm consensus benchmark to {args.out}")
    print(
        f"success_rate={float(summary['mission_success_rate']):.3f}, "
        f"mean_accuracy={float(summary['mean_consensus_accuracy']):.3f}, "
        f"mean_detection_recall={float(summary['mean_detection_recall']):.3f}, "
        f"mean_messages={float(summary['mean_messages']):.1f}"
    )
    for row in rows:
        print(
            f"{row['scenario']:<20} n={row['n_robots']:<2} byz={row['n_byzantine']:<2} "
            f"participants={row['participants']:<2} acc={float(row['consensus_accuracy']):.3f} "
            f"success={row['mission_success']} method={row['consensus_method']}"
        )


if __name__ == "__main__":
    main()
