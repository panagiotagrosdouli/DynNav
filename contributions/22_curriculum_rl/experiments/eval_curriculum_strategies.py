"""Curriculum-strategy benchmark for Contribution 22.

This benchmark compares fixed, adaptive, and reverse curriculum scheduling using
stage progression, success trend, stability, held-out transfer, and a simple
sample-efficiency proxy.

Run from the repository root:

    python contributions/22_curriculum_rl/experiments/eval_curriculum_strategies.py

Output:

    contributions/22_curriculum_rl/results/c22_curriculum_strategies.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[1]
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

from curriculum_evaluator import evaluate_curriculum_strategy  # noqa: E402
from curriculum_rl import CurriculumStrategy  # noqa: E402

RESULTS_DIR = Path("contributions/22_curriculum_rl/results")
DEFAULT_OUT = RESULTS_DIR / "c22_curriculum_strategies.csv"


def write_csv(path: Path, rows: list[dict[str, float | int | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="C22 curriculum strategy benchmark.")
    parser.add_argument("--episodes", type=int, default=300)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    strategies = [CurriculumStrategy.ADAPTIVE, CurriculumStrategy.FIXED, CurriculumStrategy.REVERSE]
    results = [evaluate_curriculum_strategy(s, n_episodes=args.episodes, seed=42) for s in strategies]
    rows = [r.to_dict() for r in results]
    write_csv(args.out, rows)

    print(f"Saved C22 curriculum strategy benchmark to {args.out}")
    for row in rows:
        print(
            f"{row['strategy']:<9} final={row['final_stage']:<8} transitions={row['n_stage_transitions']} "
            f"last_success={float(row['mean_success_last_window']):.3f} "
            f"transfer={float(row['heldout_transfer_success']):.3f} sample_eff={float(row['sample_efficiency_score']):.3f}"
        )


if __name__ == "__main__":
    main()
