"""Returnability-aware NBV benchmark for Contribution 07.

This benchmark compares classic IG/cost next-best-view selection with a safer
viewpoint score that also accounts for path risk, returnability, and connectivity.

Run from the repository root:

    python contributions/07_next_best_view/experiments/eval_returnability_aware_nbv.py

Output:

    contributions/07_next_best_view/results/c07_returnability_aware_nbv.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = MODULE_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from nbv_scoring import NBVWeights, ViewCandidate, score_candidates  # noqa: E402

RESULTS_DIR = Path("contributions/07_next_best_view/results")
DEFAULT_OUT = RESULTS_DIR / "c07_returnability_aware_nbv.csv"


def candidates() -> list[ViewCandidate]:
    return [
        ViewCandidate("near_low_gain", information_gain=18.0, travel_cost=5.0, path_risk=0.10, returnability=0.90, connectivity=0.90),
        ViewCandidate("far_high_gain", information_gain=42.0, travel_cost=9.0, path_risk=0.55, returnability=0.35, connectivity=0.50),
        ViewCandidate("bottleneck_frontier", information_gain=36.0, travel_cost=6.5, path_risk=0.70, returnability=0.20, connectivity=0.40),
        ViewCandidate("balanced_safe_frontier", information_gain=31.0, travel_cost=7.0, path_risk=0.25, returnability=0.82, connectivity=0.80),
        ViewCandidate("relay_supported_frontier", information_gain=28.0, travel_cost=7.5, path_risk=0.22, returnability=0.76, connectivity=0.98),
    ]


def write_csv(path: Path, rows: list[dict[str, float | bool | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="C07 returnability-aware NBV benchmark.")
    parser.add_argument("--risk-weight", type=float, default=1.0)
    parser.add_argument("--returnability-weight", type=float, default=1.0)
    parser.add_argument("--connectivity-weight", type=float, default=0.25)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    weights = NBVWeights(
        risk_weight=args.risk_weight,
        returnability_weight=args.returnability_weight,
        connectivity_weight=args.connectivity_weight,
    )
    scores = score_candidates(candidates(), weights=weights)
    rows = [s.to_dict() for s in scores]
    write_csv(args.out, rows)

    print(f"Saved C07 returnability-aware NBV benchmark to {args.out}")
    for row in rows:
        classic = "classic" if row["selected_by_classic"] else "       "
        safe = "safe" if row["selected_by_safe"] else "    "
        print(
            f"{row['name']:<26} classic={float(row['classic_score']):.3f} "
            f"safe={float(row['safe_score']):.3f} {classic} {safe}"
        )


if __name__ == "__main__":
    main()
