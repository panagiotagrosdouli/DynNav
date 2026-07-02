"""NeRF uncertainty benchmark for Contribution 24.

This benchmark evaluates NeRF-derived uncertainty as a navigation signal using
calibration, OOD detection, novel-view uncertainty, exploration priority, and a
planning-safety proxy.

Run from the repository root:

    python contributions/24_nerf_uncertainty/experiments/eval_nerf_uncertainty.py

Output:

    contributions/24_nerf_uncertainty/results/c24_nerf_uncertainty.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[1]
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

from nerf_uncertainty_evaluator import evaluate_nerf_uncertainty_case  # noqa: E402

RESULTS_DIR = Path("contributions/24_nerf_uncertainty/results")
DEFAULT_OUT = RESULTS_DIR / "c24_nerf_uncertainty.csv"


def write_csv(path: Path, rows: list[dict[str, float | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="C24 NeRF uncertainty evaluation benchmark.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    results = [
        evaluate_nerf_uncertainty_case("nominal_scene", seed=24, ood_shift=False),
        evaluate_nerf_uncertainty_case("ood_view_shift", seed=25, ood_shift=True),
    ]
    rows = [r.to_dict() for r in results]
    write_csv(args.out, rows)

    print(f"Saved C24 NeRF uncertainty benchmark to {args.out}")
    for row in rows:
        print(
            f"{row['scenario']:<16} brier={float(row['brier_score']):.3f} "
            f"ece={float(row['ece']):.3f} auroc={float(row['ood_auroc']):.3f} "
            f"explore_p@k={float(row['exploration_precision_at_k']):.3f} "
            f"safety_gain={float(row['planning_safety_gain']):.3f}"
        )


if __name__ == "__main__":
    main()
