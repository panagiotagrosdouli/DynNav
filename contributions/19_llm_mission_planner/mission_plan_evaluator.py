"""Mission-plan validation and evaluation for Contribution 19.

The LLM mission planner translates language into waypoints. This evaluator checks
whether the resulting plan is actually executable and constraint-aware.

Metrics include:
- expected waypoint ordering accuracy,
- unresolved waypoint count,
- duplicate waypoint count,
- forbidden-zone violations,
- missing required waypoints,
- execution-readiness verdict.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from llm_mission_planner import Mission


@dataclass(frozen=True)
class MissionPlanExpectation:
    instruction: str
    expected_labels: tuple[str, ...]
    required_labels: tuple[str, ...] = ()
    forbidden_labels: tuple[str, ...] = ()


@dataclass(frozen=True)
class MissionPlanReport:
    instruction: str
    predicted_sequence: str
    expected_sequence: str
    ordering_accuracy: float
    exact_sequence_match: bool
    unresolved_waypoints: int
    duplicate_waypoints: int
    forbidden_violations: int
    missing_required: int
    execution_ready: bool
    confidence: float

    def to_dict(self) -> dict[str, float | int | bool | str]:
        return asdict(self)


def _normalize(label: str) -> str:
    return label.lower().strip().replace(" ", "_")


def ordering_accuracy(predicted: list[str], expected: tuple[str, ...]) -> float:
    if not expected:
        return 1.0 if not predicted else 0.0
    score = 0
    for i, label in enumerate(expected):
        if i < len(predicted) and predicted[i] == label:
            score += 1
    return score / len(expected)


def evaluate_mission_plan(
    mission: Mission,
    expectation: MissionPlanExpectation,
    zone_map: dict[str, tuple[float, float]],
) -> MissionPlanReport:
    predicted = [_normalize(w.label) for w in mission.waypoints]
    expected = tuple(_normalize(x) for x in expectation.expected_labels)
    required = tuple(_normalize(x) for x in expectation.required_labels)
    forbidden = tuple(_normalize(x) for x in expectation.forbidden_labels)

    unresolved = sum(label not in zone_map for label in predicted)
    duplicate_count = len(predicted) - len(set(predicted))
    forbidden_violations = sum(label in forbidden for label in predicted)
    missing_required = sum(label not in predicted for label in required)
    exact = tuple(predicted) == expected
    order_acc = ordering_accuracy(predicted, expected)
    execution_ready = (
        unresolved == 0
        and duplicate_count == 0
        and forbidden_violations == 0
        and missing_required == 0
        and len(predicted) > 0
    )

    return MissionPlanReport(
        instruction=expectation.instruction,
        predicted_sequence="->".join(predicted),
        expected_sequence="->".join(expected),
        ordering_accuracy=float(order_acc),
        exact_sequence_match=bool(exact),
        unresolved_waypoints=int(unresolved),
        duplicate_waypoints=int(duplicate_count),
        forbidden_violations=int(forbidden_violations),
        missing_required=int(missing_required),
        execution_ready=bool(execution_ready),
        confidence=float(mission.confidence),
    )


def summarize_reports(reports: list[MissionPlanReport]) -> dict[str, float | int]:
    if not reports:
        raise ValueError("reports must not be empty")
    return {
        "n_cases": len(reports),
        "mean_ordering_accuracy": sum(r.ordering_accuracy for r in reports) / len(reports),
        "exact_match_rate": sum(r.exact_sequence_match for r in reports) / len(reports),
        "execution_ready_rate": sum(r.execution_ready for r in reports) / len(reports),
        "total_forbidden_violations": sum(r.forbidden_violations for r in reports),
        "total_unresolved_waypoints": sum(r.unresolved_waypoints for r in reports),
    }
