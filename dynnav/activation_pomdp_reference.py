"""Exact one-step belief/POMDP reference for uncertain trigger activation.

This is deliberately a minimal POMDP-style decision problem, not a claim of a
general POMDP planner.

Hidden state:
    A in {inactive, active}
Observation:
    noisy crossing detector O in {0,1}
Decision after O:
    continue through the return-critical region, or take a deterministic detour

Continuing has expected loss:
    continue_cost + P(A=1 | O) * closure_probability * failure_cost

Detouring has deterministic loss:
    detour_cost

The exact belief-state action is whichever has lower posterior expected loss.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from dynnav.activation_belief import ActivationBelief


@dataclass(frozen=True)
class OneStepActivationDecisionProblem:
    activation_probability: float
    closure_probability: float
    detector_sensitivity: float
    detector_specificity: float
    failure_cost: float
    detour_cost: float
    continue_cost: float = 0.0

    def validate(self) -> None:
        for name in (
            "activation_probability",
            "closure_probability",
            "detector_sensitivity",
            "detector_specificity",
        ):
            value = getattr(self, name)
            if not isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be finite and in [0, 1]")
        for name in ("failure_cost", "detour_cost", "continue_cost"):
            value = getattr(self, name)
            if not isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and non-negative")


@dataclass(frozen=True)
class OneStepActivationDecision:
    observed_crossing: bool
    posterior_activation_probability: float
    posterior_failure_probability: float
    continue_expected_loss: float
    detour_expected_loss: float
    action: str
    value: float


def direct_activation_posterior(
    problem: OneStepActivationDecisionProblem,
    *,
    observed_crossing: bool,
) -> float:
    """Closed-form Bayes posterior P(A=1 | observation)."""

    problem.validate()
    prior = problem.activation_probability
    likelihood_if_active = (
        problem.detector_sensitivity
        if observed_crossing
        else 1.0 - problem.detector_sensitivity
    )
    likelihood_if_inactive = (
        1.0 - problem.detector_specificity
        if observed_crossing
        else problem.detector_specificity
    )
    numerator = prior * likelihood_if_active
    denominator = numerator + (1.0 - prior) * likelihood_if_inactive
    if denominator <= 0.0:
        raise ValueError("observation has zero probability under the model")
    return numerator / denominator


def exact_one_step_activation_decision(
    problem: OneStepActivationDecisionProblem,
    *,
    observed_crossing: bool,
) -> OneStepActivationDecision:
    """Solve the exact one-step belief-state decision."""

    posterior = direct_activation_posterior(
        problem,
        observed_crossing=observed_crossing,
    )
    failure_probability = posterior * problem.closure_probability
    continue_loss = problem.continue_cost + failure_probability * problem.failure_cost
    detour_loss = problem.detour_cost
    if continue_loss <= detour_loss:
        action = "continue"
        value = continue_loss
    else:
        action = "detour"
        value = detour_loss
    return OneStepActivationDecision(
        observed_crossing=observed_crossing,
        posterior_activation_probability=posterior,
        posterior_failure_probability=failure_probability,
        continue_expected_loss=continue_loss,
        detour_expected_loss=detour_loss,
        action=action,
        value=value,
    )


def dynnav_belief_one_step_decision(
    problem: OneStepActivationDecisionProblem,
    *,
    observed_crossing: bool,
) -> OneStepActivationDecision:
    """Solve the same decision using DynNav's ActivationBelief update."""

    problem.validate()
    posterior = ActivationBelief.certain_inactive().update_after_trigger_attempt(
        0,
        execution_probability=problem.activation_probability,
        observed_crossing=observed_crossing,
        detection_sensitivity=problem.detector_sensitivity,
        detection_specificity=problem.detector_specificity,
    )
    posterior_active = sum(
        probability
        for active, probability in posterior.probability_by_active_set.items()
        if 0 in active
    )
    failure_probability = posterior_active * problem.closure_probability
    continue_loss = problem.continue_cost + failure_probability * problem.failure_cost
    detour_loss = problem.detour_cost
    if continue_loss <= detour_loss:
        action = "continue"
        value = continue_loss
    else:
        action = "detour"
        value = detour_loss
    return OneStepActivationDecision(
        observed_crossing=observed_crossing,
        posterior_activation_probability=posterior_active,
        posterior_failure_probability=failure_probability,
        continue_expected_loss=continue_loss,
        detour_expected_loss=detour_loss,
        action=action,
        value=value,
    )
