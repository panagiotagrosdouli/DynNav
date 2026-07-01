"""Safe-mode controller for Contribution 05.

This module implements an auditable finite-state controller for switching
between normal navigation, conservative safe mode, and emergency stop.

Compared with a simple threshold switch, this upgraded controller adds:

- activation persistence,
- deactivation persistence,
- hysteresis,
- cooldown after leaving safe mode,
- emergency-stop handling,
- transition logging,
- summary metrics for experiments.

These mechanisms reduce mode flickering and make safe-mode behaviour easier to
measure in benchmarks.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum


class SafeModeState(str, Enum):
    NORMAL = "NORMAL"
    SAFE_MODE = "SAFE_MODE"
    EMERGENCY_STOP = "EMERGENCY_STOP"


@dataclass(frozen=True)
class SafeModeConfig:
    """Configuration for risk-triggered safe-mode switching."""

    risk_on_threshold: float = 0.70
    risk_off_threshold: float = 0.45
    critical_threshold: float = 0.95
    activation_steps_required: int = 2
    recovery_steps_required: int = 3
    cooldown_steps: int = 2
    normal_speed: float = 1.0
    safe_speed: float = 0.35
    normal_inflation_radius: float = 1.0
    safe_inflation_radius: float = 2.0

    def __post_init__(self) -> None:
        if self.risk_off_threshold >= self.risk_on_threshold:
            raise ValueError("risk_off_threshold must be lower than risk_on_threshold for hysteresis.")
        if self.critical_threshold < self.risk_on_threshold:
            raise ValueError("critical_threshold should be >= risk_on_threshold.")
        if self.activation_steps_required < 1 or self.recovery_steps_required < 1:
            raise ValueError("activation/recovery step requirements must be >= 1.")
        if self.cooldown_steps < 0:
            raise ValueError("cooldown_steps must be >= 0.")


@dataclass(frozen=True)
class SafeModeOutput:
    step: int
    risk: float
    state: SafeModeState
    speed_scale: float
    inflation_radius: float
    should_replan: bool
    alert_operator: bool
    emergency_stop: bool
    activation_counter: int
    recovery_counter: int
    cooldown_remaining: int
    transition: str

    def to_dict(self) -> dict[str, float | int | bool | str]:
        row = asdict(self)
        row["state"] = self.state.value
        return row


class SafeModeController:
    """Risk-triggered safe-mode state machine for navigation.

    State transitions:

    NORMAL -> SAFE_MODE
        risk remains above risk_on_threshold for activation_steps_required steps.

    SAFE_MODE -> NORMAL
        risk remains below risk_off_threshold for recovery_steps_required steps.

    Any state -> EMERGENCY_STOP
        risk exceeds critical_threshold.

    EMERGENCY_STOP -> SAFE_MODE
        risk remains below risk_off_threshold for recovery_steps_required steps.
    """

    def __init__(self, cfg: SafeModeConfig | None = None):
        self.cfg = cfg or SafeModeConfig()
        self.state = SafeModeState.NORMAL
        self.recovery_counter = 0
        self.activation_counter = 0
        self.cooldown_remaining = 0
        self.step_index = 0

    def reset(self) -> None:
        self.state = SafeModeState.NORMAL
        self.recovery_counter = 0
        self.activation_counter = 0
        self.cooldown_remaining = 0
        self.step_index = 0

    def update(self, risk: float) -> SafeModeOutput:
        risk = float(risk)
        prev_state = self.state
        transition = "none"

        if self.cooldown_remaining > 0:
            self.cooldown_remaining -= 1

        if risk >= self.cfg.critical_threshold:
            self.state = SafeModeState.EMERGENCY_STOP
            self.recovery_counter = 0
            self.activation_counter = 0
            transition = f"{prev_state.value}->EMERGENCY_STOP" if prev_state != self.state else "hold_emergency"

        elif self.state == SafeModeState.NORMAL:
            self.recovery_counter = 0
            if risk >= self.cfg.risk_on_threshold and self.cooldown_remaining == 0:
                self.activation_counter += 1
            else:
                self.activation_counter = 0

            if self.activation_counter >= self.cfg.activation_steps_required:
                self.state = SafeModeState.SAFE_MODE
                self.activation_counter = 0
                transition = "NORMAL->SAFE_MODE"

        elif self.state == SafeModeState.SAFE_MODE:
            self.activation_counter = 0
            if risk <= self.cfg.risk_off_threshold:
                self.recovery_counter += 1
            else:
                self.recovery_counter = 0

            if self.recovery_counter >= self.cfg.recovery_steps_required:
                self.state = SafeModeState.NORMAL
                self.recovery_counter = 0
                self.cooldown_remaining = self.cfg.cooldown_steps
                transition = "SAFE_MODE->NORMAL"

        elif self.state == SafeModeState.EMERGENCY_STOP:
            self.activation_counter = 0
            if risk <= self.cfg.risk_off_threshold:
                self.recovery_counter += 1
            else:
                self.recovery_counter = 0

            if self.recovery_counter >= self.cfg.recovery_steps_required:
                self.state = SafeModeState.SAFE_MODE
                self.recovery_counter = 0
                transition = "EMERGENCY_STOP->SAFE_MODE"

        safe_like = self.state in {SafeModeState.SAFE_MODE, SafeModeState.EMERGENCY_STOP}
        speed = 0.0 if self.state == SafeModeState.EMERGENCY_STOP else (
            self.cfg.safe_speed if safe_like else self.cfg.normal_speed
        )
        inflation = self.cfg.safe_inflation_radius if safe_like else self.cfg.normal_inflation_radius
        should_replan = transition in {"NORMAL->SAFE_MODE", "SAFE_MODE->NORMAL", "EMERGENCY_STOP->SAFE_MODE"}
        alert_operator = self.state == SafeModeState.EMERGENCY_STOP

        output = SafeModeOutput(
            step=self.step_index,
            risk=risk,
            state=self.state,
            speed_scale=speed,
            inflation_radius=inflation,
            should_replan=should_replan,
            alert_operator=alert_operator,
            emergency_stop=self.state == SafeModeState.EMERGENCY_STOP,
            activation_counter=self.activation_counter,
            recovery_counter=self.recovery_counter,
            cooldown_remaining=self.cooldown_remaining,
            transition=transition,
        )
        self.step_index += 1
        return output


def summarize_outputs(outputs: list[SafeModeOutput]) -> dict[str, float | int]:
    """Aggregate a controller trace into experiment-level metrics."""
    if not outputs:
        raise ValueError("outputs must not be empty")
    normal_steps = sum(o.state == SafeModeState.NORMAL for o in outputs)
    safe_steps = sum(o.state == SafeModeState.SAFE_MODE for o in outputs)
    emergency_steps = sum(o.state == SafeModeState.EMERGENCY_STOP for o in outputs)
    transitions = sum(o.transition != "none" and not o.transition.startswith("hold") for o in outputs)
    replans = sum(o.should_replan for o in outputs)
    alerts = sum(o.alert_operator for o in outputs)
    return {
        "n_steps": len(outputs),
        "normal_steps": normal_steps,
        "safe_mode_steps": safe_steps,
        "emergency_stop_steps": emergency_steps,
        "transitions": transitions,
        "replans": replans,
        "operator_alerts": alerts,
        "mean_commanded_speed": sum(o.speed_scale for o in outputs) / len(outputs),
        "max_risk": max(o.risk for o in outputs),
        "mean_risk": sum(o.risk for o in outputs) / len(outputs),
    }
