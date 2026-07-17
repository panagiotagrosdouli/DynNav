"""Deterministic alert correlation for cyber-physical attack campaigns.

The correlator is intentionally transparent: it groups temporally adjacent
alerts, preserves their provenance, and reports the strongest plausible attack
chain without claiming proof of malicious intent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class SecurityAlert:
    """Normalized alert consumed by the campaign correlator."""

    source_id: str
    alert_type: str
    timestamp: float
    confidence: float
    severity: float
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class CampaignLink:
    """Directed relation between two alerts in a candidate campaign."""

    predecessor: SecurityAlert
    successor: SecurityAlert
    score: float
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class AttackCampaign:
    """Correlated alert chain with an auditable aggregate score."""

    alerts: tuple[SecurityAlert, ...]
    links: tuple[CampaignLink, ...]
    score: float
    sources: tuple[str, ...]
    attack_types: tuple[str, ...]


class CampaignCorrelator:
    """Build attack campaigns from ordered alerts using explicit rules."""

    def __init__(self, max_gap: float = 5.0, minimum_link_score: float = 0.35) -> None:
        if max_gap <= 0.0:
            raise ValueError("max_gap must be positive")
        if not 0.0 <= minimum_link_score <= 1.0:
            raise ValueError("minimum_link_score must be in [0, 1]")
        self.max_gap = float(max_gap)
        self.minimum_link_score = float(minimum_link_score)

    @staticmethod
    def _clip(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    def _link(self, previous: SecurityAlert, current: SecurityAlert) -> CampaignLink | None:
        gap = current.timestamp - previous.timestamp
        if gap < 0.0 or gap > self.max_gap:
            return None

        reasons: list[str] = []
        temporal_score = 1.0 - gap / self.max_gap
        score = 0.35 * temporal_score

        if previous.source_id == current.source_id:
            score += 0.25
            reasons.append("same_source")
        else:
            score += 0.10
            reasons.append("cross_source")

        if previous.alert_type == current.alert_type:
            score += 0.20
            reasons.append("same_attack_type")
        else:
            reasons.append("multi_stage_pattern")

        evidence_overlap = set(previous.evidence).intersection(current.evidence)
        if evidence_overlap:
            score += 0.10
            reasons.append("shared_evidence")

        score += 0.10 * min(self._clip(previous.confidence), self._clip(current.confidence))
        score = self._clip(score)
        if score < self.minimum_link_score:
            return None
        return CampaignLink(previous, current, score, tuple(reasons))

    def correlate(self, alerts: Iterable[SecurityAlert]) -> tuple[AttackCampaign, ...]:
        ordered = sorted(alerts, key=lambda item: (item.timestamp, item.source_id, item.alert_type))
        if not ordered:
            return ()

        campaigns: list[list[SecurityAlert]] = [[ordered[0]]]
        campaign_links: list[list[CampaignLink]] = [[]]

        for alert in ordered[1:]:
            link = self._link(campaigns[-1][-1], alert)
            if link is None:
                campaigns.append([alert])
                campaign_links.append([])
            else:
                campaigns[-1].append(alert)
                campaign_links[-1].append(link)

        results: list[AttackCampaign] = []
        for grouped_alerts, links in zip(campaigns, campaign_links, strict=True):
            confidence = sum(self._clip(item.confidence) for item in grouped_alerts) / len(grouped_alerts)
            severity = max(self._clip(item.severity) for item in grouped_alerts)
            continuity = sum(link.score for link in links) / len(links) if links else 0.0
            score = self._clip(0.45 * confidence + 0.35 * severity + 0.20 * continuity)
            results.append(
                AttackCampaign(
                    alerts=tuple(grouped_alerts),
                    links=tuple(links),
                    score=score,
                    sources=tuple(sorted({item.source_id for item in grouped_alerts})),
                    attack_types=tuple(sorted({item.alert_type for item in grouped_alerts})),
                )
            )
        return tuple(results)
