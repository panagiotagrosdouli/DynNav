from __future__ import annotations

from dynnav.security import (
    AttributionEvidence,
    DetectorResult,
    FusionMethod,
    MitigationAction,
    NavigationContext,
    SecurityState,
    SecurityStateMachine,
    TrustState,
    attribute_anomaly,
    choose_mitigation,
    fuse_trust,
    security_risk,
)


def trust(source: str, value: float, confidence: float = 0.9) -> TrustState:
    return TrustState(source, value, value, confidence, 20, 1.0 - value, 10.0, "stable", "healthy")


def detector(source: str = "gps") -> DetectorResult:
    return DetectorResult(20.0, 9.0, True, True, 0.9, 3, "cusum", source, 10.0, {})


def test_reliability_weighted_fusion_preserves_contributors() -> None:
    result = fuse_trust(
        {"gps": trust("gps", 0.2, 0.9), "imu": trust("imu", 0.9, 0.8)},
        FusionMethod.RELIABILITY_WEIGHTED,
    )
    assert 0.2 < result.value < 0.9
    assert result.contributors == ("gps", "imu")


def test_minimum_fusion_is_conservative() -> None:
    result = fuse_trust({"gps": trust("gps", 0.3), "imu": trust("imu", 0.95)}, FusionMethod.MINIMUM)
    assert result.value == 0.3


def test_gps_attribution_uses_cross_sensor_disagreement() -> None:
    result = attribute_anomaly(
        detector(), trust("gps", 0.3), AttributionEvidence("gps", trend="ramp", cross_sensor_consistent=False, duration=6)
    )
    assert result.likely_cause == "GPS spoofing"
    assert result.confidence > 0.5
    assert result.supporting_evidence


def test_contextual_mitigation_isolates_only_with_redundancy() -> None:
    attribution = attribute_anomaly(
        detector(), trust("gps", 0.25), AttributionEvidence("gps", cross_sensor_consistent=False, duration=5)
    )
    decision = choose_mitigation(
        "gps",
        "WARNING",
        trust("gps", 0.25),
        attribution,
        5,
        NavigationContext(speed=1.0, obstacle_proximity=3.0, redundancy_available=True),
    )
    assert decision.isolate_source
    assert decision.primary is MitigationAction.DISABLE_SOURCE
    assert decision.speed_scale < 1.0


def test_critical_close_obstacle_recommends_emergency_stop() -> None:
    attribution = attribute_anomaly(
        detector(), trust("gps", 0.2), AttributionEvidence("gps", cross_sensor_consistent=False, duration=5)
    )
    decision = choose_mitigation(
        "gps",
        "CRITICAL",
        trust("gps", 0.2),
        attribution,
        5,
        NavigationContext(speed=1.2, obstacle_proximity=0.5, redundancy_available=False),
    )
    assert decision.primary is MitigationAction.EMERGENCY_STOP_RECOMMENDATION
    assert decision.speed_scale == 0.0


def test_security_risk_increases_as_trust_falls() -> None:
    nominal = security_risk(1.0, 0.9, 0.9, 0.1)
    degraded = security_risk(1.0, 0.2, 0.4, 0.1)
    assert degraded > nominal


def test_state_machine_requires_persistent_attribution() -> None:
    machine = SecurityStateMachine()
    states = []
    for index in range(3):
        transition = machine.update(
            timestamp=float(index), triggered=True, trust=0.45, attribution_confidence=0.8
        )
        states.append(transition.current)
    assert states[-1] is SecurityState.ATTACK_LIKELY


def test_state_machine_enters_recovery_monitoring() -> None:
    machine = SecurityStateMachine()
    for index in range(3):
        machine.update(timestamp=float(index), triggered=True, trust=0.4, attribution_confidence=0.8)
    transition = machine.update(timestamp=4.0, triggered=False, trust=0.85, attribution_confidence=0.1)
    assert transition.current is SecurityState.RECOVERY_MONITORING
