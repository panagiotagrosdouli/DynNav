from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SafeModeState(str, Enum):
    NORMAL = "NORMAL"
    SAFE_MODE = "SAFE_MODE"
    EMERGENCY_STOP = "EMERGENCY_STOP"


@dataclass
class SafeModeConfig:
    risk_on_threshold: float = 0.70
    risk_off_threshold: float = 0.45
    critical_threshold: float = 0.95
    recovery_steps_required: int = 3
    normal_speed: float = 1.0
    safe_speed: float = 0.35
    normal_inflation_radius: float = 1.0
    safe_inflation_radius: float = 2.0


@dataclass
class SafeModeOutput:
    state: SafeModeState
    speed_scale: float
    inflation_radius: float
    should_replan: bool
    alert_operator: bool
    recovery_counter: int


class SafeModeController:
    """Risk-triggered safe-mode state machine for navigation.

    NORMAL -> SAFE_MODE when risk exceeds risk_on_threshold.
    SAFE_MODE -> NORMAL after risk remains below risk_off_threshold for N steps.
    Any state -> EMERGENCY_STOP when risk exceeds critical_threshold.
    """

    def __init__(self, cfg: SafeModeConfig | None = None):
        self.cfg = cfg or SafeModeConfig()
        self.state = SafeModeState.NORMAL
        self.recovery_counter = 0

    def reset(self) -> None:
        self.state = SafeModeState.NORMAL
        self.recovery_counter = 0

    def update(self, risk: float) -> SafeModeOutput:
        risk = float(risk)
        prev_state = self.state

        if risk >= self.cfg.critical_threshold:
            self.state = SafeModeState.EMERGENCY_STOP
            self.recovery_counter = 0
        elif self.state == SafeModeState.NORMAL:
            if risk >= self.cfg.risk_on_threshold:
                self.state = SafeModeState.SAFE_MODE
                self.recovery_counter = 0
        elif self.state == SafeModeState.SAFE_MODE:
            if risk <= self.cfg.risk_off_threshold:
                self.recovery_counter += 1
                if self.recovery_counter >= self.cfg.recovery_steps_required:
                    self.state = SafeModeState.NORMAL
                    self.recovery_counter = 0
            else:
                self.recovery_counter = 0
        elif self.state == SafeModeState.EMERGENCY_STOP:
            if risk <= self.cfg.risk_off_threshold:
                self.recovery_counter += 1
                if self.recovery_counter >= self.cfg.recovery_steps_required:
                    self.state = SafeModeState.SAFE_MODE
                    self.recovery_counter = 0
            else:
                self.recovery_counter = 0

        safe_like = self.state in {SafeModeState.SAFE_MODE, SafeModeState.EMERGENCY_STOP}
        speed = 0.0 if self.state == SafeModeState.EMERGENCY_STOP else (
            self.cfg.safe_speed if safe_like else self.cfg.normal_speed
        )
        inflation = self.cfg.safe_inflation_radius if safe_like else self.cfg.normal_inflation_radius
        should_replan = self.state != prev_state or self.state == SafeModeState.SAFE_MODE
        alert_operator = self.state == SafeModeState.EMERGENCY_STOP

        return SafeModeOutput(
            state=self.state,
            speed_scale=speed,
            inflation_radius=inflation,
            should_replan=should_replan,
            alert_operator=alert_operator,
            recovery_counter=self.recovery_counter,
        )
