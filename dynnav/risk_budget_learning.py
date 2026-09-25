"""Exploration-budget mechanism for breaking safe-learning lockout.

A strictly confidence-gated learner can deadlock when its initial conservative
return bound is already below the required threshold and trigger-conditioned
outcomes are observable only after exposure.

This module adds an explicit finite *exploration risk budget*.  Each exposure is
charged by a one-sided posterior upper bound on closure probability.  Once the
budget is exhausted, no further exploratory exposure is allowed unless the
ordinary credible safety gate is already satisfied.

The budget is an accounting device for research experiments, not a deployment
safety guarantee.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from scipy.stats import beta as beta_distribution

from dynnav.online_hazard_learning import (
    BetaClosurePosterior,
    credible_safe_probe_allowed,
)


@dataclass(frozen=True)
class ExplorationRiskBudget:
    total: float
    spent: float = 0.0
    exploratory_exposures: int = 0

    def validate(self) -> None:
        if not isfinite(self.total) or self.total < 0.0:
            raise ValueError("total exploration risk budget must be finite and non-negative")
        if not isfinite(self.spent) or self.spent < 0.0:
            raise ValueError("spent exploration risk must be finite and non-negative")
        if self.spent > self.total + 1e-12:
            raise ValueError("spent exploration risk cannot exceed total budget")
        if self.exploratory_exposures < 0:
            raise ValueError("exploratory_exposures must be non-negative")

    @property
    def remaining(self) -> float:
        self.validate()
        return max(0.0, self.total - self.spent)

    def charge(self, amount: float) -> ExplorationRiskBudget:
        self.validate()
        if not isfinite(amount) or amount < 0.0:
            raise ValueError("risk charge must be finite and non-negative")
        if amount > self.remaining + 1e-12:
            raise ValueError("risk charge exceeds remaining exploration budget")
        return ExplorationRiskBudget(
            total=self.total,
            spent=self.spent + amount,
            exploratory_exposures=self.exploratory_exposures + 1,
        )


@dataclass(frozen=True)
class BudgetedProbeDecision:
    allowed: bool
    exploratory: bool
    risk_charge: float
    reason: str


def posterior_upper_closure_bound(
    posterior: BetaClosurePosterior,
    *,
    confidence: float = 0.90,
) -> float:
    """Return a one-sided posterior upper quantile for closure probability."""

    posterior.validate()
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in (0, 1)")
    return float(beta_distribution.ppf(confidence, posterior.alpha, posterior.beta))


def budgeted_probe_decision(
    posterior: BetaClosurePosterior,
    budget: ExplorationRiskBudget,
    *,
    minimum_return_probability: float,
    confidence: float = 0.90,
) -> BudgetedProbeDecision:
    """Allow a probe via the credible gate or a finite explicit risk budget."""

    posterior.validate()
    budget.validate()
    if not 0.0 <= minimum_return_probability <= 1.0:
        raise ValueError("minimum_return_probability must be in [0, 1]")

    if credible_safe_probe_allowed(
        posterior,
        minimum_return_probability=minimum_return_probability,
        confidence=confidence,
    ):
        return BudgetedProbeDecision(
            allowed=True,
            exploratory=False,
            risk_charge=0.0,
            reason="credible return bound satisfies threshold",
        )

    charge = posterior_upper_closure_bound(posterior, confidence=confidence)
    if charge <= budget.remaining + 1e-12:
        return BudgetedProbeDecision(
            allowed=True,
            exploratory=True,
            risk_charge=charge,
            reason="credible gate failed; finite exploration budget admits one probe",
        )

    return BudgetedProbeDecision(
        allowed=False,
        exploratory=False,
        risk_charge=0.0,
        reason="credible gate failed and exploration budget is exhausted",
    )
