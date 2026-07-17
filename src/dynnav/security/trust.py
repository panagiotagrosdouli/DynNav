"""Source-specific trust estimation with asymmetric degradation and recovery."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .events import DetectorResult, TrustState


@dataclass(frozen=True)
class TrustConfig:
    initial_trust: float = 1.0
    minimum_trust: float = 0.05
    loss_rate: float = 0.35
    recovery_rate: float = 0.03
    evidence_decay: float = 0.98
    stale_penalty: float = 0.1
    recovery_samples: int = 12
    warmup: int = 10


class SourceTrustEstimator:
    def __init__(self, source_id: str, config: TrustConfig | None = None) -> None:
        self.source_id = source_id
        self.config = config or TrustConfig()
        self._trust = self.config.initial_trust
        self._evidence = 0.0
        self._count = 0
        self._anomalies = 0
        self._normal_streak = 0

    def update(self, result: DetectorResult, *, freshness: float = 1.0) -> TrustState:
        if result.source_id != self.source_id:
            raise ValueError(f"expected source {self.source_id!r}, got {result.source_id!r}")
        self._count += 1
        freshness = float(np.clip(freshness, 0.0, 1.0))
        anomaly = float(np.clip(max(result.confidence, float(result.triggered)), 0.0, 1.0))
        self._evidence = self.config.evidence_decay * self._evidence + anomaly
        if result.flagged:
            self._anomalies += 1
            self._normal_streak = 0
            self._trust -= self.config.loss_rate * (0.25 + 0.75 * anomaly)
        else:
            self._normal_streak += 1
            if self._count > self.config.warmup and self._normal_streak >= self.config.recovery_samples:
                self._trust += self.config.recovery_rate * (1.0 - self._trust)
        self._trust -= self.config.stale_penalty * (1.0 - freshness)
        self._trust = float(np.clip(self._trust, self.config.minimum_trust, 1.0))
        instantaneous = float(np.clip(1.0 - anomaly - self.config.stale_penalty * (1.0 - freshness), 0.0, 1.0))
        anomaly_rate = self._anomalies / self._count
        confidence = float(np.clip(1.0 - np.exp(-self._count / 10.0), 0.0, 1.0))
        if self._normal_streak >= self.config.recovery_samples and self._trust < 0.95:
            recovery = "RECOVERING"
        elif result.flagged:
            recovery = "DEGRADING"
        else:
            recovery = "STABLE"
        health = "HEALTHY" if self._trust >= 0.75 else "DEGRADED" if self._trust >= 0.35 else "UNTRUSTED"
        return TrustState(
            source_id=self.source_id,
            instantaneous_trust=instantaneous,
            filtered_trust=self._trust,
            confidence=confidence,
            evidence_count=self._count,
            anomaly_rate=anomaly_rate,
            last_update=result.timestamp,
            recovery_state=recovery,
            health_status=health,
        )

    def reset(self) -> None:
        self._trust = self.config.initial_trust
        self._evidence = 0.0
        self._count = 0
        self._anomalies = 0
        self._normal_streak = 0
