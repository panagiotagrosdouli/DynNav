"""Sensor-specific anomaly profiles for interpretable IDS configuration."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .detectors import DetectorConfig


class SensorKind(str, Enum):
    GNSS = "gnss"
    LIDAR = "lidar"
    CAMERA = "camera"
    IMU = "imu"
    WHEEL_ODOMETRY = "wheel_odometry"


@dataclass(frozen=True)
class SensorSecurityProfile:
    sensor: SensorKind
    preferred_detector: str
    detector_config: DetectorConfig
    expected_attack_modes: tuple[str, ...]
    evidence_keys: tuple[str, ...]
    mitigation_priority: tuple[str, ...]


_PROFILES: dict[SensorKind, SensorSecurityProfile] = {
    SensorKind.GNSS: SensorSecurityProfile(
        sensor=SensorKind.GNSS,
        preferred_detector="cusum",
        detector_config=DetectorConfig(warmup=10, cusum_drift=0.15, cusum_threshold=3.5),
        expected_attack_modes=("spoofing", "meaconing", "replay", "jamming"),
        evidence_keys=("position_jump", "clock_bias", "freshness", "cross_sensor_disagreement"),
        mitigation_priority=("reject_measurement", "switch_estimator", "relocalize", "reduce_speed"),
    ),
    SensorKind.LIDAR: SensorSecurityProfile(
        sensor=SensorKind.LIDAR,
        preferred_detector="nis",
        detector_config=DetectorConfig(alpha=0.005, warmup=12, consecutive=2),
        expected_attack_modes=("point_injection", "point_removal", "occlusion", "degradation"),
        evidence_keys=("scan_density", "range_distribution", "map_inconsistency", "freshness"),
        mitigation_priority=("reject_measurement", "increase_uncertainty", "replan", "reduce_speed"),
    ),
    SensorKind.CAMERA: SensorSecurityProfile(
        sensor=SensorKind.CAMERA,
        preferred_detector="ewma",
        detector_config=DetectorConfig(warmup=15, ewma_factor=0.25, ewma_threshold=2.2),
        expected_attack_modes=("blinding", "replay", "adversarial_pattern", "frame_injection"),
        evidence_keys=("feature_count", "frame_hash", "exposure_shift", "cross_sensor_disagreement"),
        mitigation_priority=("reject_measurement", "increase_uncertainty", "switch_estimator", "reduce_speed"),
    ),
    SensorKind.IMU: SensorSecurityProfile(
        sensor=SensorKind.IMU,
        preferred_detector="cusum",
        detector_config=DetectorConfig(warmup=20, cusum_drift=0.1, cusum_threshold=3.0),
        expected_attack_modes=("bias_injection", "scale_factor", "replay", "saturation"),
        evidence_keys=("bias_drift", "saturation", "freshness", "kinematic_inconsistency"),
        mitigation_priority=("switch_estimator", "increase_uncertainty", "reduce_speed", "safe_stop"),
    ),
    SensorKind.WHEEL_ODOMETRY: SensorSecurityProfile(
        sensor=SensorKind.WHEEL_ODOMETRY,
        preferred_detector="kofn",
        detector_config=DetectorConfig(alpha=0.01, warmup=10, k=3, n=5),
        expected_attack_modes=("scale_manipulation", "replay", "dropout", "slip_masquerading"),
        evidence_keys=("velocity_ratio", "sequence_gap", "freshness", "kinematic_inconsistency"),
        mitigation_priority=("reject_measurement", "switch_estimator", "reduce_speed", "relocalize"),
    ),
}


def get_sensor_profile(sensor: SensorKind | str) -> SensorSecurityProfile:
    """Return an immutable profile, accepting canonical string names."""
    try:
        key = sensor if isinstance(sensor, SensorKind) else SensorKind(sensor.lower())
    except ValueError as exc:
        available = ", ".join(item.value for item in SensorKind)
        raise ValueError(f"unknown sensor {sensor!r}; available={available}") from exc
    return _PROFILES[key]


def available_sensor_profiles() -> tuple[SensorKind, ...]:
    """List supported sensor kinds in deterministic order."""
    return tuple(SensorKind)
