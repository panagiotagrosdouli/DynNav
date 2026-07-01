"""Risk trade-off benchmark for Contribution 03.

This experiment creates a small family of candidate paths and evaluates them
under expected risk, maximum risk, and CVaR. It is intentionally lightweight and
self-contained so the scientific point can be audited without ROS or external
assets.

Run from the repository root:

    python contributions/03_belief_risk_planning/experiments/eval_risk_tradeoff.py

Output:

    contributions/03_belief_risk_planning/results/c03_risk_tradeoff_benchmark.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np

MODULE_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = MODULE_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from risk_tradeoff_analyzer import (  # noqa: E402
    evaluate_plan,
    mark_pareto_dominated,
    path_length_increase,
    relative_improvement,
)

RESULTS_DIR = Path("contributions/03_belief_risk_planning/results")
DEFAULT_OUT = RESULTS_DIR / "c03_risk_tradeoff_benchmark.csv"


def synthetic_candidate_paths() -> list[tuple[str, float, np.ndarray]]:
    """Return candidate plans as (name, path_length, per-step risk samples)."""
    return [
        (
            "short_risky_corridor",
            44.0,
            np.array([0.05, 0.08, 0.10, 0.14, 0.18, 0.22, 0.75, 0.82, 0.20, 0.12]),
        ),
        (
            "medium_balanced_route",
            49.0,
            np.array([0.08, 0.09, 0.12, 0.16, 0.18, 0.19, 0.22, 0.25, 0.20, 0.15]),
        ),
        (
            "long_safe_route",
            58.0,
            np.array([0.03, 0.04, 0.05, 0.06, 0.07, 0.07, 0.08, 0.08, 0.06, 0.05]),
        ),
        (
            "detour_with_single_hotspot",
            53.0,
            np.array([0.04, 0.05, 0.05, 0.06, 0.07, 0.55, 0.06, 0.05, 0.04, 0.04]),
        ),
    ]


def select_plan_for_lambda(paths: list[tuple[str, float, np.ndarray]], lambda_value: float, alpha: float, objective_risk: str):
    scored = [
        evaluate_plan(name, lambda_value, length, risks, alpha=alpha, objective_risk=objective_risk)
        for name, length, risks in paths
    ]
    return min(scored, key=lambda p: p.total_objective)


def write_csv(path: Path, rows: list[dict[str, float | int | str | bool]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="C03 risk trade-off benchmark.")
    parser.add_argument("--alpha", type=float, default=0.95)
    parser.add_argument("--objective-risk", choices=["expected", "cvar", "max"], default="cvar")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    lambdas = [0.0, 0.1, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 12.0]
    paths = synthetic_candidate_paths()

    selected = [select_plan_for_lambda(paths, lam, args.alpha, args.objective_risk) for lam in lambdas]
    selected = mark_pareto_dominated(selected, risk_field="cvar_risk")

    baseline = selected[0]
    rows: list[dict[str, float | int | str | bool]] = []
    for plan in selected:
        row = plan.to_dict()
        row["risk_reduction_vs_lambda0_pct"] = relative_improvement(baseline.cvar_risk, plan.cvar_risk)
        row["path_length_increase_vs_lambda0_pct"] = path_length_increase(baseline.path_length, plan.path_length)
        row["objective_risk"] = args.objective_risk
        row["alpha"] = args.alpha
        rows.append(row)

    write_csv(args.out, rows)
    print(f"Saved C03 risk trade-off benchmark to {args.out}")
    for row in rows:
        print(
            f"lambda={float(row['lambda_value']):>4.2f} -> {row['method']}: "
            f"length={float(row['path_length']):.1f}, "
            f"CVaR={float(row['cvar_risk']):.3f}, "
            f"risk_reduction={float(row['risk_reduction_vs_lambda0_pct']):.1f}%, "
            f"length_increase={float(row['path_length_increase_vs_lambda0_pct']):.1f}%, "
            f"dominated={row['dominated']}"
        )


if __name__ == "__main__":
    main()
