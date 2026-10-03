"""V4 hidden-arming contracts for Gazebo/ROS execution benchmarks.

This module is ROS-independent by design so the information barrier can be
unit-tested without launching Gazebo.  A non-oracle planner receives only a
noisy detector message and declared model parameters.  Latent arming truth and
future closure truth remain benchmark-controller state.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class V4ArmingModel:
    arming_probability: float
    detection_sensitivity: float
    detection_specificity: float
    closure_probability_given_armed: float

    def validate(self) -> None:
        for name, value in (
            ("arming_probability", self.arming_probability),
            ("detection_sensitivity", self.detection_sensitivity),
            ("detection_specificity", self.detection_specificity),
            (
                "closure_probability_given_armed",
                self.closure_probability_given_armed,
            ),
        ):
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class PlannerArmingObservation:
    """Information exposed to non-oracle planners after trigger execution."""

    hazard_id: str
    observed_armed: bool
    arming_probability: float
    detection_sensitivity: float
    detection_specificity: float
    closure_probability_given_armed: float


@dataclass(frozen=True, slots=True)
class OracleArmingObservation:
    """Explicit oracle-only payload. Never publish this to ordinary planners."""

    hazard_id: str
    true_armed: bool
    closure_probability_given_armed: float


@dataclass(frozen=True, slots=True)
class HiddenArmingOutcome:
    """Benchmark-controller truth plus the blinded planner observation."""

    hazard_id: str
    true_armed: bool
    detector_message: PlannerArmingObservation
    future_closure_realized: bool


def keyed_v4_draw(
    seed: int,
    scenario: str,
    repetition: int,
    hazard_id: str,
    event_type: str,
    occurrence: int = 0,
) -> float:
    if not hazard_id:
        raise ValueError("hazard_id must be non-empty")
    if event_type not in {"arming", "observation", "closure"}:
        raise ValueError("unsupported V4 event_type")
    if occurrence < 0:
        raise ValueError("occurrence must be non-negative")
    payload = (
        f"{seed}|{scenario}|{repetition}|{hazard_id}|"
        f"{event_type}|{occurrence}"
    ).encode()
    integer = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
    return integer / float(1 << 64)


def sample_hidden_arming_after_executed_trigger(
    *,
    seed: int,
    scenario: str,
    repetition: int,
    hazard_id: str,
    model: V4ArmingModel,
    occurrence: int = 0,
) -> HiddenArmingOutcome:
    """Sample V4 truth while exposing only a noisy observation to the planner."""

    model.validate()
    armed = (
        keyed_v4_draw(
            seed,
            scenario,
            repetition,
            hazard_id,
            "arming",
            occurrence,
        )
        < model.arming_probability
    )

    observation_probability = (
        model.detection_sensitivity
        if armed
        else 1.0 - model.detection_specificity
    )
    observed_armed = (
        keyed_v4_draw(
            seed,
            scenario,
            repetition,
            hazard_id,
            "observation",
            occurrence,
        )
        < observation_probability
    )

    closure_realized = armed and (
        keyed_v4_draw(
            seed,
            scenario,
            repetition,
            hazard_id,
            "closure",
            occurrence,
        )
        < model.closure_probability_given_armed
    )

    message = PlannerArmingObservation(
        hazard_id=hazard_id,
        observed_armed=observed_armed,
        arming_probability=model.arming_probability,
        detection_sensitivity=model.detection_sensitivity,
        detection_specificity=model.detection_specificity,
        closure_probability_given_armed=model.closure_probability_given_armed,
    )
    return HiddenArmingOutcome(
        hazard_id=hazard_id,
        true_armed=armed,
        detector_message=message,
        future_closure_realized=closure_realized,
    )


def oracle_observation(outcome: HiddenArmingOutcome) -> OracleArmingObservation:
    """Construct truth-bearing data only for the explicitly named oracle."""

    return OracleArmingObservation(
        hazard_id=outcome.hazard_id,
        true_armed=outcome.true_armed,
        closure_probability_given_armed=(
            outcome.detector_message.closure_probability_given_armed
        ),
    )
