"""Exploratory benchmark for risk-budgeted learning after G3 lockout."""

from __future__ import annotations

import random
from dataclasses import dataclass

from dynnav.online_hazard_learning import (
    BetaClosurePosterior,
    credible_safe_probe_allowed,
)
from dynnav.risk_budget_learning import (
    ExplorationRiskBudget,
    budgeted_probe_decision,
)


@dataclass(frozen=True)
class RiskBudgetLearningRecord:
    policy: str
    true_closure_probability: float
    minimum_return_probability: float
    confidence: float
    opportunities: int
    exposures: int
    exploratory_exposures: int
    closures: int
    return_failures: int
    posterior_mean: float
    absolute_error: float
    budget_total: float
    budget_spent: float


def run_risk_budget_learning_benchmark(
    *,
    opportunities: int = 2_000,
    true_closure_probability: float = 0.3,
    minimum_return_probability: float = 0.7,
    confidence: float = 0.90,
    budgets: tuple[float, ...] = (5.0, 20.0, 50.0),
    seed: int = 0,
) -> list[RiskBudgetLearningRecord]:
    """Compare strict credible gating with finite risk-budgeted exposure."""

    if opportunities <= 0:
        raise ValueError("opportunities must be positive")
    if not 0.0 <= true_closure_probability <= 1.0:
        raise ValueError("true_closure_probability must be in [0, 1]")
    if not 0.0 <= minimum_return_probability <= 1.0:
        raise ValueError("minimum_return_probability must be in [0, 1]")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in (0, 1)")
    if any(value < 0.0 for value in budgets):
        raise ValueError("budgets must be non-negative")

    rng = random.Random(seed)
    latent = [
        rng.random() < true_closure_probability
        for _ in range(opportunities)
    ]

    posterior_by_policy: dict[str, BetaClosurePosterior] = {
        "credible_gate": BetaClosurePosterior(1.0, 3.0),
        "posterior_mean_gate": BetaClosurePosterior(1.0, 3.0),
        "oracle_gate": BetaClosurePosterior(1.0, 3.0),
    }
    budget_by_policy: dict[str, ExplorationRiskBudget] = {}
    for budget in budgets:
        name = f"risk_budget_{budget:g}"
        posterior_by_policy[name] = BetaClosurePosterior(1.0, 3.0)
        budget_by_policy[name] = ExplorationRiskBudget(total=float(budget))

    failures = {name: 0 for name in posterior_by_policy}
    exploratory = {name: 0 for name in posterior_by_policy}

    for closure in latent:
        credible = posterior_by_policy["credible_gate"]
        credible_exposed = credible_safe_probe_allowed(
            credible,
            minimum_return_probability=minimum_return_probability,
            confidence=confidence,
        )
        posterior_by_policy["credible_gate"] = credible.update(
            exposed=credible_exposed,
            closure_observed=closure if credible_exposed else False,
        )
        failures["credible_gate"] += int(credible_exposed and closure)

        mean_posterior = posterior_by_policy["posterior_mean_gate"]
        mean_exposed = 1.0 - mean_posterior.mean >= minimum_return_probability
        posterior_by_policy["posterior_mean_gate"] = mean_posterior.update(
            exposed=mean_exposed,
            closure_observed=closure if mean_exposed else False,
        )
        failures["posterior_mean_gate"] += int(mean_exposed and closure)

        oracle_exposed = (
            1.0 - true_closure_probability >= minimum_return_probability
        )
        posterior_by_policy["oracle_gate"] = posterior_by_policy[
            "oracle_gate"
        ].update(
            exposed=oracle_exposed,
            closure_observed=closure if oracle_exposed else False,
        )
        failures["oracle_gate"] += int(oracle_exposed and closure)

        for name in budget_by_policy:
            posterior = posterior_by_policy[name]
            budget = budget_by_policy[name]
            decision = budgeted_probe_decision(
                posterior,
                budget,
                minimum_return_probability=minimum_return_probability,
                confidence=confidence,
            )
            if decision.allowed and decision.exploratory:
                budget = budget.charge(decision.risk_charge)
                budget_by_policy[name] = budget
                exploratory[name] += 1
            posterior_by_policy[name] = posterior.update(
                exposed=decision.allowed,
                closure_observed=closure if decision.allowed else False,
            )
            failures[name] += int(decision.allowed and closure)

    records: list[RiskBudgetLearningRecord] = []
    for name, posterior in posterior_by_policy.items():
        estimate = (
            true_closure_probability if name == "oracle_gate" else posterior.mean
        )
        budget = budget_by_policy.get(name, ExplorationRiskBudget(0.0))
        records.append(
            RiskBudgetLearningRecord(
                policy=name,
                true_closure_probability=true_closure_probability,
                minimum_return_probability=minimum_return_probability,
                confidence=confidence,
                opportunities=opportunities,
                exposures=posterior.exposures,
                exploratory_exposures=exploratory[name],
                closures=posterior.closures,
                return_failures=failures[name],
                posterior_mean=estimate,
                absolute_error=abs(estimate - true_closure_probability),
                budget_total=budget.total,
                budget_spent=budget.spent,
            )
        )
    return records
