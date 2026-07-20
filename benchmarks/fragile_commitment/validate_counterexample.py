"""Validate that the controlled benchmark exhibits the intended counterexample."""

from __future__ import annotations

import argparse
from dataclasses import dataclass

from benchmark import evaluate_route
from scenario import generate_scenario


@dataclass(frozen=True)
class ValidationThresholds:
    max_relative_risk_gap: float = 0.20
    min_recoverability_gap: float = 0.08
    min_fragility_gap: float = 0.10


def relative_gap(a: float, b: float) -> float:
    scale = max(abs(a), abs(b), 1e-12)
    return abs(a - b) / scale


def validate_seed(seed: int, thresholds: ValidationThresholds) -> list[str]:
    scenario = generate_scenario(seed)
    fragile = evaluate_route(scenario, "fragile", scenario.fragile_route)
    resilient = evaluate_route(scenario, "resilient", scenario.resilient_route)

    errors: list[str] = []
    fragile_risk = float(fragile["route_risk"])
    resilient_risk = float(resilient["route_risk"])
    risk_gap = relative_gap(fragile_risk, resilient_risk)
    if risk_gap > thresholds.max_relative_risk_gap:
        errors.append(
            f"risk gap {risk_gap:.3f} exceeds {thresholds.max_relative_risk_gap:.3f}"
        )

    recoverability_gap = float(resilient["min_recoverability"]) - float(
        fragile["min_recoverability"]
    )
    if recoverability_gap < thresholds.min_recoverability_gap:
        errors.append(
            "recoverability gap "
            f"{recoverability_gap:.3f} is below {thresholds.min_recoverability_gap:.3f}"
        )

    fragility_gap = float(fragile["fragility_penalty"]) - float(
        resilient["fragility_penalty"]
    )
    if fragility_gap < thresholds.min_fragility_gap:
        errors.append(
            f"fragility gap {fragility_gap:.3f} is below {thresholds.min_fragility_gap:.3f}"
        )

    if not bool(fragile["event_blocks_route"]):
        errors.append("dynamic event does not block the fragile route")
    if bool(resilient["event_blocks_route"]):
        errors.append("dynamic event unexpectedly blocks the resilient route")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=100)
    parser.add_argument("--max-relative-risk-gap", type=float, default=0.20)
    parser.add_argument("--min-recoverability-gap", type=float, default=0.08)
    parser.add_argument("--min-fragility-gap", type=float, default=0.10)
    args = parser.parse_args()
    if args.seeds <= 0:
        parser.error("--seeds must be positive")

    thresholds = ValidationThresholds(
        max_relative_risk_gap=args.max_relative_risk_gap,
        min_recoverability_gap=args.min_recoverability_gap,
        min_fragility_gap=args.min_fragility_gap,
    )

    failures: list[str] = []
    for seed in range(args.seeds):
        for error in validate_seed(seed, thresholds):
            failures.append(f"seed {seed}: {error}")

    if failures:
        preview = "\n".join(failures[:20])
        remaining = len(failures) - min(len(failures), 20)
        suffix = f"\n... and {remaining} more" if remaining else ""
        raise SystemExit(f"counterexample validation failed:\n{preview}{suffix}")

    print(f"validated intended counterexample across {args.seeds} seeds")


if __name__ == "__main__":
    main()
