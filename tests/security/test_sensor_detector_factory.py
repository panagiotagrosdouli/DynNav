"""Tests for profile-driven detector construction."""

import pytest

from dynnav.security import CUSUMDetector, EWMADetector, NISDetector, create_sensor_detector


def test_gnss_uses_profile_preferred_detector() -> None:
    detector = create_sensor_detector("gnss")

    assert isinstance(detector, CUSUMDetector)
    assert detector.config.warmup == 10
    assert detector.config.cusum_threshold == 3.5


def test_camera_uses_ewma_profile() -> None:
    detector = create_sensor_detector("camera")

    assert isinstance(detector, EWMADetector)
    assert detector.config.ewma_factor == 0.25


def test_detector_name_and_config_can_be_overridden() -> None:
    detector = create_sensor_detector(
        "imu",
        detector_name="nis",
        config_overrides={"warmup": 2, "alpha": 0.001},
    )

    assert isinstance(detector, NISDetector)
    assert detector.config.warmup == 2
    assert detector.config.alpha == 0.001


def test_unknown_config_override_fails_fast() -> None:
    with pytest.raises(TypeError):
        create_sensor_detector("lidar", config_overrides={"not_a_field": 1})
