"""Pre-registered V4 analysis utilities.

The primary inferential unit is scenario -> paired execution seed. Raw rows are
never treated as independent environments. This module is deliberately
outcome-agnostic and can be frozen before held-out execution.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import asdict, dataclass
from statistics import mean
from typing import Iterable

from dynnav.experiments.statistics import hierarchical_paired_bootstrap_interval


@dataclass(frozen=True)
class V4AnalysisRow:
    scenario: str
    topology_family: str
    seed: int
    planner: str
    observation_regime: str
    path_length: float
    predicted_return_probability: float
    return_feasible: bool
    mission_success: bool
    protocol_valid: bool


@dataclass(frozen=True)
class CalibrationBin:
    lower: float
    upper: float
    count: int
    mean_prediction: float
    empirical_frequency: float


def _brier(row: V4AnalysisRow) -> float:
    if not math.isfinite(row.predicted_return_probability):
        raise ValueError(
            f"non-finite prediction for {row.scenario}/{row.seed}/{row.planner}"
        )
    target = float(row.return_feasible)
    return (row.predicted_return_probability - target) ** 2


def fixed_bin_calibration(
    rows: Iterable[V4AnalysisRow],
    *,
    planner: str,
    observation_regime: str,
) -> tuple[CalibrationBin, ...]:
    selected = [
        row
        for row in rows
        if row.planner == planner
        and row.observation_regime == observation_regime
        and row.protocol_valid
        and row.mission_success
        and math.isfinite(row.predicted_return_probability)
    ]

    bins: list[CalibrationBin] = []
    for index in range(10):
        lower = index / 10.0
        upper = (index + 1) / 10.0
        members = [
            row
            for row in selected
            if (
                lower <= row.predicted_return_probability < upper
                or (
                    index == 9
                    and row.predicted_return_probability == 1.0
                )
            )
        ]
        if not members:
            bins.append(CalibrationBin(lower, upper, 0, float("nan"), float("nan")))
            continue
        bins.append(
            CalibrationBin(
                lower=lower,
                upper=upper,
                count=len(members),
                mean_prediction=mean(
                    row.predicted_return_probability for row in members
                ),
                empirical_frequency=mean(
                    float(row.return_feasible) for row in members
                ),
            )
        )
    return tuple(bins)


def paired_v4_comparison(
    rows: Iterable[V4AnalysisRow],
    *,
    proposed: str,
    baseline: str,
    observation_regime: str,
    resamples: int = 5000,
    seed: int = 2026100304,
    require_all_valid: bool = True,
) -> dict[str, object]:
    """Return scenario-weighted paired effects for one frozen comparison."""

    selected = [
        row
        for row in rows
        if row.observation_regime == observation_regime
        and row.planner in {proposed, baseline}
    ]
    if not selected:
        raise ValueError("no rows match comparison")

    invalid = [row for row in selected if not row.protocol_valid]
    if require_all_valid and invalid:
        raise ValueError(
            f"comparison contains {len(invalid)} protocol-invalid rows"
        )

    selected = [
        row for row in selected if row.protocol_valid and row.mission_success
    ]

    indexed: dict[tuple[str, int, str], V4AnalysisRow] = {}
    for row in selected:
        key = (row.scenario, row.seed, row.planner)
        if key in indexed:
            raise ValueError(f"duplicate paired row: {key}")
        indexed[key] = row

    pairs: list[tuple[V4AnalysisRow, V4AnalysisRow]] = []
    scenario_seed_keys = sorted(
        {
            (scenario, execution_seed)
            for scenario, execution_seed, _ in indexed
        }
    )
    for scenario, execution_seed in scenario_seed_keys:
        baseline_key = (scenario, execution_seed, baseline)
        proposed_key = (scenario, execution_seed, proposed)
        if baseline_key not in indexed or proposed_key not in indexed:
            raise ValueError(
                "incomplete planner pairing for "
                f"{scenario}/{execution_seed}"
            )
        pairs.append((indexed[baseline_key], indexed[proposed_key]))

    risk_by_scenario: dict[str, list[float]] = defaultdict(list)
    brier_by_scenario: dict[str, list[float]] = defaultdict(list)
    path_by_scenario: dict[str, list[float]] = defaultdict(list)
    family_scenario_effects: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for base, prop in pairs:
        if base.topology_family != prop.topology_family:
            raise ValueError("paired rows disagree on topology family")
        risk_difference = float(not prop.return_feasible) - float(
            not base.return_feasible
        )
        brier_difference = _brier(prop) - _brier(base)
        path_difference = prop.path_length - base.path_length

        risk_by_scenario[prop.scenario].append(risk_difference)
        brier_by_scenario[prop.scenario].append(brier_difference)
        path_by_scenario[prop.scenario].append(path_difference)

    for scenario, values in risk_by_scenario.items():
        family = next(
            prop.topology_family
            for base, prop in pairs
            if prop.scenario == scenario
        )
        family_scenario_effects[family]["risk"].append(mean(values))
        family_scenario_effects[family]["brier"].append(
            mean(brier_by_scenario[scenario])
        )
        family_scenario_effects[family]["path"].append(
            mean(path_by_scenario[scenario])
        )

    risk_interval = hierarchical_paired_bootstrap_interval(
        risk_by_scenario,
        resamples=resamples,
        seed=seed,
    )
    brier_interval = hierarchical_paired_bootstrap_interval(
        brier_by_scenario,
        resamples=resamples,
        seed=seed + 1,
    )
    path_interval = hierarchical_paired_bootstrap_interval(
        path_by_scenario,
        resamples=resamples,
        seed=seed + 2,
    )

    by_family: dict[str, dict[str, float]] = {}
    for family, metrics in sorted(family_scenario_effects.items()):
        by_family[family] = {
            "scenario_count": float(len(metrics["risk"])),
            "mean_risk_difference": mean(metrics["risk"]),
            "mean_brier_difference": mean(metrics["brier"]),
            "mean_path_difference": mean(metrics["path"]),
        }

    return {
        "proposed": proposed,
        "baseline": baseline,
        "observation_regime": observation_regime,
        "scenario_count": len(risk_by_scenario),
        "paired_seed_count": len(pairs),
        "invalid_rows": len(invalid),
        "risk_difference": asdict(risk_interval),
        "brier_difference": asdict(brier_interval),
        "path_length_difference": asdict(path_interval),
        "by_family": by_family,
    }
