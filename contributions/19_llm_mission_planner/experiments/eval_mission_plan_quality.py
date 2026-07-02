"""Mission-plan quality benchmark for Contribution 19.

This benchmark evaluates whether natural-language instructions are converted into
ordered, executable, and constraint-aware waypoint plans.

Run from the repository root:

    python contributions/19_llm_mission_planner/experiments/eval_mission_plan_quality.py

Output:

    contributions/19_llm_mission_planner/results/c19_mission_plan_quality.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[1]
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

from llm_mission_planner import LLMPlannerConfig, LLMMissionPlanner  # noqa: E402
from mission_plan_evaluator import MissionPlanExpectation, evaluate_mission_plan, summarize_reports  # noqa: E402

RESULTS_DIR = Path("contributions/19_llm_mission_planner/results")
DEFAULT_OUT = RESULTS_DIR / "c19_mission_plan_quality.csv"

ZONE_MAP = {
    "start": (0.0, 0.0),
    "kitchen": (2.0, 3.0),
    "corridor": (5.0, 1.0),
    "office": (3.0, 5.0),
    "exit": (8.0, 0.0),
    "charging_station": (1.0, -1.0),
    "storage_room": (6.0, 3.0),
    "entrance": (0.0, 1.0),
}


def expectations() -> list[MissionPlanExpectation]:
    return [
        MissionPlanExpectation(
            instruction="go to the kitchen then the corridor and exit",
            expected_labels=("kitchen", "corridor", "exit"),
        ),
        MissionPlanExpectation(
            instruction="inspect the office and then return to the charging station",
            expected_labels=("office", "charging_station"),
            required_labels=("charging_station",),
        ),
        MissionPlanExpectation(
            instruction="start at the entrance, check the storage room, then go to the exit",
            expected_labels=("entrance", "storage_room", "exit"),
        ),
        MissionPlanExpectation(
            instruction="go to the private lab then kitchen",
            expected_labels=("kitchen",),
            forbidden_labels=("private_lab", "restricted_area"),
        ),
        MissionPlanExpectation(
            instruction="go to the corridor corridor and then exit",
            expected_labels=("corridor", "exit"),
        ),
    ]


def write_csv(path: Path, rows: list[dict[str, float | int | bool | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="C19 LLM mission-plan quality benchmark.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    cfg = LLMPlannerConfig(endpoint="http://localhost:9/api/chat")  # force offline fallback deterministically
    planner = LLMMissionPlanner(cfg)
    reports = []
    for exp in expectations():
        mission = planner.parse(exp.instruction)
        mission = planner.resolve_to_metric(mission, ZONE_MAP)
        reports.append(evaluate_mission_plan(mission, exp, ZONE_MAP))

    rows = [r.to_dict() for r in reports]
    write_csv(args.out, rows)
    summary = summarize_reports(reports)
    print(f"Saved C19 mission-plan quality benchmark to {args.out}")
    print(
        f"mean_ordering_accuracy={float(summary['mean_ordering_accuracy']):.3f}, "
        f"exact_match_rate={float(summary['exact_match_rate']):.3f}, "
        f"execution_ready_rate={float(summary['execution_ready_rate']):.3f}"
    )
    for row in rows:
        print(
            f"ready={row['execution_ready']} order={float(row['ordering_accuracy']):.2f} "
            f"pred={row['predicted_sequence']} expected={row['expected_sequence']}"
        )


if __name__ == "__main__":
    main()
