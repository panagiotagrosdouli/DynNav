"""Resource feasibility benchmark for Contribution 06.

This benchmark evaluates candidate routes under battery and communication
constraints. It complements the existing grid-planning demo by making mission
verdicts explicit: direct feasible, needs recharge, needs relay, or infeasible.

Run from the repository root:

    python contributions/06_energy_connectivity/experiments/eval_resource_feasibility.py

Output:

    contributions/06_energy_connectivity/results/c06_resource_feasibility.csv
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

from resource_feasibility import (  # noqa: E402
    CandidateRoute,
    ResourceConfig,
    choose_best_feasible,
    classify_route,
)

RESULTS_DIR = Path("contributions/06_energy_connectivity/results")
DEFAULT_OUT = RESULTS_DIR / "c06_resource_feasibility.csv"


def candidate_routes() -> list[CandidateRoute]:
    return [
        CandidateRoute("short_low_link", distance=11.0, min_connectivity=0.20, mean_connectivity=0.55),
        CandidateRoute("long_high_link", distance=25.0, min_connectivity=0.78, mean_connectivity=0.88),
        CandidateRoute("via_recharge", distance=34.0, min_connectivity=0.70, mean_connectivity=0.82, via_recharge=True),
        CandidateRoute("via_relay", distance=18.0, min_connectivity=0.25, mean_connectivity=0.70, via_relay=True),
        CandidateRoute("via_recharge_and_relay", distance=38.0, min_connectivity=0.22, mean_connectivity=0.68, via_recharge=True, via_relay=True),
    ]


def write_csv(path: Path, rows: list[dict[str, float | bool | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="C06 resource-feasibility benchmark.")
    parser.add_argument("--battery-budget", type=float, default=26.0)
    parser.add_argument("--reserve-energy", type=float, default=2.0)
    parser.add_argument("--min-connectivity", type=float, default=0.35)
    parser.add_argument("--energy-per-meter", type=float, default=1.0)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    cfg = ResourceConfig(
        battery_budget=args.battery_budget,
        reserve_energy=args.reserve_energy,
        min_connectivity=args.min_connectivity,
        energy_per_meter=args.energy_per_meter,
    )

    reports = [classify_route(route, cfg) for route in candidate_routes()]
    best = choose_best_feasible(reports)

    rows = []
    for report in reports:
        row = report.to_dict()
        row["selected_best"] = best is not None and report.route_name == best.route_name
        rows.append(row)

    write_csv(args.out, rows)
    print(f"Saved C06 resource feasibility benchmark to {args.out}")
    for row in rows:
        marker = "*" if row["selected_best"] else " "
        print(
            f"{marker} {row['route_name']}: verdict={row['verdict']}, "
            f"energy_margin={float(row['energy_margin']):.2f}, "
            f"connectivity_margin={float(row['connectivity_margin']):.2f}"
        )


if __name__ == "__main__":
    main()
