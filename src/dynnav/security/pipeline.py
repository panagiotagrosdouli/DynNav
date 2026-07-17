"""Profile-driven sensor anomaly detection and trust updates."""

from __future__ import annotations

from dataclasses import dataclass

from .detectors import Detector
from .events import DetectorResult, ResidualEvent, TrustState
from .sensor_profiles import SensorKind, SensorSecurityProfile, create_sensor_detector, get_sensor_profile
from .trust import SourceTrustEstimator, TrustConfig


@dataclass(frozen=True)
class SensorSecurityObservation:
    """Atomic output from one detector and trust-estimator update."""

    sensor: SensorKind
    detector_result: DetectorResult
    trust_state: TrustState
    mitigation_priority: tuple[str, ...]


class SensorSecurityMonitor:
    """Bind a sensor profile, anomaly detector, and source trust estimator.

    The monitor is intentionally source-specific. A residual event from another
    source is rejected so detector state and trust history cannot be mixed
    accidentally across sensors.
    """

    def __init__(
        self,
        source_id: str,
        sensor: SensorKind | str,
        *,
        trust_config: TrustConfig | None = None,
        detector_name: str | None = None,
        detector_config_overrides: dict[str, float | int] | None = None,
    ) -> None:
        if not source_id:
            raise ValueError("source_id must be non-empty")
        self.source_id = source_id
        self.profile: SensorSecurityProfile = get_sensor_profile(sensor)
        self.detector: Detector = create_sensor_detector(
            self.profile.sensor,
            detector_name=detector_name,
            config_overrides=detector_config_overrides,
        )
        self.trust_estimator = SourceTrustEstimator(source_id, trust_config)

    def update(self, event: ResidualEvent) -> SensorSecurityObservation:
        """Process one residual event and update source trust atomically."""
        if event.source_id != self.source_id:
            raise ValueError(f"expected source {self.source_id!r}, got {event.source_id!r}")
        result = self.detector.update(event)
        trust = self.trust_estimator.update(result, freshness=event.freshness)
        return SensorSecurityObservation(
            sensor=self.profile.sensor,
            detector_result=result,
            trust_state=trust,
            mitigation_priority=self.profile.mitigation_priority,
        )

    def reset_trust(self) -> None:
        """Reset trust history while preserving detector state."""
        self.trust_estimator.reset()
