"""Safe online calibration utilities for action-triggered closure probabilities.

The learner only updates a hazard after that trigger was actually exposed.
This makes policy-dependent data availability explicit: avoiding a trigger
preserves safety but also leaves its closure probability uncertain.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from scipy.stats import beta as beta_distribution


@dataclass(frozen=True)
class BetaClosurePosterior:
    alpha: float = 1.0
    beta: float = 1.0
    exposures: int = 0
    closures: int = 0

    def validate(self) -> None:
        if not isfinite(self.alpha) or not isfinite(self.beta):
            raise ValueError("beta posterior parameters must be finite")
        if self.alpha <= 0.0 or self.beta <= 0.0:
            raise ValueError("beta posterior parameters must be positive")
        if self.exposures < 0 or self.closures < 0 or self.closures > self.exposures:
            raise ValueError("invalid exposure/closure counts")

    @property
    def mean(self) -> float:
        self.validate()
        return self.alpha / (self.alpha + self.beta)

    @property
    def variance(self) -> float:
        self.validate()
        total = self.alpha + self.beta
        return self.alpha * self.beta / (total * total * (total + 1.0))

    def credible_interval(self, mass: float = 0.95) -> tuple[float, float]:
        self.validate()
        if not 0.0 < mass < 1.0:
            raise ValueError("mass must be in (0, 1)")
        tail = (1.0 - mass) / 2.0
        return (
            float(beta_distribution.ppf(tail, self.alpha, self.beta)),
            float(beta_distribution.ppf(1.0 - tail, self.alpha, self.beta)),
        )

    def update(self, *, exposed: bool, closure_observed: bool = False) -> BetaClosurePosterior:
        """Update only from an activated/exposed trigger.

        A non-exposed action carries no information about P(closure | trigger).
        """

        self.validate()
        if not exposed:
            if closure_observed:
                raise ValueError("cannot observe a trigger-conditioned closure without exposure")
            return self
        return BetaClosurePosterior(
            alpha=self.alpha + float(closure_observed),
            beta=self.beta + float(not closure_observed),
            exposures=self.exposures + 1,
            closures=self.closures + int(closure_observed),
        )

    def expected_variance_after_one_exposure(self) -> float:
        """Expected posterior variance after one additional Bernoulli outcome."""

        p = self.mean
        closed = BetaClosurePosterior(self.alpha + 1.0, self.beta)
        open_ = BetaClosurePosterior(self.alpha, self.beta + 1.0)
        return p * closed.variance + (1.0 - p) * open_.variance

    def expected_variance_reduction(self) -> float:
        return max(0.0, self.variance - self.expected_variance_after_one_exposure())


@dataclass(frozen=True)
class SafeProbeCandidate:
    hazard_index: int
    predicted_return_probability: float
    traversal_cost: float = 1.0

    def validate(self) -> None:
        if self.hazard_index < 0:
            raise ValueError("hazard_index must be non-negative")
        if (
            not isfinite(self.predicted_return_probability)
            or not 0.0 <= self.predicted_return_probability <= 1.0
        ):
            raise ValueError("predicted_return_probability must be in [0, 1]")
        if not isfinite(self.traversal_cost) or self.traversal_cost <= 0.0:
            raise ValueError("traversal_cost must be positive")


@dataclass(frozen=True)
class SafeProbeDecision:
    hazard_index: int | None
    score: float
    reason: str


def select_safe_information_probe(
    posteriors: dict[int, BetaClosurePosterior],
    candidates: tuple[SafeProbeCandidate, ...],
    *,
    minimum_return_probability: float,
) -> SafeProbeDecision:
    """Select the safest admissible probe with the highest learning value/cost.

    The learning value is expected Beta posterior variance reduction.  This is
    deliberately a transparent acquisition rule rather than a claim of optimal
    Bayesian experimental design.
    """

    if not 0.0 <= minimum_return_probability <= 1.0:
        raise ValueError("minimum_return_probability must be in [0, 1]")
    best_index: int | None = None
    best_score = float("-inf")
    for candidate in candidates:
        candidate.validate()
        if candidate.hazard_index not in posteriors:
            raise ValueError(f"missing posterior for hazard {candidate.hazard_index}")
        if candidate.predicted_return_probability < minimum_return_probability:
            continue
        posterior = posteriors[candidate.hazard_index]
        score = posterior.expected_variance_reduction() / candidate.traversal_cost
        if score > best_score:
            best_score = score
            best_index = candidate.hazard_index

    if best_index is None:
        return SafeProbeDecision(None, 0.0, "no candidate satisfies the return constraint")
    return SafeProbeDecision(best_index, best_score, "max expected variance reduction per traversal cost")


def naive_unexposed_as_open_limit(
    exposure_probability: float,
    true_closure_probability: float,
) -> float:
    """Asymptotic naive estimate when non-exposures are logged as open.

    If exposure occurs with probability r and closure conditional on exposure
    occurs with probability p, coding every non-exposure as a Bernoulli zero
    makes the sample mean converge to r*p instead of p.
    """

    if not 0.0 <= exposure_probability <= 1.0:
        raise ValueError("exposure_probability must be in [0, 1]")
    if not 0.0 <= true_closure_probability <= 1.0:
        raise ValueError("true_closure_probability must be in [0, 1]")
    return exposure_probability * true_closure_probability


def conservative_return_lower_bound(
    posterior: BetaClosurePosterior,
    *,
    confidence: float = 0.90,
) -> float:
    """One-sided Bayesian lower bound on return in a single critical-trigger model.

    If closure makes return fail and the closure probability has a Beta
    posterior, the one-sided upper posterior quantile for closure risk induces
    a lower bound on return probability. This is a diagnostic model quantity,
    not a frequentist or deployment-safety guarantee.
    """

    posterior.validate()
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in (0, 1)")
    upper_closure = float(
        beta_distribution.ppf(confidence, posterior.alpha, posterior.beta)
    )
    return min(1.0, max(0.0, 1.0 - upper_closure))


def credible_safe_probe_allowed(
    posterior: BetaClosurePosterior,
    *,
    minimum_return_probability: float,
    confidence: float = 0.90,
) -> bool:
    """Return whether a one-sided posterior return bound admits exposure."""

    if not 0.0 <= minimum_return_probability <= 1.0:
        raise ValueError("minimum_return_probability must be in [0, 1]")
    return (
        conservative_return_lower_bound(posterior, confidence=confidence)
        >= minimum_return_probability
    )
