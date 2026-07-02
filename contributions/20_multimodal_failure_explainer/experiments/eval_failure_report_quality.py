"""Failure-report quality benchmark for Contribution 20.

This benchmark evaluates generated failure reports using completeness,
root-cause coverage, action relevance, STL coverage, and operator readiness.

Run from the repository root:

    python contributions/20_multimodal_failure_explainer/experiments/eval_failure_report_quality.py

Output:

    contributions/20_multimodal_failure_explainer/results/c20_failure_report_quality.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[1]
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

from failure_report_evaluator import (  # noqa: E402
    FailureExplanationExpectation,
    score_failure_report,
    summarize_scores,
)
from multimodal_failure_explainer import (  # noqa: E402
    FailureEvent,
    FailureType,
    MultimodalFailureExplainer,
)

RESULTS_DIR = Path("contributions/20_multimodal_failure_explainer/results")
DEFAULT_OUT = RESULTS_DIR / "c20_failure_report_quality.csv"


def cases() -> list[tuple[FailureEvent, FailureExplanationExpectation]]:
    return [
        (
            FailureEvent(
                failure_type=FailureType.COLLISION,
                timestamp=12.5,
                robot_pos=(3.2, 4.1),
                robot_vel=(0.3, 0.0),
                sensor_readings={"min_obstacle_dist": 0.15},
                stl_robustness={"always_keep_distance": -0.30},
            ),
            FailureExplanationExpectation(
                case_name="collision_near_obstacle",
                expected_root_causes=("sensor_noise", "localization_error"),
                expected_action_keywords=("safety radius", "velocity", "sensor"),
            ),
        ),
        (
            FailureEvent(
                failure_type=FailureType.SENSOR_FAULT,
                timestamp=8.0,
                robot_pos=(1.0, 2.0),
                robot_vel=(0.0, 0.0),
                sensor_readings={"dropout_rate": 0.7},
                stl_robustness={"sensor_validity": -0.50},
            ),
            FailureExplanationExpectation(
                case_name="sensor_fault",
                expected_root_causes=("sensor_noise",),
                expected_action_keywords=("ids", "dead-reckoning", "neuromorphic"),
            ),
        ),
        (
            FailureEvent(
                failure_type=FailureType.IRREVERSIBLE,
                timestamp=22.0,
                robot_pos=(6.0, 1.5),
                robot_vel=(0.1, -0.2),
                sensor_readings={"returnability": 0.12},
                stl_robustness={"recoverability_margin": -0.40},
            ),
            FailureExplanationExpectation(
                case_name="irreversible_state",
                expected_root_causes=("localization_error",),
                expected_action_keywords=("returnability", "mental rollout", "u-turn"),
            ),
        ),
    ]


def write_csv(path: Path, rows: list[dict[str, float | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="C20 failure-report quality benchmark.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    explainer = MultimodalFailureExplainer(use_vlm=False, use_causal=True)
    rows = []
    scores = []
    for event, expectation in cases():
        report = explainer.explain(event)
        score = score_failure_report(report, expectation)
        scores.append(score)
        rows.append(score.to_dict())

    write_csv(args.out, rows)
    summary = summarize_scores(scores)
    print(f"Saved C20 failure-report quality benchmark to {args.out}")
    print(
        f"mean_total_score={float(summary['mean_total_score']):.3f}, "
        f"mean_root_cause_recall={float(summary['mean_root_cause_recall']):.3f}, "
        f"operator_ready_rate={float(summary['operator_ready_rate']):.3f}"
    )
    for row in rows:
        print(
            f"{row['case_name']:<24} total={float(row['total_score']):.3f} "
            f"root_recall={float(row['root_cause_recall']):.3f} action={float(row['action_relevance']):.3f}"
        )


if __name__ == "__main__":
    main()
