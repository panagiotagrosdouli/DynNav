"""Exploratory G3 benchmark for safety-learning lockout.

The frozen V1 benchmark gates probing by posterior mean. This post-full-study
diagnostic compares that optimistic model quantity with a one-sided posterior
lower bound on return probability. The purpose is to expose the identifiability
tradeoff: a sufficiently conservative rule may refuse the very exposure needed
to reduce uncertainty.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from dynnav.online_hazard_learning import (
    BetaClosurePosterior,
    credible_safe_probe_allowed,
)


@dataclass(frozen=True)
class SafeLearningLockoutRecord:
    policy: str
    true_closure_probability: float
    minimum_return_probability: float
    confidence: float
    opportunities: int
    exposures: int
    closures: int
    posterior_mean: float
    absolute_error: float
    return_failures: int


def run_safe_learning_lockout_benchmark(
    *,
    opportunities: int = 2_000,
    true_closure_probability: float = 0.3,
    minimum_return_probability: float = 0.7,
    confidence: float = 0.90,
    seed: int = 0,
) -> list[SafeLearningLockoutRecord]:
    """Compare posterior-mean, credible-bound and oracle exposure gates."""

    if opportunities <= 0:
        raise ValueError("opportunities must be positive")
    if not 0.0 <= true_closure_probability <= 1.0:
        raise ValueError("true_closure_probability must be in [0, 1]")
    if not 0.0 <= minimum_return_probability <= 1.0:
        raise ValueError("minimum_return_probability must be in [0, 1]")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in (0, 1)")

    rng = random.Random(seed)
    latent = [
        rng.random() < true_closure_probability
        for _ in range(opportunities)
    ]
    posteriors = {
        "posterior_mean_gate": BetaClosurePosterior(1.0, 3.0),
        "credible_lower_gate": BetaClosurePosterior(1.0, 3.0),
        "oracle_gate": BetaClosurePosterior(1.0, 3.0),
    }
    failures = {name: 0 for name in posteriors}

    for closure in latent:
        mean_posterior = posteriors["posterior_mean_gate"]
        mean_exposed = (
            1.0 - mean_posterior.mean >= minimum_return_probability
        )
        posteriors["posterior_mean_gate"] = mean_posterior.update(
            exposed=mean_exposed,
            closure_observed=closure if mean_exposed else False,
        )
        failures["posterior_mean_gate"] += int(mean_exposed and closure)

        credible_posterior = posteriors["credible_lower_gate"]
        credible_exposed = credible_safe_probe_allowed(
            credible_posterior,
            minimum_return_probability=minimum_return_probability,
            confidence=confidence,
        )
        posteriors["credible_lower_gate"] = credible_posterior.update(
            exposed=credible_exposed,
            closure_observed=closure if credible_exposed else False,
        )
        failures["credible_lower_gate"] += int(credible_exposed and closure)

        oracle_exposed = (
            1.0 - true_closure_probability >= minimum_return_probability
        )
        posteriors["oracle_gate"] = posteriors["oracle_gate"].update(
            exposed=oracle_exposed,
            closure_observed=closure if oracle_exposed else False,
        )
        failures["oracle_gate"] += int(oracle_exposed and closure)

    records: list[SafeLearningLockoutRecord] = []
    for name, posterior in posteriors.items():
        estimate = (
            true_closure_probability if name == "oracle_gate" else posterior.mean
        )
        records.append(
            SafeLearningLockoutRecord(
                policy=name,
                true_closure_probability=true_closure_probability,
                minimum_return_probability=minimum_return_probability,
                confidence=confidence,
                opportunities=opportunities,
                exposures=posterior.exposures,
                closures=posterior.closures,
                posterior_mean=estimate,
                absolute_error=abs(estimate - true_closure_probability),
                return_failures=failures[name],
            )
        )
    return records
