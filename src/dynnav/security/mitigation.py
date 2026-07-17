"""Context-aware navigation responses to cyber-physical evidence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .events import AttributionResult, TrustState


class MitigationAction(str, Enum):
    NONE = "no_action"
    INCREASE_MONITORING = "increase_monitoring"
    REDUCE_SPEED = "reduce_speed"
    INCREASE_OBSTACLE_INFLATION = "increase_obstacle_inflation"
    INCREASE_UNCERTAINTY_COST = "increase_uncertainty_cost"
    INCREASE_RISK_COST = "increase_risk_cost"
    DISABLE_SOURCE = "disable_affected_source"
    SWITCH_ESTIMATOR = "switch_estimator"
    REQUEST_RELOCALIZATION = "request_relocalization"
    REJECT_MAP_UPDATE = "reject_map_update"
    ISOLATE_PEER = "isolate_communication_peer"
    REPLAN = "replan"
    CAUTIOUS_MODE = "enter_cautious_mode"
    SAFE_STOP = "safe_stop"
    EMERGENCY_STOP_RECOMMENDATION = "emergency_stop_recommendation"
    MISSION_ABORT_RECOMMENDATION = "mission_abort_recommendation"


@dataclass(frozen=True)
class NavigationContext:
    speed: float
    obstacle_proximity: float
    redundancy_available: bool
    localization_critical: bool = True
    recovery_available: bool = True


@dataclass(frozen=True)
class MitigationDecision:
    primary: MitigationAction
    additional: tuple[MitigationAction, ...]
    speed_scale: float
    risk_multiplier: float
    isolate_source: bool
    rationale: tuple[str, ...]


def choose_mitigation(
    source_id: str,
    severity: str,
    trust: TrustState,
    attribution: AttributionResult,
    duration: int,
    context: NavigationContext,
) -> MitigationDecision:
    severity = severity.upper()
    actions: list[MitigationAction] = []
    rationale: list[str] = []
    speed_scale = 1.0
    risk_multiplier = 1.0
    isolate = False

    if severity == "NORMAL" and trust.filtered_trust >= 0.8:
        return MitigationDecision(MitigationAction.NONE, (), 1.0, 1.0, False, ("evidence remains nominal",))

    actions.append(MitigationAction.INCREASE_MONITORING)
    rationale.append(f"{source_id} trust is {trust.filtered_trust:.2f}")

    if severity in {"WARNING", "CRITICAL"} or trust.filtered_trust < 0.55:
        actions.extend((MitigationAction.REDUCE_SPEED, MitigationAction.INCREASE_UNCERTAINTY_COST))
        speed_scale = 0.6
        risk_multiplier = 1.5
        rationale.append("persistent evidence requires reduced navigation aggressiveness")

    cause = attribution.likely_cause.lower()
    if "gps" in cause or "localization" in cause:
        actions.extend((MitigationAction.REQUEST_RELOCALIZATION, MitigationAction.SWITCH_ESTIMATOR))
    elif "lidar" in cause:
        actions.extend((MitigationAction.REJECT_MAP_UPDATE, MitigationAction.INCREASE_OBSTACLE_INFLATION))
    elif "map tampering" in cause:
        actions.extend((MitigationAction.REJECT_MAP_UPDATE, MitigationAction.REPLAN))
    elif "communication injection" in cause:
        actions.append(MitigationAction.ISOLATE_PEER)

    if duration >= 3 and trust.filtered_trust < 0.4 and context.redundancy_available:
        actions.append(MitigationAction.DISABLE_SOURCE)
        isolate = True
        rationale.append("low trust is sustained and a redundant source is available")
    elif duration >= 3 and trust.filtered_trust < 0.4:
        actions.append(MitigationAction.CAUTIOUS_MODE)
        rationale.append("source cannot be isolated safely because redundancy is unavailable")

    if severity == "CRITICAL" and context.obstacle_proximity < 1.0 and context.speed > 0.5:
        actions.append(MitigationAction.EMERGENCY_STOP_RECOMMENDATION)
        speed_scale = 0.0
        risk_multiplier = 3.0
        rationale.append("critical evidence coincides with close obstacles and non-trivial speed")
    elif severity == "CRITICAL" and not context.recovery_available:
        actions.append(MitigationAction.SAFE_STOP)
        speed_scale = 0.0
        risk_multiplier = 2.5

    unique = tuple(dict.fromkeys(actions))
    return MitigationDecision(unique[-1], unique[:-1], speed_scale, risk_multiplier, isolate, tuple(rationale))


def security_risk(base_risk: float, source_trust: float, global_trust: float, context_sensitivity: float,
                  source_weight: float = 1.0, global_weight: float = 1.0, context_weight: float = 1.0) -> float:
    penalty = source_weight * (1.0 - source_trust) + global_weight * (1.0 - global_trust)
    penalty += context_weight * max(0.0, context_sensitivity)
    return max(0.0, float(base_risk) + penalty)
