"""Human-aware and ethics-guided navigation policy for Contribution 10.

This module converts human-proximity, ethical-zone, and operator-trust evidence
into concrete planner actions.

The goal is to make human-aware navigation auditable:

    context -> ethical decision -> planner constraint / velocity / autonomy level
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum


class ZoneType(str, Enum):
    NONE = "none"
    NO_GO = "no_go"
    SLOW_ZONE = "slow_zone"
    ANNOUNCE = "announce"
    AVOID_IF_POSSIBLE = "avoid_if_possible"


class PlannerAction(str, Enum):
    NORMAL = "NORMAL"
    SLOW_DOWN = "SLOW_DOWN"
    ANNOUNCE_AND_SLOW = "ANNOUNCE_AND_SLOW"
    AVOID_ZONE = "AVOID_ZONE"
    BLOCK_PATH = "BLOCK_PATH"
    ASK_OPERATOR = "ASK_OPERATOR"


@dataclass(frozen=True)
class HumanEthicsContext:
    zone_type: ZoneType = ZoneType.NONE
    distance_to_human_m: float = 10.0
    operator_trust: float = 1.0
    language_confidence: float = 1.0
    requested_autonomy: float = 1.0


@dataclass(frozen=True)
class HumanEthicsConfig:
    personal_space_m: float = 1.2
    caution_space_m: float = 2.5
    low_trust_threshold: float = 0.35
    low_language_confidence: float = 0.55
    normal_max_speed: float = 1.0
    caution_speed: float = 0.45
    slow_zone_speed: float = 0.20


@dataclass(frozen=True)
class HumanEthicsDecision:
    action: PlannerAction
    max_speed: float
    autonomy_level: float
    path_allowed: bool
    requires_announcement: bool
    requires_operator_confirmation: bool
    ethical_cost_multiplier: float
    explanation: str

    def to_dict(self) -> dict[str, float | bool | str]:
        row = asdict(self)
        row["action"] = self.action.value
        return row


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def decide_human_ethics_policy(
    context: HumanEthicsContext,
    cfg: HumanEthicsConfig | None = None,
) -> HumanEthicsDecision:
    cfg = cfg or HumanEthicsConfig()
    trust = clamp01(context.operator_trust)
    language_confidence = clamp01(context.language_confidence)
    requested_autonomy = clamp01(context.requested_autonomy)
    autonomy = min(requested_autonomy, 0.5 + 0.5 * trust)

    # Hard ethical constraints override everything.
    if context.zone_type == ZoneType.NO_GO:
        return HumanEthicsDecision(
            action=PlannerAction.BLOCK_PATH,
            max_speed=0.0,
            autonomy_level=0.0,
            path_allowed=False,
            requires_announcement=False,
            requires_operator_confirmation=True,
            ethical_cost_multiplier=float("inf"),
            explanation="candidate path enters a hard no-go ethical zone",
        )

    if trust < cfg.low_trust_threshold or language_confidence < cfg.low_language_confidence:
        return HumanEthicsDecision(
            action=PlannerAction.ASK_OPERATOR,
            max_speed=cfg.caution_speed,
            autonomy_level=min(autonomy, 0.35),
            path_allowed=True,
            requires_announcement=False,
            requires_operator_confirmation=True,
            ethical_cost_multiplier=2.0,
            explanation="operator trust or language confidence is too low for full autonomy",
        )

    if context.distance_to_human_m < cfg.personal_space_m:
        return HumanEthicsDecision(
            action=PlannerAction.SLOW_DOWN,
            max_speed=min(cfg.slow_zone_speed, cfg.caution_speed),
            autonomy_level=min(autonomy, 0.5),
            path_allowed=True,
            requires_announcement=False,
            requires_operator_confirmation=False,
            ethical_cost_multiplier=2.5,
            explanation="robot is inside personal-space distance of a human",
        )

    if context.zone_type == ZoneType.SLOW_ZONE:
        return HumanEthicsDecision(
            action=PlannerAction.SLOW_DOWN,
            max_speed=cfg.slow_zone_speed,
            autonomy_level=autonomy,
            path_allowed=True,
            requires_announcement=False,
            requires_operator_confirmation=False,
            ethical_cost_multiplier=1.5,
            explanation="candidate path enters a slow-zone ethical region",
        )

    if context.zone_type == ZoneType.ANNOUNCE:
        return HumanEthicsDecision(
            action=PlannerAction.ANNOUNCE_AND_SLOW,
            max_speed=cfg.caution_speed,
            autonomy_level=autonomy,
            path_allowed=True,
            requires_announcement=True,
            requires_operator_confirmation=False,
            ethical_cost_multiplier=1.2,
            explanation="robot should announce presence and proceed cautiously",
        )

    if context.zone_type == ZoneType.AVOID_IF_POSSIBLE:
        return HumanEthicsDecision(
            action=PlannerAction.AVOID_ZONE,
            max_speed=cfg.caution_speed,
            autonomy_level=autonomy,
            path_allowed=True,
            requires_announcement=False,
            requires_operator_confirmation=False,
            ethical_cost_multiplier=2.0,
            explanation="soft ethical zone should be avoided unless needed",
        )

    if context.distance_to_human_m < cfg.caution_space_m:
        return HumanEthicsDecision(
            action=PlannerAction.SLOW_DOWN,
            max_speed=cfg.caution_speed,
            autonomy_level=autonomy,
            path_allowed=True,
            requires_announcement=False,
            requires_operator_confirmation=False,
            ethical_cost_multiplier=1.3,
            explanation="human nearby; reduce speed and increase clearance",
        )

    return HumanEthicsDecision(
        action=PlannerAction.NORMAL,
        max_speed=cfg.normal_max_speed,
        autonomy_level=autonomy,
        path_allowed=True,
        requires_announcement=False,
        requires_operator_confirmation=False,
        ethical_cost_multiplier=1.0,
        explanation="no human-aware or ethical constraint requires intervention",
    )
