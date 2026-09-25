"""G3 assumption-class benchmark after the no-exposure impossibility result.

The benchmark asks what additional assumption breaks exposure-only
non-identifiability and what cost it introduces.

Policies/information structures:
- strict_credible_gate: target-trigger observations only; no admitted risk;
- risk_budget: target-trigger observations bought with an explicit risk budget;
- passive_same_parameter: risk-free Bernoulli observations of the same p;
- transfer_shared_parameter: risk-free observations from a related trigger,
  analyzed under the assumption that it shares the target p;
- oracle: target p known.

The passive and transfer methods are assumption controls, not claims that such
side information is generally available in robotics.
"""

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
class InformationAssumptionRecord:
    policy: str
    true_target_probability: float
    related_probability: float | None
    minimum_return_probability: float
    opportunities: int
    target_exposures: int
    side_observations: int
    target_failures: int
    posterior_mean: float
    absolute_error: float
    budget_total: float
    budget_spent: float
    structural_bias: float | None


def _observe_without_target_exposure(
    posterior: BetaClosurePosterior,
    closure_observed: bool,
) -> BetaClosurePosterior:
    """Update Beta evidence without counting a target-trigger exposure."""

    posterior.validate()
    return BetaClosurePosterior(
        posterior.alpha + float(closure_observed),
        posterior.beta + float(not closure_observed),
        exposures=posterior.exposures,
        closures=posterior.closures,
    )


def run_information_assumption_benchmark(
    *,
    opportunities: int = 1_000,
    true_target_probability: float = 0.3,
    minimum_return_probability: float = 0.7,
    confidence: float = 0.90,
    risk_budget: float = 20.0,
    passive_observation_rate: float = 0.25,
    transfer_observation_rate: float = 0.25,
    transfer_biases: tuple[float, ...] = (-0.2, 0.0, 0.2),
    seed: int = 20260925,
) -> list[InformationAssumptionRecord]:
    """Compare information assumptions on matched latent target opportunities."""

    if opportunities <= 0:
        raise ValueError("opportunities must be positive")
    for name, value in (
        ("true_target_probability", true_target_probability),
        ("minimum_return_probability", minimum_return_probability),
        ("passive_observation_rate", passive_observation_rate),
        ("transfer_observation_rate", transfer_observation_rate),
    ):
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be in [0, 1]")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in (0, 1)")
    if risk_budget < 0.0:
        raise ValueError("risk_budget must be non-negative")

    rng = random.Random(seed)
    target_latent = [
        rng.random() < true_target_probability for _ in range(opportunities)
    ]
    passive_available = [
        rng.random() < passive_observation_rate for _ in range(opportunities)
    ]
    passive_latent = [
        rng.random() < true_target_probability for _ in range(opportunities)
    ]
    transfer_available = [
        rng.random() < transfer_observation_rate for _ in range(opportunities)
    ]

    records: list[InformationAssumptionRecord] = []

    strict = BetaClosurePosterior(1.0, 3.0)
    strict_failures = 0
    for outcome in target_latent:
        exposed = credible_safe_probe_allowed(
            strict,
            minimum_return_probability=minimum_return_probability,
            confidence=confidence,
        )
        strict = strict.update(
            exposed=exposed,
            closure_observed=outcome if exposed else False,
        )
        strict_failures += int(exposed and outcome)
    records.append(
        InformationAssumptionRecord(
            policy="strict_credible_gate",
            true_target_probability=true_target_probability,
            related_probability=None,
            minimum_return_probability=minimum_return_probability,
            opportunities=opportunities,
            target_exposures=strict.exposures,
            side_observations=0,
            target_failures=strict_failures,
            posterior_mean=strict.mean,
            absolute_error=abs(strict.mean - true_target_probability),
            budget_total=0.0,
            budget_spent=0.0,
            structural_bias=None,
        )
    )

    budgeted = BetaClosurePosterior(1.0, 3.0)
    budget = ExplorationRiskBudget(float(risk_budget))
    budget_failures = 0
    for outcome in target_latent:
        decision = budgeted_probe_decision(
            budgeted,
            budget,
            minimum_return_probability=minimum_return_probability,
            confidence=confidence,
        )
        if decision.allowed and decision.exploratory:
            budget = budget.charge(decision.risk_charge)
        budgeted = budgeted.update(
            exposed=decision.allowed,
            closure_observed=outcome if decision.allowed else False,
        )
        budget_failures += int(decision.allowed and outcome)
    records.append(
        InformationAssumptionRecord(
            policy=f"risk_budget_{risk_budget:g}",
            true_target_probability=true_target_probability,
            related_probability=None,
            minimum_return_probability=minimum_return_probability,
            opportunities=opportunities,
            target_exposures=budgeted.exposures,
            side_observations=0,
            target_failures=budget_failures,
            posterior_mean=budgeted.mean,
            absolute_error=abs(budgeted.mean - true_target_probability),
            budget_total=budget.total,
            budget_spent=budget.spent,
            structural_bias=None,
        )
    )

    passive = BetaClosurePosterior(1.0, 3.0)
    passive_count = 0
    for available, outcome in zip(
        passive_available,
        passive_latent,
        strict=True,
    ):
        if available:
            passive = _observe_without_target_exposure(passive, outcome)
            passive_count += 1
    records.append(
        InformationAssumptionRecord(
            policy="passive_same_parameter",
            true_target_probability=true_target_probability,
            related_probability=true_target_probability,
            minimum_return_probability=minimum_return_probability,
            opportunities=opportunities,
            target_exposures=0,
            side_observations=passive_count,
            target_failures=0,
            posterior_mean=passive.mean,
            absolute_error=abs(passive.mean - true_target_probability),
            budget_total=0.0,
            budget_spent=0.0,
            structural_bias=0.0,
        )
    )

    for bias_index, transfer_bias in enumerate(transfer_biases):
        related_probability = min(
            1.0,
            max(0.0, true_target_probability + transfer_bias),
        )
        transfer_rng = random.Random(seed + 100_000 + bias_index)
        transfer_latent = [
            transfer_rng.random() < related_probability
            for _ in range(opportunities)
        ]
        posterior = BetaClosurePosterior(1.0, 3.0)
        count = 0
        for available, outcome in zip(
            transfer_available,
            transfer_latent,
            strict=True,
        ):
            if available:
                posterior = _observe_without_target_exposure(
                    posterior,
                    outcome,
                )
                count += 1
        records.append(
            InformationAssumptionRecord(
                policy=f"transfer_shared_parameter_bias_{transfer_bias:+.2f}",
                true_target_probability=true_target_probability,
                related_probability=related_probability,
                minimum_return_probability=minimum_return_probability,
                opportunities=opportunities,
                target_exposures=0,
                side_observations=count,
                target_failures=0,
                posterior_mean=posterior.mean,
                absolute_error=abs(
                    posterior.mean - true_target_probability
                ),
                budget_total=0.0,
                budget_spent=0.0,
                structural_bias=related_probability
                - true_target_probability,
            )
        )

    records.append(
        InformationAssumptionRecord(
            policy="oracle_known_probability",
            true_target_probability=true_target_probability,
            related_probability=None,
            minimum_return_probability=minimum_return_probability,
            opportunities=opportunities,
            target_exposures=0,
            side_observations=0,
            target_failures=0,
            posterior_mean=true_target_probability,
            absolute_error=0.0,
            budget_total=0.0,
            budget_spent=0.0,
            structural_bias=None,
        )
    )
    return records
