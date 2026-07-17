"""Deterministic policy from sensor-security observations to navigation responses."""

from __future__ import annotations

from dataclasses import dataclass

from .events import AttributionResult
from .mitigation import MitigationDecision, NavigationContext, choose_mitigation
from .pipeline import SensorSecurityObservation


@dataclass(frozen=True)
class SensorNavigationDecision:
    """Security observation paired with its navigation-facing mitigation."""

    observation: SensorSecurityObservation
    severity: str
    attribution: AttributionResult
    mitigation: MitigationDecision


def observation_severity(observation: SensorSecurityObservation) -> str:
    """Map detector and trust evidence to a stable severity label."""
    result = observation.detector_result
    trust = observation.trust_state
    if result.triggered or trust.health_status == "UNTRUSTED":
        return "CRITICAL"
    if result.flagged or trust.health_status == "DEGRADED" or trust.filtered_trust < 0.8:
        return "WARNING"
    return "NORMAL"


def default_sensor_attribution(observation: SensorSecurityObservation) -> AttributionResult:
    """Create transparent fallback attribution when no causal model is supplied."""
    sensor = observation.sensor.value
    result = observation.detector_result
    evidence = [f"detector={result.detector_name}", f"sensor={sensor}"]
    if result.flagged:
        evidence.append("residual anomaly flagged")
    if result.triggered:
        evidence.append("detector trigger policy satisfied")
    return AttributionResult(
        likely_cause=f"{sensor} sensor anomaly",
        confidence=result.confidence,
        supporting_evidence=tuple(evidence),
        alternative_causes=("sensor degradation", "environmental disturbance"),
    )


def decide_sensor_response(
    observation: SensorSecurityObservation,
    context: NavigationContext,
    *,
    duration: int = 1,
    attribution: AttributionResult | None = None,
) -> SensorNavigationDecision:
    """Convert one security observation into a deterministic mitigation decision."""
    if duration < 1:
        raise ValueError("duration must be at least 1")
    resolved_attribution = attribution or default_sensor_attribution(observation)
    severity = observation_severity(observation)
    mitigation = choose_mitigation(
        observation.trust_state.source_id,
        severity,
        observation.trust_state,
        resolved_attribution,
        duration,
        context,
    )
    return SensorNavigationDecision(observation, severity, resolved_attribution, mitigation)
