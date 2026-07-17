import pytest

from dynnav.security.sensor_profiles import (
    SensorKind,
    available_sensor_profiles,
    get_sensor_profile,
)


def test_all_supported_sensor_profiles_are_available() -> None:
    assert available_sensor_profiles() == tuple(SensorKind)


def test_gnss_profile_prioritizes_spoofing_detection() -> None:
    profile = get_sensor_profile("gnss")

    assert profile.sensor is SensorKind.GNSS
    assert profile.preferred_detector == "cusum"
    assert "spoofing" in profile.expected_attack_modes
    assert profile.mitigation_priority[0] == "reject_measurement"


def test_lidar_profile_uses_strict_nis_threshold() -> None:
    profile = get_sensor_profile(SensorKind.LIDAR)

    assert profile.preferred_detector == "nis"
    assert profile.detector_config.alpha == pytest.approx(0.005)
    assert "map_inconsistency" in profile.evidence_keys


def test_imu_profile_tracks_bias_and_saturation() -> None:
    profile = get_sensor_profile("imu")

    assert {"bias_injection", "saturation"}.issubset(profile.expected_attack_modes)
    assert {"bias_drift", "saturation"}.issubset(profile.evidence_keys)


def test_unknown_sensor_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown sensor"):
        get_sensor_profile("radar")
