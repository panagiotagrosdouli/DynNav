"""Transparent rule-based attack and fault attribution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .events import AttributionResult, DetectorResult, TrustState


@dataclass(frozen=True)
class AttributionEvidence:
    source_id: str
    trend: str = "unknown"
    cross_sensor_consistent: bool | None = None
    repeated_payload: bool = False
    stale_or_delayed: bool = False
    covariance_anomalous: bool = False
    map_inconsistent: bool = False
    packet_injection_evidence: bool = False
    duration: int = 0


def attribute_anomaly(
    detector: DetectorResult,
    trust: TrustState,
    evidence: AttributionEvidence,
    alternatives: Sequence[str] = (),
) -> AttributionResult:
    support: list[str] = []
    contradict: list[str] = []
    scores: dict[str, float] = {
        "unknown anomaly": 0.20,
        "random noise": 0.0,
        "sensor drift": 0.0,
        "calibration fault": 0.0,
        "GPS spoofing": 0.0,
        "replay": 0.0,
        "LiDAR corruption": 0.0,
        "localization inconsistency": 0.0,
        "map tampering": 0.0,
        "communication injection": 0.0,
    }

    if not detector.triggered and detector.flagged and evidence.duration <= 1:
        scores["random noise"] += 0.65
        support.append("isolated threshold violation without temporal trigger")
    if evidence.trend in {"ramp", "monotonic"} and evidence.duration >= 3:
        scores["sensor drift"] += 0.55
        support.append("sustained monotonic innovation trend")
    if evidence.trend == "constant_bias" and evidence.duration >= 3:
        scores["calibration fault"] += 0.45
        support.append("persistent approximately constant residual bias")
    if evidence.repeated_payload:
        scores["replay"] += 0.80
        support.append("repeated measurement payload or sequence pattern")
    if evidence.covariance_anomalous:
        scores["localization inconsistency"] += 0.55
        support.append("reported covariance is inconsistent or manipulated")
    if evidence.map_inconsistent:
        scores["map tampering"] += 0.80
        support.append("map observations conflict with independent spatial evidence")
    if evidence.packet_injection_evidence:
        scores["communication injection"] += 0.85
        support.append("unexpected packet or peer contribution was observed")
    if evidence.source_id.lower().startswith("gps") and evidence.cross_sensor_consistent is False:
        scores["GPS spoofing"] += 0.75
        support.append("GPS disagrees while odometry/IMU evidence remains consistent")
    if "lidar" in evidence.source_id.lower() and evidence.cross_sensor_consistent is False:
        scores["LiDAR corruption"] += 0.70
        support.append("LiDAR-derived evidence disagrees with independent sources")
    if evidence.stale_or_delayed:
        scores["replay"] += 0.35
        support.append("source freshness or packet timing is abnormal")
    if trust.filtered_trust > 0.8:
        contradict.append("source trust remains high")
    if detector.confidence < 0.5:
        contradict.append("detector confidence is limited")

    likely = max(scores, key=scores.get)
    raw = scores[likely]
    confidence = max(0.0, min(0.95, raw * detector.confidence + 0.15 * (1.0 - trust.filtered_trust)))
    ranked = tuple(name for name, _ in sorted(scores.items(), key=lambda item: item[1], reverse=True)[1:3])
    merged_alternatives = tuple(dict.fromkeys((*ranked, *alternatives)))
    return AttributionResult(
        likely_cause=likely,
        confidence=confidence,
        supporting_evidence=tuple(support) or ("anomaly evidence is insufficient for specific attribution",),
        contradictory_evidence=tuple(contradict),
        alternative_causes=merged_alternatives,
    )
