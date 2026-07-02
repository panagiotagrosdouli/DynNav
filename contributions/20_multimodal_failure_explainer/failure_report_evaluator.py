"""Failure-report quality evaluator for Contribution 20.

A failure explainer should be evaluated, not only generated. This module scores
reports using auditable criteria:

- completeness of required sections,
- coverage of expected root causes,
- relevance of corrective actions,
- STL/safety-monitor coverage,
- operator readiness.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from multimodal_failure_explainer import FailureReport


@dataclass(frozen=True)
class FailureExplanationExpectation:
    case_name: str
    expected_root_causes: tuple[str, ...]
    expected_action_keywords: tuple[str, ...]
    requires_stl_summary: bool = True


@dataclass(frozen=True)
class FailureReportScore:
    case_name: str
    completeness_score: float
    root_cause_recall: float
    action_relevance: float
    stl_coverage: float
    operator_readiness: float
    total_score: float

    def to_dict(self) -> dict[str, float | str]:
        return asdict(self)


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(k.lower() in lowered for k in keywords)


def score_failure_report(
    report: FailureReport,
    expectation: FailureExplanationExpectation,
) -> FailureReportScore:
    sections = [
        bool(report.scene_description.strip()),
        len(report.root_causes) > 0,
        bool(report.stl_summary.strip()),
        len(report.corrective_actions) > 0,
        report.confidence > 0.0,
    ]
    completeness = sum(sections) / len(sections)

    predicted_causes = {name for name, _ in report.root_causes}
    if expectation.expected_root_causes:
        root_recall = sum(c in predicted_causes for c in expectation.expected_root_causes) / len(expectation.expected_root_causes)
    else:
        root_recall = 1.0

    action_text = " ".join(report.corrective_actions).lower()
    if expectation.expected_action_keywords:
        action_relevance = sum(k.lower() in action_text for k in expectation.expected_action_keywords) / len(expectation.expected_action_keywords)
    else:
        action_relevance = 1.0

    stl_summary = report.stl_summary.lower()
    stl_coverage = 1.0
    if expectation.requires_stl_summary:
        stl_coverage = 0.0 if "no stl data" in stl_summary or not stl_summary.strip() else 1.0

    operator_readiness = 1.0 if (
        completeness >= 0.8
        and len(report.corrective_actions) >= 2
        and report.confidence >= 0.5
    ) else 0.0

    total = (
        0.25 * completeness
        + 0.25 * root_recall
        + 0.20 * action_relevance
        + 0.15 * stl_coverage
        + 0.15 * operator_readiness
    )
    return FailureReportScore(
        case_name=expectation.case_name,
        completeness_score=float(completeness),
        root_cause_recall=float(root_recall),
        action_relevance=float(action_relevance),
        stl_coverage=float(stl_coverage),
        operator_readiness=float(operator_readiness),
        total_score=float(total),
    )


def summarize_scores(scores: list[FailureReportScore]) -> dict[str, float | int]:
    if not scores:
        raise ValueError("scores must not be empty")
    return {
        "n_cases": len(scores),
        "mean_total_score": sum(s.total_score for s in scores) / len(scores),
        "mean_root_cause_recall": sum(s.root_cause_recall for s in scores) / len(scores),
        "mean_action_relevance": sum(s.action_relevance for s in scores) / len(scores),
        "operator_ready_rate": sum(s.operator_readiness for s in scores) / len(scores),
    }
