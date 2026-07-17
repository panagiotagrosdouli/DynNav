"""Typed records shared by DynNav's research-grade security pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass(frozen=True)
class ResidualEvent:
    source_id: str
    measurement: np.ndarray
    prediction: np.ndarray
    innovation: np.ndarray
    covariance: np.ndarray
    timestamp: float
    frame: str = ""
    sequence_number: int = 0
    valid: bool = True
    freshness: float = 1.0


@dataclass(frozen=True)
class DetectorResult:
    statistic: float
    threshold: float
    flagged: bool
    triggered: bool
    confidence: float
    latency: int | None
    detector_name: str
    source_id: str
    timestamp: float
    diagnostics: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TrustState:
    source_id: str
    instantaneous_trust: float
    filtered_trust: float
    confidence: float
    evidence_count: int
    anomaly_rate: float
    last_update: float
    recovery_state: str
    health_status: str


@dataclass(frozen=True)
class AttributionResult:
    likely_cause: str
    confidence: float
    supporting_evidence: tuple[str, ...]
    contradictory_evidence: tuple[str, ...] = ()
    alternative_causes: tuple[str, ...] = ()
