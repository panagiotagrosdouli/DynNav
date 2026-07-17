"""Detector registry and stateful residual detectors."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Protocol

import numpy as np

from .events import DetectorResult, ResidualEvent
from .statistics import chi_square_quantile, mahalanobis_squared


class Detector(Protocol):
    name: str

    def update(self, event: ResidualEvent) -> DetectorResult: ...


@dataclass(frozen=True)
class DetectorConfig:
    alpha: float = 0.01
    warmup: int = 20
    consecutive: int = 3
    k: int = 3
    n: int = 10
    cusum_drift: float = 0.25
    cusum_threshold: float = 5.0
    ewma_factor: float = 0.2
    ewma_threshold: float = 2.5


class NISDetector:
    name = "normalized_innovation_squared"

    def __init__(self, config: DetectorConfig | None = None, *, trigger_policy: str = "consecutive") -> None:
        self.config = config or DetectorConfig()
        self.trigger_policy = trigger_policy
        self._count = 0
        self._streak = 0
        self._flags: deque[bool] = deque(maxlen=self.config.n)
        self._first_flag: int | None = None

    def update(self, event: ResidualEvent) -> DetectorResult:
        self._count += 1
        statistic, covariance = mahalanobis_squared(event.innovation, event.covariance)
        threshold = chi_square_quantile(self.config.alpha, event.innovation.size)
        flagged = statistic > threshold
        self._streak = self._streak + 1 if flagged else 0
        self._flags.append(flagged)
        if flagged and self._first_flag is None:
            self._first_flag = self._count
        triggered = False
        if self._count > self.config.warmup:
            if self.trigger_policy == "consecutive":
                triggered = self._streak >= self.config.consecutive
            elif self.trigger_policy == "kofn":
                triggered = len(self._flags) == self.config.n and sum(self._flags) >= self.config.k
            else:
                raise ValueError(f"unknown trigger policy: {self.trigger_policy}")
        confidence = float(np.clip((statistic / max(threshold, 1e-12) - 1.0) / 3.0, 0.0, 1.0))
        return DetectorResult(
            statistic=statistic,
            threshold=threshold,
            flagged=flagged,
            triggered=triggered,
            confidence=confidence,
            latency=None if self._first_flag is None else self._count - self._first_flag,
            detector_name=self.name,
            source_id=event.source_id,
            timestamp=event.timestamp,
            diagnostics={
                "streak": self._streak,
                "kofn_sum": int(sum(self._flags)),
                "covariance": covariance.__dict__,
            },
        )


class CUSUMDetector:
    name = "two_sided_cusum"

    def __init__(self, config: DetectorConfig | None = None) -> None:
        self.config = config or DetectorConfig()
        self._positive = 0.0
        self._negative = 0.0
        self._count = 0
        self._first_flag: int | None = None

    def update(self, event: ResidualEvent) -> DetectorResult:
        self._count += 1
        nis, covariance = mahalanobis_squared(event.innovation, event.covariance)
        normalized = nis / max(1, event.innovation.size) - 1.0
        self._positive = max(0.0, self._positive + normalized - self.config.cusum_drift)
        self._negative = min(0.0, self._negative + normalized + self.config.cusum_drift)
        statistic = max(self._positive, abs(self._negative))
        flagged = statistic > self.config.cusum_threshold
        if flagged and self._first_flag is None:
            self._first_flag = self._count
        return DetectorResult(
            statistic=statistic,
            threshold=self.config.cusum_threshold,
            flagged=flagged,
            triggered=flagged and self._count > self.config.warmup,
            confidence=float(np.clip(statistic / max(self.config.cusum_threshold, 1e-12) - 1.0, 0.0, 1.0)),
            latency=None if self._first_flag is None else self._count - self._first_flag,
            detector_name=self.name,
            source_id=event.source_id,
            timestamp=event.timestamp,
            diagnostics={"positive": self._positive, "negative": self._negative, "covariance": covariance.__dict__},
        )


class EWMADetector:
    name = "ewma_nis"

    def __init__(self, config: DetectorConfig | None = None) -> None:
        self.config = config or DetectorConfig()
        if not 0.0 < self.config.ewma_factor <= 1.0:
            raise ValueError("ewma_factor must be in (0, 1]")
        self._value = 1.0
        self._count = 0

    def update(self, event: ResidualEvent) -> DetectorResult:
        self._count += 1
        nis, covariance = mahalanobis_squared(event.innovation, event.covariance)
        normalized = nis / max(1, event.innovation.size)
        factor = self.config.ewma_factor
        self._value = factor * normalized + (1.0 - factor) * self._value
        flagged = self._value > self.config.ewma_threshold
        return DetectorResult(
            statistic=self._value,
            threshold=self.config.ewma_threshold,
            flagged=flagged,
            triggered=flagged and self._count > self.config.warmup,
            confidence=float(np.clip(self._value / self.config.ewma_threshold - 1.0, 0.0, 1.0)),
            latency=None,
            detector_name=self.name,
            source_id=event.source_id,
            timestamp=event.timestamp,
            diagnostics={"instantaneous_nis": normalized, "covariance": covariance.__dict__},
        )


DETECTOR_REGISTRY: dict[str, type[NISDetector] | type[CUSUMDetector] | type[EWMADetector]] = {
    "nis": NISDetector,
    "chi_square": NISDetector,
    "consecutive": NISDetector,
    "kofn": NISDetector,
    "cusum": CUSUMDetector,
    "ewma": EWMADetector,
}


def create_detector(name: str, config: DetectorConfig | None = None) -> Detector:
    key = name.lower()
    if key not in DETECTOR_REGISTRY:
        raise ValueError(f"unknown detector {name!r}; available={sorted(DETECTOR_REGISTRY)}")
    if key == "kofn":
        return NISDetector(config, trigger_policy="kofn")
    return DETECTOR_REGISTRY[key](config)
