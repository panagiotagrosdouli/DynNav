"""Self-awareness scoring for navigation under uncertainty."""

from __future__ import annotations

from dataclasses import dataclass

from dynnav.core.navigation_state import NavigationState


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, value))


@dataclass(frozen=True)
class SelfAwarenessScore:
    """Interpretable confidence summary used by higher-level planners.

    Attributes:
        trust: Overall trust in the current navigation state in [0, 1].
        uncertainty_pressure: How strongly uncertainty should affect planning.
        risk_pressure: How strongly risk should affect planning.
        recoverability_pressure: How strongly low recoverability should affect planning.
        recommended_mode: Suggested high-level mode: NOMINAL, CAUTIOUS, ACTIVE_SENSE, or SAFE_STOP.
    """

    trust: float
    uncertainty_pressure: float
    risk_pressure: float
    recoverability_pressure: float
    recommended_mode: str


def estimate_self_awareness(state: NavigationState) -> SelfAwarenessScore:
    """Estimate whether the robot should trust, slow down, or gather information.

    The score is a deliberately simple baseline, not a final research claim. It
    provides an interpretable starting point for benchmark ablations.
    """
    state.validate()

    uncertainty_pressure = _clip01(
        0.55 * state.localization_uncertainty + 0.45 * state.map_uncertainty
    )
    sensor_trust = _clip01(
        0.50 * state.perception_confidence + 0.50 * state.planner_confidence
    )
    risk_pressure = _clip01(state.risk_estimate)
    recoverability_pressure = _clip01(1.0 - state.recoverability)

    trust = _clip01(
        0.40 * sensor_trust
        + 0.25 * (1.0 - uncertainty_pressure)
        + 0.20 * (1.0 - risk_pressure)
        + 0.15 * state.recoverability
    )

    if risk_pressure > 0.85 or (trust < 0.25 and state.recoverability < 0.35):
        mode = "SAFE_STOP"
    elif uncertainty_pressure > 0.60 and sensor_trust < 0.65:
        mode = "ACTIVE_SENSE"
    elif trust < 0.60 or risk_pressure > 0.50 or recoverability_pressure > 0.50:
        mode = "CAUTIOUS"
    else:
        mode = "NOMINAL"

    return SelfAwarenessScore(
        trust=trust,
        uncertainty_pressure=uncertainty_pressure,
        risk_pressure=risk_pressure,
        recoverability_pressure=recoverability_pressure,
        recommended_mode=mode,
    )
