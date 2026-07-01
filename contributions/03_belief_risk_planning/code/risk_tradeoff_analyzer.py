"""Risk trade-off analysis utilities for Contribution 03.

Contribution 03 studies the tension between path efficiency and risk exposure.
This module provides small, auditable utilities for evaluating a family of plans
under different risk metrics and selecting Pareto-efficient alternatives.

The goal is to make risk-aware planning claims more precise:

- not only "risk went down",
- but also how much path cost was paid for that reduction,
- whether a plan is dominated by another plan,
- and which lambda values produce meaningful trade-off points.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class PlanMetrics:
    """Metrics for one candidate path or assignment."""

    method: str
    lambda_value: float
    path_length: float
    mean_risk: float
    max_risk: float
    expected_risk: float
    cvar_risk: float
    total_objective: float
    dominated: bool = False

    def to_dict(self) -> dict[str, float | str | bool]:
        return asdict(self)


def _as_array(values: Iterable[float] | np.ndarray, name: str) -> np.ndarray:
    arr = np.asarray(list(values) if not isinstance(values, np.ndarray) else values, dtype=float).reshape(-1)
    if arr.size == 0:
        raise ValueError(f"{name} must contain at least one value.")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains non-finite values.")
    return arr


def expected_risk(risks: Iterable[float] | np.ndarray) -> float:
    arr = _as_array(risks, "risks")
    return float(np.mean(arr))


def cvar(risks: Iterable[float] | np.ndarray, alpha: float = 0.95) -> float:
    """Compute empirical CVaR over the upper tail of risk samples.

    alpha=0.95 means the mean of approximately the worst 5% risk values.
    For small paths, at least one sample is included in the tail.
    """
    if not 0.0 <= alpha < 1.0:
        raise ValueError("alpha must satisfy 0 <= alpha < 1.")
    arr = np.sort(_as_array(risks, "risks"))
    n_tail = max(1, int(np.ceil((1.0 - alpha) * len(arr))))
    return float(np.mean(arr[-n_tail:]))


def objective(path_length: float, risk_value: float, lambda_value: float) -> float:
    return float(path_length + lambda_value * risk_value)


def evaluate_plan(
    method: str,
    lambda_value: float,
    path_length: float,
    risk_samples: Iterable[float] | np.ndarray,
    alpha: float = 0.95,
    objective_risk: str = "cvar",
) -> PlanMetrics:
    risks = _as_array(risk_samples, "risk_samples")
    exp_risk = expected_risk(risks)
    cvar_risk = cvar(risks, alpha=alpha)
    max_risk = float(np.max(risks))
    mean_risk = float(np.mean(risks))

    if objective_risk == "expected":
        selected_risk = exp_risk
    elif objective_risk == "cvar":
        selected_risk = cvar_risk
    elif objective_risk == "max":
        selected_risk = max_risk
    else:
        raise ValueError("objective_risk must be one of: expected, cvar, max")

    return PlanMetrics(
        method=method,
        lambda_value=float(lambda_value),
        path_length=float(path_length),
        mean_risk=mean_risk,
        max_risk=max_risk,
        expected_risk=exp_risk,
        cvar_risk=cvar_risk,
        total_objective=objective(path_length, selected_risk, lambda_value),
    )


def mark_pareto_dominated(plans: list[PlanMetrics], risk_field: str = "cvar_risk") -> list[PlanMetrics]:
    """Mark plans dominated in both path length and selected risk metric.

    Plan A dominates plan B if A is no worse in length and risk and strictly
    better in at least one of them.
    """
    if risk_field not in {"mean_risk", "max_risk", "expected_risk", "cvar_risk"}:
        raise ValueError("Unsupported risk field.")

    updated: list[PlanMetrics] = []
    for i, plan in enumerate(plans):
        risk_i = float(getattr(plan, risk_field))
        dominated = False
        for j, other in enumerate(plans):
            if i == j:
                continue
            risk_j = float(getattr(other, risk_field))
            no_worse = other.path_length <= plan.path_length and risk_j <= risk_i
            strictly_better = other.path_length < plan.path_length or risk_j < risk_i
            if no_worse and strictly_better:
                dominated = True
                break
        updated.append(
            PlanMetrics(
                method=plan.method,
                lambda_value=plan.lambda_value,
                path_length=plan.path_length,
                mean_risk=plan.mean_risk,
                max_risk=plan.max_risk,
                expected_risk=plan.expected_risk,
                cvar_risk=plan.cvar_risk,
                total_objective=plan.total_objective,
                dominated=dominated,
            )
        )
    return updated


def relative_improvement(baseline: float, candidate: float) -> float:
    """Positive means candidate reduced the metric relative to baseline."""
    if baseline == 0:
        return float("nan")
    return float((baseline - candidate) / abs(baseline) * 100.0)


def path_length_increase(baseline: float, candidate: float) -> float:
    if baseline == 0:
        return float("nan")
    return float((candidate - baseline) / abs(baseline) * 100.0)
