"""Security supervision state machine with dwell times and hysteresis."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SecurityState(str, Enum):
    NORMAL = "NORMAL"
    OBSERVING = "OBSERVING"
    SUSPICIOUS = "SUSPICIOUS"
    DEGRADED_TRUST = "DEGRADED_TRUST"
    ATTACK_LIKELY = "ATTACK_LIKELY"
    SOURCE_ISOLATED = "SOURCE_ISOLATED"
    RECOVERY_MONITORING = "RECOVERY_MONITORING"
    SAFE_MODE = "SAFE_MODE"
    SAFE_STOP = "SAFE_STOP"
    EMERGENCY_STOP_RECOMMENDED = "EMERGENCY_STOP_RECOMMENDED"
    MISSION_ABORT_RECOMMENDED = "MISSION_ABORT_RECOMMENDED"


@dataclass(frozen=True)
class StateTransition:
    previous: SecurityState
    current: SecurityState
    reason: str
    timestamp: float
    dwell_updates: int


@dataclass(frozen=True)
class StateMachineConfig:
    suspicious_trust: float = 0.7
    degraded_trust: float = 0.5
    recovery_trust: float = 0.8
    attack_dwell: int = 3
    recovery_dwell: int = 5


class SecurityStateMachine:
    def __init__(self, config: StateMachineConfig | None = None):
        self.config = config or StateMachineConfig()
        self.state = SecurityState.NORMAL
        self._dwell = 0
        self._recovery = 0

    def update(self, *, timestamp: float, triggered: bool, trust: float, attribution_confidence: float,
               isolated: bool = False, critical_context: bool = False, recovery_possible: bool = True) -> StateTransition:
        previous = self.state
        self._dwell = self._dwell + 1 if triggered else 0
        self._recovery = self._recovery + 1 if not triggered and trust >= self.config.recovery_trust else 0
        reason = "state retained by hysteresis"

        if critical_context and triggered and not recovery_possible:
            self.state = SecurityState.EMERGENCY_STOP_RECOMMENDED
            reason = "critical context, active trigger, and no recovery path"
        elif isolated:
            self.state = SecurityState.SOURCE_ISOLATED
            reason = "affected source has been isolated"
        elif triggered and attribution_confidence >= 0.65 and self._dwell >= self.config.attack_dwell:
            self.state = SecurityState.ATTACK_LIKELY
            reason = "persistent detector trigger with supported attribution"
        elif triggered and trust < self.config.degraded_trust:
            self.state = SecurityState.DEGRADED_TRUST
            reason = "detector trigger coincides with low source trust"
        elif triggered:
            self.state = SecurityState.SUSPICIOUS
            reason = "temporal detector trigger is active"
        elif trust < self.config.suspicious_trust:
            self.state = SecurityState.OBSERVING
            reason = "trust is reduced without a persistent trigger"
        elif previous in {SecurityState.SOURCE_ISOLATED, SecurityState.ATTACK_LIKELY, SecurityState.DEGRADED_TRUST}:
            self.state = SecurityState.RECOVERY_MONITORING
            reason = "anomaly cleared; recovery evidence is being accumulated"
        elif previous is SecurityState.RECOVERY_MONITORING and self._recovery < self.config.recovery_dwell:
            self.state = SecurityState.RECOVERY_MONITORING
            reason = "recovery dwell requirement has not yet been met"
        elif self._recovery >= self.config.recovery_dwell or previous in {SecurityState.NORMAL, SecurityState.OBSERVING}:
            self.state = SecurityState.NORMAL
            reason = "nominal trust and recovery dwell requirements are satisfied"

        return StateTransition(previous, self.state, reason, timestamp, max(self._dwell, self._recovery))
