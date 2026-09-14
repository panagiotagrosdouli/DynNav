from __future__ import annotations

import json

import pytest

from dynnav.experiments.multiseed_evaluation import (
    EvaluationConfig,
    TrialRecord,
    aggregate,
    paired_comparisons,
    run_multiseed,
    sensitivity_grid,
    write_artifacts,
)
from dynnav.experiments.statistics import (
    bootstrap_mean_interval,
    exact_mcnemar_pvalue,
    paired_binary_effect,
    paired_effect,
)


def _runner(seed: int, method: str, parameters: dict[str, float]) -> TrialRecord:
    weight = parameters.get("weight", 0.0)
    advantage = 2.0 if method == "proposed" else 0.0
    return TrialRecord(
        seed=seed,
        method=method,
        success=True,
        irreversible_failure=False,
        path_length=10.0 + seed % 2,
        planning_time_ms=20.0 + seed - advantage + weight,
        nodes_expanded=100.0 + seed - 5.0 * advantage,
        cumulative_risk=2.0 - 0.1 * advantage,
        cumulative_irreversibility=3.0 - 0.2 * advantage,
        minimum_escape_options=1.0 + advantage,
    )


def test_bootstrap_is_deterministic_and_contains_mean() -> None:
    first = bootstrap_mean_interval([1, 2, 3, 4], resamples=500, seed=7)
    second = bootstrap_mean_interval([1, 2, 3, 4], resamples=500, seed=7)
    assert first == second
    assert first.lower <= first.estimate <= first.upper


def test_paired_effect_reports_proposed_improvement() -> None:
    effect = paired_effect([10, 11, 12], [8, 9, 10], resamples=500)
    assert effect.mean_difference == pytest.approx(-2.0)
    assert effect.probability_of_superiority == 1.0


def test_exact_mcnemar_known_discordant_case() -> None:
    assert exact_mcnemar_pvalue(8, 0) == pytest.approx(2.0 / 256.0)
    assert exact_mcnemar_pvalue(0, 0) == pytest.approx(1.0)


def test_paired_binary_effect_reports_event_reduction() -> None:
    baseline = [1, 1, 1, 1, 0, 0, 1, 1]
    proposed = [0, 0, 0, 1, 0, 0, 0, 1]
    effect = paired_binary_effect(baseline, proposed, resamples=500, seed=9)

    assert effect.baseline_rate == pytest.approx(0.75)
    assert effect.proposed_rate == pytest.approx(0.25)
    assert effect.risk_difference == pytest.approx(-0.5)
    assert effect.baseline_only_events == 4
    assert effect.proposed_only_events == 0
    assert effect.discordant_pairs == 4
    assert effect.mcnemar_exact_pvalue == pytest.approx(0.125)


def test_multiseed_aggregation_and_pairing() -> None:
    config = EvaluationConfig(seeds=(1, 2, 3), bootstrap_resamples=500)
    records = run_multiseed(_runner, ["baseline", "proposed"], config=config)
    assert len(records) == 6
    summary = aggregate(records, config=config)
    assert summary["baseline"]["trials"] == 3
    assert summary["baseline"]["planning_failure_rate"] == 0.0
    assert summary["baseline"]["planning_time_ms"]["finite_trials"] == 3
    comparison = paired_comparisons(records, "baseline", "proposed", config=config)
    assert comparison["mean_difference"] < 0.0
    assert comparison["paired_trials"] == 3
    assert comparison["excluded_non_finite_pairs"] == 0


def test_failed_trials_remain_in_rates_and_non_finite_metrics_are_audited() -> None:
    config = EvaluationConfig(seeds=(1, 2), bootstrap_resamples=200)
    records = [
        TrialRecord(
            seed=1,
            method="planner",
            success=True,
            irreversible_failure=False,
            path_length=5.0,
            planning_time_ms=2.0,
            nodes_expanded=10.0,
            cumulative_risk=0.5,
            cumulative_irreversibility=0.25,
            minimum_escape_options=2.0,
        ),
        TrialRecord(
            seed=2,
            method="planner",
            success=False,
            irreversible_failure=False,
            path_length=0.0,
            planning_time_ms=3.0,
            nodes_expanded=8.0,
            cumulative_risk=float("inf"),
            cumulative_irreversibility=float("inf"),
            minimum_escape_options=0.0,
            planning_failure=True,
        ),
    ]

    summary = aggregate(records, config=config)["planner"]

    assert summary["trials"] == 2
    assert summary["success_rate"] == pytest.approx(0.5)
    assert summary["planning_failure_rate"] == pytest.approx(0.5)
    assert summary["cumulative_risk"]["finite_trials"] == 1
    assert summary["cumulative_risk"]["excluded_non_finite"] == 1
    assert summary["cumulative_risk"]["summary"]["mean"] == pytest.approx(0.5)


def test_paired_comparison_reports_non_finite_pair_exclusion() -> None:
    config = EvaluationConfig(seeds=(1, 2), bootstrap_resamples=200)
    baseline = _runner(1, "baseline", {})
    proposed = _runner(1, "proposed", {})
    failed_baseline = TrialRecord(
        seed=2,
        method="baseline",
        success=False,
        irreversible_failure=False,
        path_length=0.0,
        planning_time_ms=4.0,
        nodes_expanded=10.0,
        cumulative_risk=float("inf"),
        cumulative_irreversibility=float("inf"),
        minimum_escape_options=0.0,
        planning_failure=True,
    )
    failed_proposed = TrialRecord(
        seed=2,
        method="proposed",
        success=False,
        irreversible_failure=False,
        path_length=0.0,
        planning_time_ms=5.0,
        nodes_expanded=11.0,
        cumulative_risk=float("inf"),
        cumulative_irreversibility=float("inf"),
        minimum_escape_options=0.0,
        planning_failure=True,
    )

    comparison = paired_comparisons(
        [baseline, proposed, failed_baseline, failed_proposed],
        "baseline",
        "proposed",
        metric="cumulative_risk",
        config=config,
    )

    assert comparison["paired_trials"] == 1
    assert comparison["excluded_non_finite_pairs"] == 1


def test_sensitivity_grid_and_artifacts(tmp_path) -> None:
    config = EvaluationConfig(seeds=(1, 2), bootstrap_resamples=200)
    grid = sensitivity_grid(_runner, "proposed", "weight", [0.0, 2.0], config=config)
    assert set(grid) == {"0.0", "2.0"}
    records = run_multiseed(_runner, ["proposed"], config=config)
    summary = aggregate(records, config=config)
    write_artifacts(records, summary, tmp_path)
    assert (tmp_path / "trials.csv").exists()
    payload = json.loads((tmp_path / "summary.json").read_text())
    assert payload["proposed"]["trials"] == 2


def test_configuration_rejects_duplicate_seeds() -> None:
    with pytest.raises(ValueError):
        EvaluationConfig(seeds=(1, 1)).validate()
