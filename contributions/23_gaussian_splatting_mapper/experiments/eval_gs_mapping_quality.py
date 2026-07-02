"""Gaussian-splatting mapping quality benchmark for Contribution 23.

This benchmark evaluates projected occupancy, uncertainty usefulness, frontier
quality, and Gaussian efficiency on synthetic room mapping scenarios.

Run from the repository root:

    python contributions/23_gaussian_splatting_mapper/experiments/eval_gs_mapping_quality.py

Output:

    contributions/23_gaussian_splatting_mapper/results/c23_gs_mapping_quality.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[1]
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

from gs_mapping_evaluator import evaluate_gaussian_map  # noqa: E402

RESULTS_DIR = Path("contributions/23_gaussian_splatting_mapper/results")
DEFAULT_OUT = RESULTS_DIR / "c23_gs_mapping_quality.csv"


def write_csv(path: Path, rows: list[dict[str, float | int | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="C23 Gaussian-splatting mapping quality benchmark.")
    parser.add_argument("--frames", type=int, default=10)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    results = [
        evaluate_gaussian_map("empty_room", n_frames=args.frames, clutter=False),
        evaluate_gaussian_map("cluttered_room", n_frames=args.frames, clutter=True),
    ]
    rows = [r.to_dict() for r in results]
    write_csv(args.out, rows)

    print(f"Saved C23 Gaussian mapping benchmark to {args.out}")
    for row in rows:
        print(
            f"{row['scenario']:<14} iou={float(row['occupancy_iou']):.3f} "
            f"precision={float(row['occupancy_precision']):.3f} recall={float(row['occupancy_recall']):.3f} "
            f"frontiers={row['frontier_count']} gaussians={row['n_gaussians']}"
        )


if __name__ == "__main__":
    main()
