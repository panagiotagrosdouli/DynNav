from __future__ import annotations

import numpy as np
import pytest

from dynnav.security import ResidualEvent, SensorKind, SensorSecurityMonitor, TrustConfig


def _event(source_id: str, *, innovation: float = 0.0, freshness: float = 1.0) -> ResidualEvent:
    measurement = np.array([innovation], dtype=float)
    prediction = np.zeros(1, dtype=float)
    return ResidualEvent(
        source_id=source_id,
        measurement=measurement,
        prediction=prediction,
        innovation=measurement - prediction,
        covariance=np.eye(1, dtype=float),
        timestamp=1.0,
        freshness=freshness,
    )


def test_monitor_uses_sensor_profile_detector_and_metadata() -> None:
    monitor = SensorSecurityMonitor("camera/front", SensorKind.CAMERA)

    observation = monitor.update(_event("camera/front"))

    assert observation.sensor is SensorKind.CAMERA
    assert observation.detector_result.detector_name == "ewma_nis"
    assert observation.trust_state.source_id == "camera/front"
    assert observation.mitigation_priority[0] == "reject_measurement"


def test_flagged_measurement_degrades_source_trust() -> None:
    monitor = SensorSecurityMonitor(
        "lidar/top",
        SensorKind.LIDAR,
        trust_config=TrustConfig(warmup=0),
        detector_config_overrides={"warmup": 0, "consecutive": 1},
    )

    observation = monitor.update(_event("lidar/top", innovation=20.0))

    assert observation.detector_result.flagged
    assert observation.trust_state.filtered_trust < 1.0
    assert observation.trust_state.recovery_state == "DEGRADING"


def test_event_freshness_penalizes_trust() -> None:
    monitor = SensorSecurityMonitor("imu/base", SensorKind.IMU)

    observation = monitor.update(_event("imu/base", freshness=0.0))

    assert observation.trust_state.filtered_trust < 1.0
    assert observation.trust_state.instantaneous_trust < 1.0


def test_monitor_rejects_cross_source_events() -> None:
    monitor = SensorSecurityMonitor("gnss/main", SensorKind.GNSS)

    with pytest.raises(ValueError, match="expected source"):
        monitor.update(_event("gnss/backup"))


def test_monitor_requires_non_empty_source_id() -> None:
    with pytest.raises(ValueError, match="source_id must be non-empty"):
        SensorSecurityMonitor("", SensorKind.GNSS)
