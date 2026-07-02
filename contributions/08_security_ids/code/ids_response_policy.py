"""IDS response policy for Contribution 08.

The existing security monitor detects innovation anomalies. This module converts
IDS outputs into navigation-facing trust and mitigation decisions.

The goal is to close the loop:

    innovation anomaly -> alert severity -> trust score -> planner mitigation

This makes the IDS useful for navigation instead of only producing a diagnostic
flag.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Mapping


class AlertSeverity(str, Enum):
    NORMAL = "NORMAL"
    WATCH = "WATCH"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class PlannerMitigation(str, Enum):
    NONE = "NONE"
    INCREASE_CAUTION = "INCREASE_CAUTION"
    SAFE_MODE = "SAFE_MODE"
    EMERGENCY_STOP = "EMERGENCY_STOP"


@dataclass(frozen=True)
class IDSResponseConfig:
    watch_ratio: float = 0.60
    warning_ratio: float = 1.00
    critical_ratio: float = 2.50
    high_flag_rate: float = 0.25
    critical_streak: int = 5


@dataclass(frozen=True)
class IDSResponse:
    severity: AlertSeverity
    mitigation: PlannerMitigation
    trust_score: float
    d2_ratio: float
    flag_rate: float
    triggered: bool
    explanation: str

    def to_dict(self) -> dict[str, float | bool | str]:
        row = asdict(self)
        row["severity"] = self.severity.value
        row["mitigation"] = self.mitigation.value
        return row


def compute_trust_score(d2_ratio: float, flag_rate: float, triggered: bool) -> float:
    """Map anomaly evidence into a [0, 1] trust score."""
    ratio_penalty = min(0.60, max(0.0, d2_ratio - 1.0) * 0.25)
    flag_penalty = min(0.30, max(0.0, flag_rate) * 0.75)
    trigger_penalty = 0.25 if triggered else 0.0
    return max(0.0, min(1.0, 1.0 - ratio_penalty - flag_penalty - trigger_penalty))


def classify_ids_response(monitor_output: Mapping[str, float | int | bool], cfg: IDSResponseConfig | None = None) -> IDSResponse:
    cfg = cfg or IDSResponseConfig()
    d2 = float(monitor_output.get("d2", 0.0))
    thr = max(float(monitor_output.get("thr", 1.0)), 1e-9)
    flag_rate = float(monitor_output.get("flag_rate", 0.0))
    triggered = bool(monitor_output.get("triggered", False))
    streak = int(monitor_output.get("streak", 0))
    ratio = d2 / thr

    if ratio >= cfg.critical_ratio or streak >= cfg.critical_streak:
        severity = AlertSeverity.CRITICAL
        mitigation = PlannerMitigation.EMERGENCY_STOP
        explanation = "innovation evidence is critical; stop or hand control to safety layer"
    elif triggered or ratio >= cfg.warning_ratio or flag_rate >= cfg.high_flag_rate:
        severity = AlertSeverity.WARNING
        mitigation = PlannerMitigation.SAFE_MODE
        explanation = "IDS trigger or high anomaly evidence; switch navigation to safe mode"
    elif ratio >= cfg.watch_ratio:
        severity = AlertSeverity.WATCH
        mitigation = PlannerMitigation.INCREASE_CAUTION
        explanation = "innovation is elevated; increase caution and monitor trend"
    else:
        severity = AlertSeverity.NORMAL
        mitigation = PlannerMitigation.NONE
        explanation = "innovation evidence is within expected range"

    return IDSResponse(
        severity=severity,
        mitigation=mitigation,
        trust_score=compute_trust_score(ratio, flag_rate, triggered),
        d2_ratio=float(ratio),
        flag_rate=flag_rate,
        triggered=triggered,
        explanation=explanation,
    )
