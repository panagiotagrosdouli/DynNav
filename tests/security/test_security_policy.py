from __future__ import annotations

import numpy as np
import pytest

from dynnav.security import (
    MitigationAction,
    NavigationContext,
    ResidualEvent,
    SensorKind,
    SensorSecurityMonitor,
    TrustConfig,
    decide_sensor_response,
    observation_severity,
)


def _event(source_id: str, *, innovation: float = 0.0, freshness: float = 1.0) -> ResidualEvent:
    measurement = np.array([innovation], dtype=float)
    return ResidualEvent(
        source_id=source_id,
        measurement=measurement,
        prediction=np.zeros(1, dtype=float),
        innovation=measurement,
        covariance=np.eye(1, dtype=float),
        timestamp=1.0,
        freshness=freshness,
    )


def _context(**overrides: object) -> NavigationContext:
    values = {
        "speed": 0.2,
        "obstacle_proximity": 5.0,
        "redundancy_available": True,
        "localization_critical": True,
        "recovery_available": True,
    }
    values.update(overrides)
    return NavigationContext(**values)


def test_nominal_observation_requires_no_action() -> None:
    monitor = SensorSecurityMonitor("camera/front", SensorKind.CAMERA)
    observation = monitor.update(_event("camera/front"))

    decision = decide_sensor_response(observation, _context())

    assert observation_severity(observation) == "NORMAL"
    assert decision.mitigation.primary is MitigationAction.NONE
    assert decision.mitigation.speed_scale == 1.0


def test_flagged_lidar_observation_reduces_navigation_aggressiveness() -> None:
    monitor = SensorSecurityMonitor(
        "lidar/top",
        SensorKind.LIDAR,
        detector_config_overrides={"warmup": 20, "consecutive": 1},
    )
    observation = monitor.update(_event("lidar/top", innovation=20.0))

    decision = decide_sensor_response(observation, _context())

    assert decision.severity == "WARNING"
    assert MitigationAction.REDUCE_SPEED in decision.mitigation.additional
    assert decision.mitigation.speed_scale == 0.6


def test_triggered_localization_observation_can_request_emergency_stop() -> None:
    monitor = SensorSecurityMonitor(
        "gnss/main",
        SensorKind.GNSS,
        trust_config=TrustConfig(warmup=0),
        detector_config_overrides={"warmup": 0, "cusum_threshold": 0.1},
    )
    observation = monitor.update(_event("gnss/main", innovation=20.0))

    decision = decide_sensor_response(
        observation,
        _context(speed=1.0, obstacle_proximity=0.5),
    )

    assert decision.severity == "CRITICAL"
    assert decision.mitigation.primary is MitigationAction.EMERGENCY_STOP_RECOMMENDATION
    assert decision.mitigation.speed_scale == 0.0


def test_sustained_low_trust_isolates_source_when_redundancy_exists() -> None:
    monitor = SensorSecurityMonitor(
        "lidar/top",
        SensorKind.LIDAR,
        trust_config=TrustConfig(warmup=0, loss_rate=1.0),
        detector_config_overrides={"warmup": 0, "consecutive": 1},
    )
    observation = monitor.update(_event("lidar/top", innovation=20.0))

    decision = decide_sensor_response(observation, _context(), duration=3)

    assert decision.mitigation.isolate_source
    assert MitigationAction.DISABLE_SOURCE in (
        *decision.mitigation.additional,
        decision.mitigation.primary,
    )


def test_duration_must_be_positive() -> None:
    monitor = SensorSecurityMonitor("imu/base", SensorKind.IMU)
    observation = monitor.update(_event("imu/base"))

    with pytest.raises(ValueError, match="duration must be at least 1"):
        decide_sensor_response(observation, _context(), duration=0)
