"""Federated navigation-learning trade-off benchmark for Contribution 16.

This benchmark compares aggregation and privacy settings using fleet-level
metrics: mean client MSE, fairness gap, communication cost, and server validation
loss.

Run from the repository root:

    python contributions/16_federated_nav_learning/experiments/eval_federated_tradeoffs.py

Output:

    contributions/16_federated_nav_learning/results/c16_federated_tradeoffs.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[1]
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

from federated_evaluator import run_federated_eval  # noqa: E402

RESULTS_DIR = Path("contributions/16_federated_nav_learning/results")
DEFAULT_OUT = RESULTS_DIR / "c16_federated_tradeoffs.csv"


def write_csv(path: Path, rows: list[dict[str, float | int | bool | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="C16 federated learning trade-off benchmark.")
    parser.add_argument("--rounds", type=int, default=8)
    parser.add_argument("--n-clients", type=int, default=6)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    configs = [
        ("weighted_no_dp", "weighted", None),
        ("uniform_no_dp", "uniform", None),
        ("weighted_dp_eps_2", "weighted", 2.0),
        ("weighted_dp_eps_1", "weighted", 1.0),
    ]
    results = [
        run_federated_eval(name, aggregation, dp, n_clients=args.n_clients, rounds=args.rounds)
        for name, aggregation, dp in configs
    ]
    rows = [r.to_dict() for r in results]
    write_csv(args.out, rows)

    print(f"Saved C16 federated trade-off benchmark to {args.out}")
    for row in rows:
        print(
            f"{row['scenario']:<18} mean_mse={float(row['mean_client_mse']):.4f} "
            f"fairness_gap={float(row['fairness_gap']):.4f} "
            f"comm_floats={row['communication_floats']} dp={row['dp_enabled']}"
        )


if __name__ == "__main__":
    main()
