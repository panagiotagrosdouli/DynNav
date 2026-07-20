"""Run the Fragile Commitment Benchmark and export paired planner results."""

from __future__ import annotations

import argparse
import csv
import importlib.util
from pathlib import Path
from typing import Any

from scenario import FragileCommitmentScenario, generate_scenario

ROOT = Path(__file__).resolve().parents[2]
METRICS_PATH = ROOT / "contributions/04_irreversibility_returnability/code/recoverability_metrics.py"


def _load_metrics_module() -> Any:
    spec = importlib.util.spec_from_file_location("recoverability_metrics", METRICS_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load recoverability metrics from {METRICS_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


METRICS = _load_metrics_module()


def route_risk(scenario: FragileCommitmentScenario, route: tuple[tuple[int, int], ...]) -> float:
    return float(sum(scenario.risk[y, x] for x, y in route))


def evaluate_route(
    scenario: FragileCommitmentScenario,
    route_name: str,
    route: tuple[tuple[int, int], ...],
) -> dict[str, float | int | bool | str]:
    profile = METRICS.build_path_recoverability_profile(
        scenario.grid,
        route,
        base=scenario.start,
    )
    blocked = scenario.closure in route
    return {
        "route": route_name,
        "path_length": len(route) - 1,
        "route_risk": route_risk(scenario, route),
        "all_returnable": profile.all_returnable,
        "min_recoverability": profile.min_recoverability,
        "mean_recoverability": profile.mean_recoverability,
        "terminal_recoverability": profile.terminal_recoverability,
        "commitment_loss": profile.cumulative_recoverability_loss,
        "maximum_single_step_loss": profile.maximum_single_step_loss,
        "bottleneck_exposure": profile.bottleneck_exposure,
        "fragility_penalty": profile.penalty(),
        "event_blocks_route": blocked,
        "mission_success": not blocked,
    }


def choose_route(
    planner: str,
    fragile: dict[str, float | int | bool | str],
    resilient: dict[str, float | int | bool | str],
) -> dict[str, float | int | bool | str]:
    candidates = (fragile, resilient)
    if planner == "shortest":
        key = lambda row: (float(row["path_length"]), float(row["route_risk"]))
    elif planner == "risk_only":
        key = lambda row: (float(row["route_risk"]), float(row["path_length"]))
    elif planner == "safe_return":
        key = lambda row: (not bool(row["all_returnable"]), float(row["path_length"]))
    elif planner == "recoverability_aware":
        key = lambda row: (
            float(row["path_length"]) + 20.0 * float(row["fragility_penalty"]),
            float(row["route_risk"]),
        )
    else:
        raise ValueError(f"unknown planner: {planner}")
    return min(candidates, key=key)


def run_seed(seed: int) -> list[dict[str, float | int | bool | str]]:
    scenario = generate_scenario(seed)
    fragile = evaluate_route(scenario, "fragile", scenario.fragile_route)
    resilient = evaluate_route(scenario, "resilient", scenario.resilient_route)

    rows: list[dict[str, float | int | bool | str]] = []
    for planner in ("shortest", "risk_only", "safe_return", "recoverability_aware"):
        selected = choose_route(planner, fragile, resilient)
        rows.append({"seed": seed, "planner": planner, **selected})
    return rows


def write_csv(rows: list[dict[str, float | int | bool | str]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=100)
    parser.add_argument("--output", type=Path, default=Path("fragile_commitment_results.csv"))
    args = parser.parse_args()
    if args.seeds <= 0:
        parser.error("--seeds must be positive")

    rows = [row for seed in range(args.seeds) for row in run_seed(seed)]
    write_csv(rows, args.output)
    successes = sum(bool(row["mission_success"]) for row in rows)
    print(f"wrote {len(rows)} paired planner rows to {args.output}")
    print(f"mission success: {successes}/{len(rows)}")


if __name__ == "__main__":
    main()
