"""VLM goal validation and safety gating for Contribution 11.

A VLM can produce useful semantic goals, but it can also hallucinate labels,
return invalid JSON fields, or point to unsafe / out-of-frame locations. This
module validates VLM semantic goals before they are passed to the navigation
planner.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Iterable


class GoalDecision(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    ASK_HUMAN = "ASK_HUMAN"


@dataclass(frozen=True)
class ValidationConfig:
    min_confidence: float = 0.55
    ask_human_confidence: float = 0.40
    max_waypoint_distance_m: float = 8.0
    allowed_regions: tuple[str, ...] = (
        "corridor",
        "doorway",
        "open_space",
        "room",
        "exit",
        "hallway",
        "frontier",
    )
    forbidden_words: tuple[str, ...] = (
        "stairs",
        "glass",
        "restricted",
        "private",
        "danger",
        "unknown_hazard",
    )


@dataclass(frozen=True)
class GoalValidationReport:
    decision: GoalDecision
    valid_confidence: bool
    valid_region: bool
    valid_pixel: bool
    valid_waypoint: bool
    reason: str

    def to_dict(self) -> dict[str, str | bool]:
        row = asdict(self)
        row["decision"] = self.decision.value
        return row


def _contains_forbidden_text(text: str, forbidden_words: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(word.lower() in lowered for word in forbidden_words)


def validate_vlm_goal(
    *,
    description: str,
    region_label: str,
    confidence: float,
    pixel_hint: tuple[int, int] | None,
    image_shape: tuple[int, int] | None = None,
    metric_waypoint: tuple[float, float] | None = None,
    robot_xy: tuple[float, float] = (0.0, 0.0),
    cfg: ValidationConfig | None = None,
) -> GoalValidationReport:
    """Validate a semantic VLM goal before navigation execution."""
    cfg = cfg or ValidationConfig()
    confidence = float(confidence)
    region = str(region_label).lower().strip()
    text = f"{description} {region}"

    valid_confidence = confidence >= cfg.min_confidence
    valid_region = region in {r.lower() for r in cfg.allowed_regions}
    if _contains_forbidden_text(text, cfg.forbidden_words):
        valid_region = False

    valid_pixel = True
    if pixel_hint is not None and image_shape is not None:
        h, w = image_shape[:2]
        u, v = pixel_hint
        valid_pixel = 0 <= int(u) < int(w) and 0 <= int(v) < int(h)

    valid_waypoint = True
    if metric_waypoint is not None:
        dx = float(metric_waypoint[0] - robot_xy[0])
        dy = float(metric_waypoint[1] - robot_xy[1])
        valid_waypoint = (dx * dx + dy * dy) ** 0.5 <= cfg.max_waypoint_distance_m

    if valid_confidence and valid_region and valid_pixel and valid_waypoint:
        return GoalValidationReport(
            decision=GoalDecision.ACCEPT,
            valid_confidence=valid_confidence,
            valid_region=valid_region,
            valid_pixel=valid_pixel,
            valid_waypoint=valid_waypoint,
            reason="goal passed VLM safety validation",
        )

    if confidence >= cfg.ask_human_confidence and valid_pixel and valid_waypoint:
        return GoalValidationReport(
            decision=GoalDecision.ASK_HUMAN,
            valid_confidence=valid_confidence,
            valid_region=valid_region,
            valid_pixel=valid_pixel,
            valid_waypoint=valid_waypoint,
            reason="goal is partially plausible but needs human confirmation",
        )

    return GoalValidationReport(
        decision=GoalDecision.REJECT,
        valid_confidence=valid_confidence,
        valid_region=valid_region,
        valid_pixel=valid_pixel,
        valid_waypoint=valid_waypoint,
        reason="goal failed VLM safety validation",
    )
