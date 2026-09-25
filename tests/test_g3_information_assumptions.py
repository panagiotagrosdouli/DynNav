from __future__ import annotations

from dynnav.experiments.g3_information_assumptions import (
    run_information_assumption_benchmark,
)


def test_passive_same_parameter_breaks_lockout_without_target_failures() -> None:
    rows = run_information_assumption_benchmark(
        opportunities=2_000,
        true_target_probability=0.3,
        minimum_return_probability=0.7,
        passive_observation_rate=0.5,
        transfer_observation_rate=0.5,
        seed=31,
    )
    by_policy = {row.policy: row for row in rows}
    strict = by_policy["strict_credible_gate"]
    passive = by_policy["passive_same_parameter"]

    assert strict.target_exposures == 0
    assert passive.target_exposures == 0
    assert passive.target_failures == 0
    assert passive.side_observations > 0
    assert passive.absolute_error < strict.absolute_error


def test_transfer_is_accurate_only_when_shared_parameter_assumption_is_correct() -> None:
    rows = run_information_assumption_benchmark(
        opportunities=4_000,
        true_target_probability=0.4,
        minimum_return_probability=0.8,
        passive_observation_rate=0.0,
        transfer_observation_rate=0.75,
        transfer_biases=(-0.2, 0.0, 0.2),
        seed=41,
    )
    by_policy = {row.policy: row for row in rows}
    matched = by_policy["transfer_shared_parameter_bias_+0.00"]
    low = by_policy["transfer_shared_parameter_bias_-0.20"]
    high = by_policy["transfer_shared_parameter_bias_+0.20"]

    assert matched.absolute_error < 0.04
    assert low.absolute_error > 0.12
    assert high.absolute_error > 0.12
    assert low.target_failures == high.target_failures == 0


def test_risk_budget_buys_target_information_with_realized_failure_cost() -> None:
    rows = run_information_assumption_benchmark(
        opportunities=2_000,
        true_target_probability=0.5,
        minimum_return_probability=0.8,
        risk_budget=50.0,
        passive_observation_rate=0.0,
        transfer_observation_rate=0.0,
        seed=73,
    )
    by_policy = {row.policy: row for row in rows}
    budgeted = by_policy["risk_budget_50"]

    assert budgeted.target_exposures > 0
    assert budgeted.target_failures > 0
    assert 0.0 < budgeted.budget_spent <= 50.0
