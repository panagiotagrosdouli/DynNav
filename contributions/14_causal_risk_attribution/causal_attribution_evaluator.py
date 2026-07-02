"""Causal attribution evaluation utilities for Contribution 14.

The SCM can rank possible root causes, but a scientific benchmark should also
measure whether the ranking recovers known injected root causes. This module
provides simple evaluation metrics for root-cause attribution experiments.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass(frozen=True)
class AttributionCase:
    name: str
    observed_noise: dict[str, float]
    true_root_cause: str
    intervention_value: float = 0.0


@dataclass(frozen=True)
class AttributionResult:
    case_name: str
    true_root_cause: str
    predicted_root_cause: str
    true_cause_rank: int
    top1_correct: bool
    baseline_outcome: float
    counterfactual_outcome: float
    counterfactual_reduction: float
    ranking: str

    def to_dict(self) -> dict[str, float | int | bool | str]:
        return asdict(self)


def evaluate_attribution_case(
    scm,
    case: AttributionCase,
    outcome_node: str = "collision",
    n_samples: int = 200,
) -> AttributionResult:
    baseline = scm.observational_query(case.observed_noise)[outcome_node]
    ranking = scm.root_cause_ranking(case.observed_noise, outcome_node=outcome_node, n_samples=n_samples)
    predicted = ranking[0][0] if ranking else "none"
    names = [name for name, _ in ranking]
    true_rank = names.index(case.true_root_cause) + 1 if case.true_root_cause in names else len(names) + 1
    cf = scm.counterfactual_query(case.observed_noise, {case.true_root_cause: case.intervention_value})
    cf_outcome = float(cf[outcome_node])
    return AttributionResult(
        case_name=case.name,
        true_root_cause=case.true_root_cause,
        predicted_root_cause=predicted,
        true_cause_rank=int(true_rank),
        top1_correct=predicted == case.true_root_cause,
        baseline_outcome=float(baseline),
        counterfactual_outcome=cf_outcome,
        counterfactual_reduction=float(baseline - cf_outcome),
        ranking=";".join(f"{name}:{score:.4f}" for name, score in ranking),
    )


def summarize_attribution_results(results: Iterable[AttributionResult]) -> dict[str, float | int]:
    results = list(results)
    if not results:
        raise ValueError("results must not be empty")
    return {
        "n_cases": len(results),
        "top1_accuracy": sum(r.top1_correct for r in results) / len(results),
        "mean_true_cause_rank": sum(r.true_cause_rank for r in results) / len(results),
        "mean_counterfactual_reduction": sum(r.counterfactual_reduction for r in results) / len(results),
    }
