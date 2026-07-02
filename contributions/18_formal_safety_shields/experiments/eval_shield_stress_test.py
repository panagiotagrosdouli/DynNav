"""Safety-shield stress-test benchmark for Contribution 18.

This experiment compares shielded and unshielded execution under obstacle-rich
scenarios. It reports violation counts, minimum distance, STL robustness,
correction effort, and path efficiency.

Run from the repository root:

    python contributions/18_formal_safety_shields/experiments/eval_shield_stress_test.py

Output:

    contributions/18_formal_safety_shields/results/c18_shield_stress_test.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[1]
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

from shield_evaluator import benchmark_scenarios, rollout_to_goal  # noqa: E402

RESULTS_DIR = Path("contributions/18_formal_safety_shields/results")
DEFAULT_OUT = RESULTS_DIR / "c18_shield_stress_test.csv"


def write_csv(path: Path, rows: list[dict[str, float | int | bool | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="C18 formal safety-shield stress test.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    rows: list[dict[str, float | int | bool | str]] = []
    for scenario, cfg in benchmark_scenarios().items():
        for shielded in [False, True]:
            result = rollout_to_goal(
                scenario=scenario,
                shielded=shielded,
                start=cfg["start"],
                goal=cfg["goal"],
                obstacles=cfg["obstacles"],
            )
            rows.append(result.to_dict())

    write_csv(args.out, rows)
    print(f"Saved C18 safety-shield stress test to {args.out}")
    for row in rows:
        print(
            f"{row['scenario']:<24} shielded={row['shielded']} "
            f"violations={row['safety_violations']} min_dist={float(row['min_obstacle_distance']):.3f} "
            f"correction={float(row['mean_correction_norm']):.4f} final_goal={float(row['final_goal_distance']):.3f}"
        )


if __name__ == "__main__":
    main()
