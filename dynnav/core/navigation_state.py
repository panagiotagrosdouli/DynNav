"""Navigation state containers for self-aware planning.

These dataclasses deliberately avoid ROS-specific types. They represent the
planner-facing quantities that a robot should reason about when deciding
whether to exploit a current route or gather more information first.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


GridCell = tuple[int, int]


@dataclass(frozen=True)
class NavigationState:
    """Planner-facing state with uncertainty and risk signals.

    Attributes:
        pose: Current discrete robot cell.
        goal: Goal cell.
        localization_uncertainty: Normalized pose uncertainty in [0, 1].
        map_uncertainty: Normalized map uncertainty in [0, 1].
        perception_confidence: Normalized confidence in current perception in [0, 1].
        planner_confidence: Normalized confidence in the planner output in [0, 1].
        risk_estimate: Normalized local risk estimate in [0, 1].
        recoverability: Normalized ability to recover or return from the current state in [0, 1].
    """

    pose: GridCell
    goal: GridCell
    localization_uncertainty: float
    map_uncertainty: float
    perception_confidence: float
    planner_confidence: float
    risk_estimate: float
    recoverability: float

    def validate(self) -> None:
        """Raise ValueError if normalized fields are outside [0, 1]."""
        for name in (
            "localization_uncertainty",
            "map_uncertainty",
            "perception_confidence",
            "planner_confidence",
            "risk_estimate",
            "recoverability",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1], got {value!r}")


@dataclass(frozen=True)
class PathEvaluation:
    """Summary metrics for a candidate path.

    These values are intentionally close to the benchmark protocol so the same
    object can feed both decision making and CSV logging.
    """

    path: Sequence[GridCell]
    path_length: float
    expected_collision_risk: float
    cvar_tail_risk: float
    localization_uncertainty: float
    map_uncertainty: float
    information_gain: float
    recoverability: float
    compute_time_ms: float = 0.0

    def validate(self) -> None:
        """Raise ValueError for invalid normalized metric values."""
        normalized_fields = (
            "expected_collision_risk",
            "cvar_tail_risk",
            "localization_uncertainty",
            "map_uncertainty",
            "information_gain",
            "recoverability",
        )
        for name in normalized_fields:
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1], got {value!r}")
        if self.path_length < 0.0:
            raise ValueError(f"path_length must be non-negative, got {self.path_length!r}")
        if self.compute_time_ms < 0.0:
            raise ValueError(f"compute_time_ms must be non-negative, got {self.compute_time_ms!r}")
