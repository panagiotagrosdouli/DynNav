"""Predeclared paired analysis for the canonical G1 Gazebo V2 experiment."""

from __future__ import annotations

import json
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
    if not repetitions:
        raise ValueError(
            f"no valid paired trials for {dependence}: {baseline} vs {proposed}"
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
            rows = [
                row
                for (dep, _rep, method), row in index.items()
                if dep == dependence and method == planner
            ]
            times = [
                float(row["navigation_time_s"])
                for row in rows
                if row.get("navigation_time_s") is not None
            ]
            condition["descriptive"][planner] = {
                "valid_trials": len(rows),
                "both_trigger_rate": (
                    sum(_both_triggers(row) for row in rows) / len(rows)
                    if rows else None
                ),
                "irreversible_failure_rate": (
                    sum(bool(row["operational_irreversible_failure"]) for row in rows)
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
