"""Predeclared paired analysis for the canonical G1 Gazebo V2 experiment."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any

from dynnav.experiments.statistics import paired_binary_effect, paired_effect

PLANNERS = ("DynNavShortest", "DynNavHistory", "DynNavRobustHistory")
DEPENDENCE_CONDITIONS = ("independent", "common_cause", "anti_correlated")


def _both_triggers(row: dict[str, Any]) -> bool:
    hazards = row.get("hazards", [])
    return len(hazards) == 2 and all(bool(item["trigger_observed"]) for item in hazards)


def _index_valid_pairs(data: dict[str, Any]) -> dict[tuple[str, int, str], dict[str, Any]]:
    index: dict[tuple[str, int, str], dict[str, Any]] = {}
    for row in data["trials"]:
        if not row.get("valid_trial", False):
            continue
        key = (str(row["dependence"]), int(row["repetition"]), str(row["planner_id"]))
        if key in index:
            raise ValueError(f"duplicate valid trial key: {key}")
        index[key] = row
    return index


def _paired_rows(
    index: dict[tuple[str, int, str], dict[str, Any]],
    dependence: str,
    baseline: str,
    proposed: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    repetitions = sorted(
        repetition
        for condition, repetition, planner in index
        if condition == dependence and planner == baseline
        and (dependence, repetition, proposed) in index
    )
    return (
        [index[(dependence, repetition, baseline)] for repetition in repetitions],
        [index[(dependence, repetition, proposed)] for repetition in repetitions],
    )


def analyze_g1_gazebo_v2(
    data: dict[str, Any],
    *,
    bootstrap_resamples: int = 5000,
    seed: int = 20260925,
) -> dict[str, Any]:
    """Analyze paired valid trials without changing efficacy denominators."""

    if data.get("schema_version") != 1:
        raise ValueError("unsupported G1 Gazebo result schema")
    if data.get("benchmark_type") != "correlated_action_triggered_history":
        raise ValueError("wrong benchmark type")
    index = _index_valid_pairs(data)

    result: dict[str, Any] = {
        "analysis": {
            "paired_by": ["dependence", "repetition"],
            "bootstrap_resamples": bootstrap_resamples,
            "seed": seed,
            "binary_difference_direction": "proposed_minus_baseline",
            "time_difference_direction": "proposed_minus_baseline_seconds",
        },
        "conditions": {},
    }

    for condition_index, dependence in enumerate(DEPENDENCE_CONDITIONS):
        condition: dict[str, Any] = {"descriptive": {}, "paired_effects": {}}
        for planner in PLANNERS:
            all_rows = [
                row
                for row in data["trials"]
                if str(row["dependence"]) == dependence
                and str(row["planner_id"]) == planner
            ]
            rows = [row for row in all_rows if row.get("valid_trial", False)]
            times = [
                float(row["navigation_time_s"])
                for row in rows
                if row.get("navigation_time_s") is not None
            ]
            invalid_reasons = Counter(
                str(row.get("invalid_reason") or "unspecified")
                for row in all_rows
                if not row.get("valid_trial", False)
            )
            initial_plans = [
                row["initial_plan"]
                for row in all_rows
                if isinstance(row.get("initial_plan"), dict)
                and row["initial_plan"].get("success", False)
            ]
            initial_lengths = [
                float(plan["path_length_m"])
                for plan in initial_plans
                if plan.get("path_length_m") is not None
            ]
            initial_routes = sorted(
                {str(plan["route_class"]) for plan in initial_plans}
            )
            initial_gate_patterns = sorted(
                {
                    tuple(bool(value) for value in plan["trigger_gate_crossings"])
                    for plan in initial_plans
                }
            )
            condition["descriptive"][planner] = {
                "total_trials": len(all_rows),
                "valid_trials": len(rows),
                "valid_trial_rate": (
                    len(rows) / len(all_rows) if all_rows else None
                ),
                "invalid_reasons": dict(sorted(invalid_reasons.items())),
                "both_trigger_rate": (
                    sum(_both_triggers(row) for row in rows) / len(rows)
                    if rows else None
                ),
                "irreversible_failure_rate": (
                    sum(bool(row["operational_irreversible_failure"]) for row in rows)
                    / len(rows)
                    if rows else None
                ),
                "return_infeasibility_rate": (
                    sum(row.get("recovery_feasible") is False for row in rows)
                    / len(rows)
                    if rows else None
                ),
                "navigation_success_rate": (
                    sum(bool(row["navigation_success"]) for row in rows) / len(rows)
                    if rows else None
                ),
                "mean_navigation_time_s": (
                    sum(times) / len(times) if times else None
                ),
                "initial_plan": {
                    "successful_audits": len(initial_plans),
                    "route_classes": initial_routes,
                    "trigger_gate_crossing_patterns": [
                        list(pattern) for pattern in initial_gate_patterns
                    ],
                    "mean_path_length_m": (
                        sum(initial_lengths) / len(initial_lengths)
                        if initial_lengths else None
                    ),
                },
            }

        for comparison_index, (baseline, proposed) in enumerate(
            (
                ("DynNavHistory", "DynNavRobustHistory"),
                ("DynNavShortest", "DynNavRobustHistory"),
            )
        ):
            baseline_rows, proposed_rows = _paired_rows(
                index, dependence, baseline, proposed
            )
            if not baseline_rows:
                condition["paired_effects"][f"{proposed}_vs_{baseline}"] = {
                    "paired_valid_trials": 0,
                    "both_trigger_exposure": None,
                    "irreversible_failure": None,
                    "return_infeasibility": None,
                    "navigation_time": None,
                }
                continue

            exposure_effect = paired_binary_effect(
                [_both_triggers(row) for row in baseline_rows],
                [_both_triggers(row) for row in proposed_rows],
                resamples=bootstrap_resamples,
                seed=seed + 100 * condition_index + comparison_index,
            )
            failure_effect = paired_binary_effect(
                [
                    bool(row["operational_irreversible_failure"])
                    for row in baseline_rows
                ],
                [
                    bool(row["operational_irreversible_failure"])
                    for row in proposed_rows
                ],
                resamples=bootstrap_resamples,
                seed=seed + 1000 + 100 * condition_index + comparison_index,
            )
            return_infeasibility_effect = paired_binary_effect(
                [
                    row.get("recovery_feasible") is False
                    for row in baseline_rows
                ],
                [
                    row.get("recovery_feasible") is False
                    for row in proposed_rows
                ],
                resamples=bootstrap_resamples,
                seed=seed + 1500 + 100 * condition_index + comparison_index,
            )

            paired_times = [
                (
                    float(left["navigation_time_s"]),
                    float(right["navigation_time_s"]),
                )
                for left, right in zip(baseline_rows, proposed_rows, strict=True)
                if left.get("navigation_time_s") is not None
                and right.get("navigation_time_s") is not None
            ]
            time_effect = None
            if paired_times:
                time_effect = asdict(
                    paired_effect(
                        [left for left, _ in paired_times],
                        [right for _, right in paired_times],
                        resamples=bootstrap_resamples,
                        seed=seed + 2000 + 100 * condition_index + comparison_index,
                    )
                )

            condition["paired_effects"][f"{proposed}_vs_{baseline}"] = {
                "paired_valid_trials": len(baseline_rows),
                "both_trigger_exposure": asdict(exposure_effect),
                "irreversible_failure": asdict(failure_effect),
                "return_infeasibility": asdict(return_infeasibility_effect),
                "navigation_time": time_effect,
            }

        result["conditions"][dependence] = condition

    return result


def analyze_g1_gazebo_v2_file(
    input_path: str | Path,
    output_path: str | Path,
    *,
    bootstrap_resamples: int = 5000,
    seed: int = 20260925,
) -> dict[str, Any]:
    data = json.loads(Path(input_path).read_text(encoding="utf-8"))
    summary = analyze_g1_gazebo_v2(
        data,
        bootstrap_resamples=bootstrap_resamples,
        seed=seed,
    )
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary
