"""Adversarial attack impact benchmark for Contribution 25.

This benchmark evaluates attack impact and simple detection quality for gradient,
LiDAR, and odometry attacks.

Run from the repository root:

    python contributions/25_adversarial_attack_simulator/experiments/eval_attack_impact.py

Output:

    contributions/25_adversarial_attack_simulator/results/c25_attack_impact.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[1]
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

from adversarial_attacks import AttackConfig  # noqa: E402
from attack_impact_evaluator import (  # noqa: E402
    evaluate_gradient_attack,
    evaluate_lidar_attack,
    evaluate_odometry_attack,
    summarize_detection,
)

RESULTS_DIR = Path("contributions/25_adversarial_attack_simulator/results")
DEFAULT_OUT = RESULTS_DIR / "c25_attack_impact.csv"


def write_csv(path: Path, rows: list[dict[str, float | bool | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="C25 adversarial attack impact benchmark.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    cfg = AttackConfig(epsilon=0.12, pgd_steps=8, pgd_step_size=0.025, lidar_n_phantoms=8, lidar_remove_frac=0.25, odom_drift_rate=0.025)
    results = [
        evaluate_gradient_attack("fgsm", cfg),
        evaluate_gradient_attack("pgd", cfg),
        evaluate_lidar_attack("lidar_spoof_add", cfg),
        evaluate_lidar_attack("lidar_spoof_remove", cfg),
        evaluate_lidar_attack("sensor_blind", cfg),
        evaluate_odometry_attack(cfg),
    ]
    rows = [r.to_dict() for r in results]
    write_csv(args.out, rows)
    summary = summarize_detection(results)

    print(f"Saved C25 attack impact benchmark to {args.out}")
    print(
        f"precision={float(summary['detection_precision']):.3f}, "
        f"recall={float(summary['detection_recall']):.3f}, "
        f"f1={float(summary['detection_f1']):.3f}, "
        f"mean_severity={float(summary['mean_severity']):.3f}"
    )
    for row in rows:
        print(
            f"{row['attack_name']:<20} detected={row['detected']} severity={float(row['severity_score']):.3f} "
            f"geom={float(row['geometry_change']):.3f} odom={float(row['odometry_error_m']):.3f} mitigation={row['mitigation']}"
        )


if __name__ == "__main__":
    main()
