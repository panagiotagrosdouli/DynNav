"""Interventional trigger-to-closure effect estimation for DynNav.

This module provides a deliberately narrow causal primitive: inverse-propensity
estimation of the effect of executing a candidate trigger on a later binary
closure event when the trigger-assignment probability is logged.  It does not
claim general causal discovery from arbitrary observational robot logs.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, sqrt


@dataclass(frozen=True)
class TriggerOutcomeRecord:
    trigger_id: str
    closure_id: str
    executed: bool
    closure_observed: bool
    execution_propensity: float

    def validate(self) -> None:
        if not self.trigger_id or not self.closure_id:
            raise ValueError("trigger_id and closure_id must be non-empty")
        if not isfinite(self.execution_propensity) or not 0.0 < self.execution_propensity < 1.0:
            raise ValueError("execution_propensity must be strictly between 0 and 1")


@dataclass(frozen=True)
class CausalEffectEstimate:
    trigger_id: str
    closure_id: str
    treated_mean: float
    control_mean: float
    ate: float
    standard_error: float
    sample_size: int
    treated_count: int
    control_count: int

    @property
    def approximate_95_interval(self) -> tuple[float, float]:
        radius = 1.96 * self.standard_error
        return self.ate - radius, self.ate + radius


def estimate_ipw_trigger_effect(
    records: list[TriggerOutcomeRecord] | tuple[TriggerOutcomeRecord, ...],
    *,
    trigger_id: str,
    closure_id: str,
) -> CausalEffectEstimate:
    """Estimate E[Y(1)] - E[Y(0)] using known execution propensities.

    The estimator is appropriate for randomized or otherwise ignorable
    assignments whose propensities are known and bounded away from zero/one.
    It is not sufficient to identify effects under hidden confounding.
    """

    selected = [
        record
        for record in records
        if record.trigger_id == trigger_id and record.closure_id == closure_id
    ]
    if not selected:
        raise ValueError("no records for requested trigger/closure pair")
    for record in selected:
        record.validate()

    treated_terms: list[float] = []
    control_terms: list[float] = []
    treated_count = 0
    control_count = 0
    for record in selected:
        y = float(record.closure_observed)
        p = record.execution_propensity
        if record.executed:
            treated_terms.append(y / p)
            control_terms.append(0.0)
            treated_count += 1
        else:
            treated_terms.append(0.0)
            control_terms.append(y / (1.0 - p))
            control_count += 1

    n = len(selected)
    treated_mean = sum(treated_terms) / n
    control_mean = sum(control_terms) / n
    influence = [
        treated - control - (treated_mean - control_mean)
        for treated, control in zip(treated_terms, control_terms, strict=True)
    ]
    variance = sum(value * value for value in influence) / max(1, n - 1) / n
    return CausalEffectEstimate(
        trigger_id=trigger_id,
        closure_id=closure_id,
        treated_mean=treated_mean,
        control_mean=control_mean,
        ate=treated_mean - control_mean,
        standard_error=sqrt(max(0.0, variance)),
        sample_size=n,
        treated_count=treated_count,
        control_count=control_count,
    )


def discover_trigger_closure_edges(
    records: list[TriggerOutcomeRecord] | tuple[TriggerOutcomeRecord, ...],
    *,
    minimum_effect: float = 0.0,
    require_positive_95_interval: bool = False,
) -> tuple[CausalEffectEstimate, ...]:
    """Screen logged trigger/closure pairs for positive interventional effects.

    This is a benchmark-oriented edge screen.  A returned edge means the
    supplied interventional data support a positive effect under the logged
    assignment assumptions; it is not a general SCM discovery guarantee.
    """

    if minimum_effect < 0.0:
        raise ValueError("minimum_effect must be non-negative")
    pairs = sorted({(record.trigger_id, record.closure_id) for record in records})
    estimates: list[CausalEffectEstimate] = []
    for trigger_id, closure_id in pairs:
        estimate = estimate_ipw_trigger_effect(
            records,
            trigger_id=trigger_id,
            closure_id=closure_id,
        )
        lower, _ = estimate.approximate_95_interval
        if estimate.ate < minimum_effect:
            continue
        if require_positive_95_interval and lower <= 0.0:
            continue
        estimates.append(estimate)
    return tuple(estimates)
