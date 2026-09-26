from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


PLANNERS = {
    "DynNavShortest",
    "DynNavHistory",
    "DynNavRobustHistory",
}

EXPECTED_ROUTE = {
    "DynNavShortest": ("upper_direct", (True, True)),
    "DynNavHistory": ("upper_direct", (True, True)),
    "DynNavRobustHistory": ("lower_detour", (False, False)),
}


def validate_confirmatory_slice(
    payload: dict[str, object],
    *,
    dependence: str,
    repetitions: int,
    minimum_paired_valid: int,
) -> dict[str, object]:
    if repetitions <= 0:
        raise ValueError("repetitions must be positive")
    if not 0 <= minimum_paired_valid <= repetitions:
        raise ValueError("minimum_paired_valid must be in [0, repetitions]")

    if payload.get("schema_version") != 1:
        raise ValueError("unexpected schema_version")
    if payload.get("benchmark_type") != "correlated_action_triggered_history":
        raise ValueError("unexpected benchmark_type")
    if payload.get("dependence_conditions") != [dependence]:
        raise ValueError("artifact does not contain the requested dependence slice")

    trials = payload.get("trials")
    if not isinstance(trials, list):
        raise ValueError("trials must be a list")
    if len(trials) != repetitions * len(PLANNERS):
        raise ValueError("unexpected trial count")

    by_repetition: dict[int, list[dict[str, object]]] = defaultdict(list)
    route_violations: list[dict[str, object]] = []
    invalid_reasons: Counter[str] = Counter()
    planner_valid: Counter[str] = Counter()

    for raw in trials:
        if not isinstance(raw, dict):
            raise ValueError("trial rows must be mappings")
        planner = raw.get("planner_id")
        if planner not in PLANNERS:
            raise ValueError(f"unexpected planner: {planner}")
        if raw.get("dependence") != dependence:
            raise ValueError("mixed dependence conditions in one slice")
        repetition = int(raw["repetition"])
        if not 0 <= repetition < repetitions:
            raise ValueError("repetition index out of range")
        by_repetition[repetition].append(raw)

        initial = raw.get("initial_plan")
        if not isinstance(initial, dict) or not initial.get("success"):
            route_violations.append(
                {
                    "repetition": repetition,
                    "planner": planner,
                    "reason": "initial_plan_failed",
                }
            )
        else:
            expected_route, expected_gates = EXPECTED_ROUTE[str(planner)]
            actual_route = initial.get("route_class")
            actual_gates = tuple(bool(value) for value in initial.get("trigger_gate_crossings", []))
            if actual_route != expected_route or actual_gates != expected_gates:
                route_violations.append(
                    {
                        "repetition": repetition,
                        "planner": planner,
                        "reason": "route_mismatch",
                        "actual_route": actual_route,
                        "actual_gates": list(actual_gates),
                        "expected_route": expected_route,
                        "expected_gates": list(expected_gates),
                    }
                )

        if bool(raw.get("valid_trial")):
            planner_valid[str(planner)] += 1
        else:
            invalid_reasons[str(raw.get("invalid_reason") or "unspecified")] += 1

    if set(by_repetition) != set(range(repetitions)):
        raise ValueError("missing repetition(s)")

    paired_history_robust = 0
    paired_shortest_history = 0
    latent_counts: Counter[str] = Counter()
    for repetition, rows in sorted(by_repetition.items()):
        planners = {str(row["planner_id"]) for row in rows}
        if planners != PLANNERS:
            raise ValueError(f"incomplete planner block at repetition {repetition}")
        latent = {tuple(bool(value) for value in row["latent_closures"]) for row in rows}
        if len(latent) != 1:
            raise ValueError(f"latent closure pairing failed at repetition {repetition}")
        latent_pair = next(iter(latent))
        latent_counts[f"{int(latent_pair[0])}{int(latent_pair[1])}"] += 1

        by_planner = {str(row["planner_id"]): row for row in rows}
        paired_history_robust += int(
            bool(by_planner["DynNavHistory"]["valid_trial"])
            and bool(by_planner["DynNavRobustHistory"]["valid_trial"])
        )
        paired_shortest_history += int(
            bool(by_planner["DynNavShortest"]["valid_trial"])
            and bool(by_planner["DynNavHistory"]["valid_trial"])
        )

    summary = {
        "dependence": dependence,
        "repetitions": repetitions,
        "attempted_trials": len(trials),
        "route_audit_passed": not route_violations,
        "route_violations": route_violations,
        "valid_trials_by_planner": {
            planner: planner_valid[planner]
            for planner in sorted(PLANNERS)
        },
        "invalid_reasons": dict(sorted(invalid_reasons.items())),
        "paired_valid_history_robust": paired_history_robust,
        "paired_valid_shortest_history": paired_shortest_history,
        "minimum_paired_valid_required": minimum_paired_valid,
        "execution_inference_complete": (
            not route_violations
            and paired_history_robust >= minimum_paired_valid
        ),
        "latent_outcome_counts": dict(sorted(latent_counts.items())),
    }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--dependence", required=True)
    parser.add_argument("--repetitions", type=int, default=10)
    parser.add_argument("--minimum-paired-valid", type=int, default=8)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    summary = validate_confirmatory_slice(
        payload,
        dependence=args.dependence,
        repetitions=args.repetitions,
        minimum_paired_valid=args.minimum_paired_valid,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))

    if not summary["route_audit_passed"]:
        raise SystemExit(2)
    if not summary["execution_inference_complete"]:
        raise SystemExit(3)


if __name__ == "__main__":
    main()
