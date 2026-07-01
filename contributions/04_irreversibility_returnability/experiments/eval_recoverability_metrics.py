"""Recoverability benchmark for Contribution 04.

This experiment evaluates a few candidate routes through a small grid world and
reports recoverability/irreversibility metrics for each route.

Run from the repository root:

    python contributions/04_irreversibility_returnability/experiments/eval_recoverability_metrics.py

Output:

    contributions/04_irreversibility_returnability/results/c04_recoverability_metrics.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np

MODULE_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = MODULE_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from recoverability_metrics import evaluate_path_recoverability, recoverability_score  # noqa: E402

Node = tuple[int, int]
RESULTS_DIR = Path("contributions/04_irreversibility_returnability/results")
DEFAULT_OUT = RESULTS_DIR / "c04_recoverability_metrics.csv"


def build_world() -> np.ndarray:
    """Create a small map with an open route, a bottleneck, and a cul-de-sac."""
    grid = np.zeros((12, 16), dtype=np.int32)
    grid[0, :] = 1
    grid[-1, :] = 1
    grid[:, 0] = 1
    grid[:, -1] = 1

    # Wall with one narrow passage.
    grid[1:10, 6] = 1
    grid[5, 6] = 0

    # Cul-de-sac pocket on the right.
    grid[2:9, 11] = 1
    grid[2, 8:12] = 1
    grid[8, 8:12] = 1
    grid[5, 11] = 0

    return grid


def candidate_paths() -> dict[str, list[Node]]:
    return {
        "open_left_route": [(1, 5), (2, 5), (3, 5), (4, 5), (5, 5)],
        "through_bottleneck": [(1, 5), (2, 5), (3, 5), (4, 5), (5, 5), (6, 5), (7, 5), (8, 5)],
        "cul_de_sac_commitment": [(7, 5), (8, 5), (9, 5), (10, 5), (11, 5), (10, 5), (9, 5)],
        "right_side_recovery": [(8, 5), (8, 6), (8, 7), (7, 7), (7, 6), (7, 5), (6, 5)],
    }


def write_csv(path: Path, rows: list[dict[str, float | int | bool | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="C04 recoverability metrics benchmark.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    grid = build_world()
    base = (1, 5)

    rows: list[dict[str, float | int | bool | str]] = []
    for name, path in candidate_paths().items():
        path_metrics = evaluate_path_recoverability(grid, path, base)
        terminal = recoverability_score(grid, path[-1], base)
        row = {
            "path_name": name,
            **path_metrics,
            "terminal_node": str(path[-1]),
            "terminal_returnable": terminal.returnable,
            "terminal_recoverability": terminal.recoverability_score,
            "terminal_irreversibility": terminal.irreversibility_score,
            "terminal_escape_options": terminal.escape_options,
        }
        rows.append(row)

    write_csv(args.out, rows)
    print(f"Saved C04 recoverability benchmark to {args.out}")
    for row in rows:
        print(
            f"{row['path_name']}: min_R={float(row['min_recoverability']):.3f}, "
            f"max_I={float(row['max_irreversibility']):.3f}, "
            f"all_returnable={row['all_returnable']}, "
            f"worst_escape_options={row['worst_escape_options']}"
        )


if __name__ == "__main__":
    main()
