"""Run paired planners across randomized topology families."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from benchmark import choose_route, evaluate_route
from topology_families import TopologyConfig, available_families, generate_topology

PLANNERS = ("shortest", "risk_only", "safe_return", "recoverability_aware")


def run_trial(family: str, seed: int) -> list[dict[str, float | int | bool | str]]:
    config = TopologyConfig(family=family)
    scenario = generate_topology(seed, config)
    fragile = evaluate_route(scenario, "fragile", scenario.fragile_route)
    resilient = evaluate_route(scenario, "resilient", scenario.resilient_route)

    rows: list[dict[str, float | int | bool | str]] = []
    for planner in PLANNERS:
        selected = choose_route(planner, fragile, resilient)
        rows.append({"family": family, "seed": seed, "planner": planner, **selected})
    return rows


def run_experiment(
    families: tuple[str, ...],
    seeds: int,
) -> list[dict[str, float | int | bool | str]]:
    if seeds <= 0:
        raise ValueError("seeds must be positive")
    return [
        row
        for family in families
        for seed in range(seeds)
        for row in run_trial(family, seed)
    ]


def write_csv(rows: list[dict[str, float | int | bool | str]], output: Path) -> None:
    if not rows:
        raise ValueError("cannot export an empty experiment")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=100)
    parser.add_argument(
        "--families",
        nargs="+",
        choices=available_families(),
        default=list(available_families()),
    )
    parser.add_argument("--output", type=Path, default=Path("random_topology_results.csv"))
    args = parser.parse_args()

    rows = run_experiment(tuple(args.families), args.seeds)
    write_csv(rows, args.output)
    print(
        f"wrote {len(rows)} rows: {len(args.families)} families x "
        f"{args.seeds} seeds x {len(PLANNERS)} planners"
    )


if __name__ == "__main__":
    main()
