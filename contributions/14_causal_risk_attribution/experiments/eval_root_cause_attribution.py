"""Root-cause attribution benchmark for Contribution 14.

This benchmark evaluates causal attribution on synthetic navigation failure cases
with known injected root causes. It measures whether the SCM ranking recovers the
true cause and how much the counterfactual intervention reduces collision risk.

Run from the repository root:

    python contributions/14_causal_risk_attribution/experiments/eval_root_cause_attribution.py

Output:

    contributions/14_causal_risk_attribution/results/c14_root_cause_attribution.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[1]
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

from causal_attribution_evaluator import (  # noqa: E402
    AttributionCase,
    evaluate_attribution_case,
    summarize_attribution_results,
)
from causal_risk import NavigationSCM  # noqa: E402

RESULTS_DIR = Path("contributions/14_causal_risk_attribution/results")
DEFAULT_OUT = RESULTS_DIR / "c14_root_cause_attribution.csv"


def cases() -> list[AttributionCase]:
    return [
        AttributionCase(
            name="sensor_noise_failure",
            true_root_cause="sensor_noise",
            observed_noise={"sensor_noise": 1.6, "localization_error": 0.2, "map_accuracy": -0.1},
        ),
        AttributionCase(
            name="localization_drift_failure",
            true_root_cause="localization_error",
            observed_noise={"sensor_noise": 0.4, "localization_error": 1.5, "collision": 0.1},
        ),
        AttributionCase(
            name="map_accuracy_failure",
            true_root_cause="map_accuracy",
            observed_noise={"sensor_noise": 0.5, "map_accuracy": -1.8, "path_risk": 0.1},
            intervention_value=1.0,
        ),
        AttributionCase(
            name="obstacle_detection_failure",
            true_root_cause="obstacle_detection",
            observed_noise={"sensor_noise": 0.6, "obstacle_detection": -1.6, "path_risk": 0.2},
            intervention_value=1.0,
        ),
        AttributionCase(
            name="path_risk_failure",
            true_root_cause="path_risk",
            observed_noise={"sensor_noise": 0.3, "path_risk": 1.4, "collision": 0.1},
        ),
    ]


def write_csv(path: Path, rows: list[dict[str, float | int | bool | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="C14 causal root-cause attribution benchmark.")
    parser.add_argument("--n-samples", type=int, default=200)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    scm = NavigationSCM()
    results = [evaluate_attribution_case(scm, case, n_samples=args.n_samples) for case in cases()]
    rows = [r.to_dict() for r in results]
    summary = summarize_attribution_results(results)
    write_csv(args.out, rows)

    print(f"Saved C14 root-cause attribution benchmark to {args.out}")
    print(
        f"top1_accuracy={float(summary['top1_accuracy']):.3f}, "
        f"mean_true_cause_rank={float(summary['mean_true_cause_rank']):.2f}, "
        f"mean_counterfactual_reduction={float(summary['mean_counterfactual_reduction']):.3f}"
    )
    for row in rows:
        print(
            f"{row['case_name']:<30} true={row['true_root_cause']:<20} "
            f"pred={row['predicted_root_cause']:<20} rank={row['true_cause_rank']} "
            f"reduction={float(row['counterfactual_reduction']):.3f}"
        )


if __name__ == "__main__":
    main()
