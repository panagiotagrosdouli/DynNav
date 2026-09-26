"""Deterministic aggregation for the G1-G5 full synthetic study."""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev
from typing import Any


def _mean_sd(values: list[float]) -> dict[str, float | int]:
    if not values:
        return {"n": 0, "mean": float("nan"), "sd": float("nan")}
    return {
        "n": len(values),
        "mean": mean(values),
        "sd": stdev(values) if len(values) > 1 else 0.0,
    }


def _group_numeric(
    rows: list[dict[str, Any]],
    *,
    keys: tuple[str, ...],
    metrics: tuple[str, ...],
) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(row[key] for key in keys)].append(row)

    summaries: list[dict[str, Any]] = []
    for group_key, members in sorted(groups.items(), key=lambda item: str(item[0])):
        summary = {key: value for key, value in zip(keys, group_key, strict=True)}
        for metric in metrics:
            values = [
                float(member[metric])
                for member in members
                if metric in member and math.isfinite(float(member[metric]))
            ]
            stats = _mean_sd(values)
            summary[f"{metric}_n"] = stats["n"]
            summary[f"{metric}_mean"] = stats["mean"]
            summary[f"{metric}_sd"] = stats["sd"]
        summaries.append(summary)
    return summaries


def analyze_full_study(study: dict[str, Any]) -> dict[str, Any]:
    """Produce frozen descriptive summaries from full-study rows."""

    g1 = _group_numeric(
        study["G1_dependence_shift_repetitions"],
        keys=("dependence", "planner"),
        metrics=("failure_rate", "path_length", "activated_hazards"),
    )
    g2 = _group_numeric(
        study["G2_activation_grid"],
        keys=(
            "sensor_profile",
            "activation_probability",
            "closure_probability",
            "method",
            "threshold",
        ),
        metrics=("brier_score", "safe_decision_rate", "false_safe_rate"),
    )
    g3 = _group_numeric(
        study["G3_online_learning_grid"],
        keys=(
            "true_closure_probability",
            "minimum_return_probability",
            "policy",
        ),
        metrics=(
            "absolute_error",
            "exposures",
            "return_failures",
            "cumulative_exposure_cost",
        ),
    )
    g4 = _group_numeric(
        study["G4_graph_recovery_grid"],
        keys=("trials_per_pair",),
        metrics=(
            "precision",
            "recall",
            "true_positives",
            "false_positives",
            "false_negatives",
        ),
    )

    g5: list[dict[str, Any]] = []
    for row in study["G5_search_scaling"]:
        raw_nodes = float(row["raw_nodes_expanded"])
        compressed_nodes = float(row["compressed_nodes_expanded"])
        raw_ms = float(row["raw_planning_ms"])
        compressed_ms = float(row["compressed_planning_ms"])
        item = dict(row)
        item["node_reduction_fraction"] = (
            (raw_nodes - compressed_nodes) / raw_nodes if raw_nodes else 0.0
        )
        item["raw_over_compressed_planning_time"] = (
            raw_ms / compressed_ms if compressed_ms > 0.0 else float("inf")
        )
        g5.append(item)

    return {
        "source_metadata": study.get("metadata", {}),
        "analysis_scope": (
            "descriptive frozen aggregation; no deployment or hardware inference"
        ),
        "G1_summary": g1,
        "G2_summary": g2,
        "G3_summary": g3,
        "G4_summary": g4,
        "G5_summary": g5,
    }


def analyze_full_study_file(
    input_path: str | Path,
    output_path: str | Path,
) -> None:
    source = Path(input_path)
    destination = Path(output_path)
    with source.open("r", encoding="utf-8") as handle:
        study = json.load(handle)
    summary = analyze_full_study(study)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
