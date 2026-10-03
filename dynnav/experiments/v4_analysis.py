"""Pre-registered V4 analysis utilities.

The primary inferential unit is scenario -> paired execution seed. Raw rows are
never treated as independent environments. Pairing is established before any
conditioning on mission success so asymmetric mission failures cannot disappear
from the analysis.

Return-risk calibration is meaningful only after an outbound evaluation state
exists. Therefore return-infeasibility and Brier effects are reported for the
jointly mission-successful paired subset, while mission failure and a composite
mission-or-return operational failure are reported on every valid pair.
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from statistics import mean

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
    if not row.mission_success:
        raise ValueError("Brier score is undefined without an outbound evaluation state")
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
                or (index == 9 and row.predicted_return_probability == 1.0)
            )
        ]
        if not members:
            bins.append(
                CalibrationBin(
                    lower,
                    upper,
                    0,
                    float("nan"),
                    float("nan"),
                )
            )
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


def _paired_rows(
    rows: Iterable[V4AnalysisRow],
    *,
    proposed: str,
    baseline: str,
    observation_regime: str,
    require_all_valid: bool,
) -> tuple[
    list[tuple[V4AnalysisRow, V4AnalysisRow]],
    int,
]:
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

    valid = [row for row in selected if row.protocol_valid]
    indexed: dict[tuple[str, int, str], V4AnalysisRow] = {}
    for row in valid:
        key = (row.scenario, row.seed, row.planner)
        if key in indexed:
            raise ValueError(f"duplicate paired row: {key}")
        indexed[key] = row

    scenario_seed_keys = sorted(
        {(scenario, seed) for scenario, seed, _ in indexed}
    )
    pairs: list[tuple[V4AnalysisRow, V4AnalysisRow]] = []
    for scenario, execution_seed in scenario_seed_keys:
        baseline_key = (scenario, execution_seed, baseline)
        proposed_key = (scenario, execution_seed, proposed)
        if baseline_key not in indexed or proposed_key not in indexed:
            raise ValueError(
                "incomplete planner pairing for "
                f"{scenario}/{execution_seed}"
            )
        base = indexed[baseline_key]
        prop = indexed[proposed_key]
        if base.topology_family != prop.topology_family:
            raise ValueError("paired rows disagree on topology family")
        pairs.append((base, prop))
    if not pairs:
        raise ValueError("no complete valid planner pairs")
    return pairs, len(invalid)


def _interval_or_none(
    values_by_scenario: dict[str, list[float]],
    *,
    resamples: int,
    seed: int,
) -> dict[str, object] | None:
    if not values_by_scenario:
        return None
    return asdict(
        hierarchical_paired_bootstrap_interval(
            values_by_scenario,
            resamples=resamples,
            seed=seed,
        )
    )


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
    """Return scenario-weighted paired V4 effects.

    Every protocol-valid pair contributes to mission failure and composite
    operational failure. Return-risk, Brier and path-length effects are
    evaluated only when both methods reached the outbound goal, because those
    quantities are otherwise undefined or not comparable at the same endpoint.

    This separation prevents a method from looking safer merely because its
    mission failures were silently removed.
    """

    pairs, invalid_count = _paired_rows(
        rows,
        proposed=proposed,
        baseline=baseline,
        observation_regime=observation_regime,
        require_all_valid=require_all_valid,
    )

    mission_by_scenario: dict[str, list[float]] = defaultdict(list)
    composite_by_scenario: dict[str, list[float]] = defaultdict(list)
    return_risk_by_scenario: dict[str, list[float]] = defaultdict(list)
    brier_by_scenario: dict[str, list[float]] = defaultdict(list)
    path_by_scenario: dict[str, list[float]] = defaultdict(list)

    family_by_scenario: dict[str, str] = {}
    joint_success_pairs = 0
    asymmetric_mission_pairs = 0

    for base, prop in pairs:
        family_by_scenario[prop.scenario] = prop.topology_family

        base_mission_failure = not base.mission_success
        prop_mission_failure = not prop.mission_success
        mission_by_scenario[prop.scenario].append(
            float(prop_mission_failure) - float(base_mission_failure)
        )

        base_operational_failure = (
            (not base.mission_success)
            or (base.mission_success and not base.return_feasible)
        )
        prop_operational_failure = (
            (not prop.mission_success)
            or (prop.mission_success and not prop.return_feasible)
        )
        composite_by_scenario[prop.scenario].append(
            float(prop_operational_failure)
            - float(base_operational_failure)
        )

        if base.mission_success != prop.mission_success:
            asymmetric_mission_pairs += 1

        if not (base.mission_success and prop.mission_success):
            continue

        joint_success_pairs += 1
        return_risk_by_scenario[prop.scenario].append(
            float(not prop.return_feasible) - float(not base.return_feasible)
        )
        brier_by_scenario[prop.scenario].append(_brier(prop) - _brier(base))
        path_by_scenario[prop.scenario].append(
            prop.path_length - base.path_length
        )

    mission_interval = hierarchical_paired_bootstrap_interval(
        mission_by_scenario,
        resamples=resamples,
        seed=seed,
    )
    composite_interval = hierarchical_paired_bootstrap_interval(
        composite_by_scenario,
        resamples=resamples,
        seed=seed + 1,
    )

    risk_interval = _interval_or_none(
        return_risk_by_scenario,
        resamples=resamples,
        seed=seed + 2,
    )
    brier_interval = _interval_or_none(
        brier_by_scenario,
        resamples=resamples,
        seed=seed + 3,
    )
    path_interval = _interval_or_none(
        path_by_scenario,
        resamples=resamples,
        seed=seed + 4,
    )

    by_family: dict[str, dict[str, float]] = {}
    scenarios = sorted(mission_by_scenario)
    for family in sorted(set(family_by_scenario.values())):
        family_scenarios = [
            scenario
            for scenario in scenarios
            if family_by_scenario[scenario] == family
        ]
        family_row: dict[str, float] = {
            "scenario_count": float(len(family_scenarios)),
            "mean_mission_failure_difference": mean(
                mean(mission_by_scenario[s]) for s in family_scenarios
            ),
            "mean_operational_failure_difference": mean(
                mean(composite_by_scenario[s]) for s in family_scenarios
            ),
        }
        successful = [
            s for s in family_scenarios if s in return_risk_by_scenario
        ]
        if successful:
            family_row.update(
                {
                    "joint_success_scenario_count": float(len(successful)),
                    "mean_conditional_return_risk_difference": mean(
                        mean(return_risk_by_scenario[s]) for s in successful
                    ),
                    "mean_conditional_brier_difference": mean(
                        mean(brier_by_scenario[s]) for s in successful
                    ),
                    "mean_conditional_path_difference": mean(
                        mean(path_by_scenario[s]) for s in successful
                    ),
                }
            )
        by_family[family] = family_row

    return {
        "proposed": proposed,
        "baseline": baseline,
        "observation_regime": observation_regime,
        "scenario_count": len(mission_by_scenario),
        "paired_seed_count": len(pairs),
        "joint_mission_success_pair_count": joint_success_pairs,
        "asymmetric_mission_success_pair_count": asymmetric_mission_pairs,
        "invalid_rows": invalid_count,
        "mission_failure_difference": asdict(mission_interval),
        "operational_failure_difference": asdict(composite_interval),
        "conditional_return_risk_difference": risk_interval,
        "conditional_brier_difference": brier_interval,
        "conditional_path_length_difference": path_interval,
        "by_family": by_family,
    }
