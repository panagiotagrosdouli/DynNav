from __future__ import annotations

from dynnav.experiments.risk_budget_learning_benchmark import (
    run_risk_budget_learning_benchmark,
)
from dynnav.online_hazard_learning import BetaClosurePosterior
from dynnav.risk_budget_learning import (
    ExplorationRiskBudget,
    budgeted_probe_decision,
    posterior_upper_closure_bound,
)


def test_zero_budget_reduces_to_strict_credible_gate_when_prior_is_unsafe() -> None:
    posterior = BetaClosurePosterior(1.0, 3.0)
    decision = budgeted_probe_decision(
        posterior,
        ExplorationRiskBudget(0.0),
        minimum_return_probability=0.7,
        confidence=0.90,
    )
    assert not decision.allowed
    assert not decision.exploratory


def test_positive_budget_breaks_cold_start_lockout() -> None:
    posterior = BetaClosurePosterior(1.0, 3.0)
    upper = posterior_upper_closure_bound(posterior, confidence=0.90)
    decision = budgeted_probe_decision(
        posterior,
        ExplorationRiskBudget(upper),
        minimum_return_probability=0.7,
        confidence=0.90,
    )
    assert decision.allowed
    assert decision.exploratory
    assert decision.risk_charge == upper


def test_risk_budget_obtains_data_when_strict_gate_stays_locked() -> None:
    rows = run_risk_budget_learning_benchmark(
        opportunities=500,
        true_closure_probability=0.3,
        minimum_return_probability=0.7,
        confidence=0.90,
        budgets=(5.0, 20.0),
        seed=31,
    )
    by_policy = {row.policy: row for row in rows}
    assert by_policy["credible_gate"].exposures == 0
    assert by_policy["risk_budget_5"].exposures > 0
    assert by_policy["risk_budget_20"].exposures >= by_policy["risk_budget_5"].exposures
    assert by_policy["risk_budget_20"].budget_spent <= 20.0 + 1e-12
