"""Team coordination benchmark for Contribution 09.

This benchmark evaluates multi-robot plans for conflicts, risk-budget violations,
and belief disagreement. It is intentionally small and auditable.

Run from the repository root:

    python contributions/09_multi_robot/experiments/eval_team_coordination.py

Output:

    contributions/09_multi_robot/results/c09_team_coordination.csv
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

from team_coordination_metrics import RobotPlan, summarize_team_coordination  # noqa: E402

RESULTS_DIR = Path("contributions/09_multi_robot/results")
DEFAULT_OUT = RESULTS_DIR / "c09_team_coordination.csv"


def scenarios() -> dict[str, list[RobotPlan]]:
    return {
        "conflicting_paths": [
            RobotPlan("r1", [(0, 0), (1, 0), (2, 0), (3, 0)], risk=0.20, allocated_risk_budget=0.30, belief_hash="A"),
            RobotPlan("r2", [(3, 0), (2, 0), (1, 0), (0, 0)], risk=0.25, allocated_risk_budget=0.30, belief_hash="A"),
            RobotPlan("r3", [(0, 2), (1, 2), (2, 2), (3, 2)], risk=0.15, allocated_risk_budget=0.25, belief_hash="A"),
        ],
        "risk_budget_violation": [
            RobotPlan("r1", [(0, 0), (0, 1), (0, 2)], risk=0.50, allocated_risk_budget=0.30, belief_hash="A"),
            RobotPlan("r2", [(2, 0), (2, 1), (2, 2)], risk=0.20, allocated_risk_budget=0.30, belief_hash="A"),
            RobotPlan("r3", [(4, 0), (4, 1), (4, 2)], risk=0.18, allocated_risk_budget=0.25, belief_hash="A"),
        ],
        "belief_disagreement": [
            RobotPlan("r1", [(0, 0), (1, 0), (2, 0)], risk=0.20, allocated_risk_budget=0.30, belief_hash="A"),
            RobotPlan("r2", [(0, 1), (1, 1), (2, 1)], risk=0.22, allocated_risk_budget=0.30, belief_hash="A"),
            RobotPlan("r3", [(0, 2), (1, 2), (2, 2)], risk=0.19, allocated_risk_budget=0.25, belief_hash="B"),
        ],
        "coordinated_feasible": [
            RobotPlan("r1", [(0, 0), (1, 0), (2, 0), (3, 0)], risk=0.18, allocated_risk_budget=0.30, belief_hash="A"),
            RobotPlan("r2", [(0, 1), (1, 1), (2, 1), (3, 1)], risk=0.22, allocated_risk_budget=0.30, belief_hash="A"),
            RobotPlan("r3", [(0, 2), (1, 2), (2, 2), (3, 2)], risk=0.16, allocated_risk_budget=0.25, belief_hash="A"),
        ],
    }


def write_csv(path: Path, rows: list[dict[str, float | int | bool | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="C09 multi-robot coordination benchmark.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    rows: list[dict[str, float | int | bool | str]] = []
    for name, plans in scenarios().items():
        report = summarize_team_coordination(plans)
        rows.append({"scenario": name, **report.to_dict()})

    write_csv(args.out, rows)
    print(f"Saved C09 team coordination benchmark to {args.out}")
    for row in rows:
        print(
            f"{row['scenario']:<24} feasible={row['feasible']} "
            f"conflicts={row['n_conflicts']} risk_violations={row['risk_budget_violations']} "
            f"belief_disagreements={row['belief_disagreement_count']}"
        )


if __name__ == "__main__":
    main()
