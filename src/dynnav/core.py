"""Core navigation data structures used across DynNav modules."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

import numpy as np

GridCell = tuple[int, int]


@dataclass(frozen=True, slots=True)
class Pose:
    """Discrete grid pose."""

    x: int
    y: int


@dataclass(frozen=True, slots=True)
class Trajectory:
    """A planned route with scalar diagnostics."""

    poses: tuple[Pose, ...]
    cost: float
    risk: float
    recoverability: float

    @property
    def length(self) -> int:
        """Return the number of poses in the trajectory."""
        return len(self.poses)


@dataclass(slots=True)
class GridMap:
    """Occupancy belief grid.

    Values are interpreted as obstacle probabilities in [0, 1]. A value close to
    1 is likely occupied; a value close to 0 is likely free.
    """

    occupancy: np.ndarray
    resolution: float = 1.0

    def __post_init__(self) -> None:
        if self.occupancy.ndim != 2:
            raise ValueError("occupancy must be a 2-D array")
        self.occupancy = np.clip(self.occupancy.astype(float), 0.0, 1.0)

    @property
    def shape(self) -> tuple[int, int]:
        """Return grid shape as (height, width)."""
        return self.occupancy.shape

    def in_bounds(self, pose: Pose) -> bool:
        """Return whether a pose lies inside the grid."""
        height, width = self.shape
        return 0 <= pose.y < height and 0 <= pose.x < width

    def probability(self, pose: Pose) -> float:
        """Return obstacle probability at a pose."""
        if not self.in_bounds(pose):
            return 1.0
        return float(self.occupancy[pose.y, pose.x])

    def neighbors4(self, pose: Pose) -> Iterable[Pose]:
        """Yield four-connected neighboring poses inside the grid."""
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            candidate = Pose(pose.x + dx, pose.y + dy)
            if self.in_bounds(candidate):
                yield candidate


@dataclass(frozen=True, slots=True)
class NavigationState:
    """Planner-facing state with uncertainty and risk signals."""

    pose: GridCell
    goal: GridCell
    localization_uncertainty: float
    map_uncertainty: float
    perception_confidence: float
    planner_confidence: float
    risk_estimate: float
    recoverability: float

    def validate(self) -> None:
        """Raise ValueError if normalized fields are outside [0, 1]."""
        for name in (
            "localization_uncertainty",
            "map_uncertainty",
            "perception_confidence",
            "planner_confidence",
            "risk_estimate",
            "recoverability",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1], got {value!r}")


@dataclass(frozen=True, slots=True)
class PathEvaluation:
    """Summary metrics for a candidate self-aware path."""

    path: Sequence[GridCell]
    path_length: float
    expected_collision_risk: float
    cvar_tail_risk: float
    localization_uncertainty: float
    map_uncertainty: float
    information_gain: float
    recoverability: float
    compute_time_ms: float = 0.0

    def validate(self) -> None:
        """Raise ValueError for invalid normalized metric values."""
        normalized_fields = (
            "expected_collision_risk",
            "cvar_tail_risk",
            "localization_uncertainty",
            "map_uncertainty",
            "information_gain",
            "recoverability",
        )
        for name in normalized_fields:
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1], got {value!r}")
        if self.path_length < 0.0:
            raise ValueError(f"path_length must be non-negative, got {self.path_length!r}")
        if self.compute_time_ms < 0.0:
            raise ValueError(
                f"compute_time_ms must be non-negative, got {self.compute_time_ms!r}"
            )


@dataclass(frozen=True, slots=True)
class SelfAwarenessScore:
    """Interpretable confidence summary for high-level navigation mode choice."""

    trust: float
    uncertainty_pressure: float
    risk_pressure: float
    recoverability_pressure: float
    recommended_mode: str


@dataclass(frozen=True, slots=True)
class SelfAwareCostWeights:
    """Weights for the self-aware navigation objective."""

    alpha_length: float = 1.0
    beta_expected_risk: float = 5.0
    gamma_cvar_risk: float = 3.0
    delta_localization_uncertainty: float = 2.0
    eta_map_uncertainty: float = 2.0
    zeta_irreversibility: float = 2.0
    kappa_information_gain: float = 1.5

    def validate(self) -> None:
        """Raise ValueError when a cost weight is negative."""
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            if value < 0.0:
                raise ValueError(f"{name} must be non-negative, got {value!r}")


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, value))


def estimate_self_awareness(state: NavigationState) -> SelfAwarenessScore:
    """Estimate whether the robot should trust, slow down, or gather information."""
    state.validate()

    uncertainty_pressure = _clip01(
        0.55 * state.localization_uncertainty + 0.45 * state.map_uncertainty
    )
    sensor_trust = _clip01(
        0.50 * state.perception_confidence + 0.50 * state.planner_confidence
    )
    risk_pressure = _clip01(state.risk_estimate)
    recoverability_pressure = _clip01(1.0 - state.recoverability)

    trust = _clip01(
        0.40 * sensor_trust
        + 0.25 * (1.0 - uncertainty_pressure)
        + 0.20 * (1.0 - risk_pressure)
        + 0.15 * state.recoverability
    )

    if risk_pressure > 0.85 or (trust < 0.25 and state.recoverability < 0.35):
        mode = "SAFE_STOP"
    elif uncertainty_pressure > 0.60 and sensor_trust < 0.65:
        mode = "ACTIVE_SENSE"
    elif trust < 0.60 or risk_pressure > 0.50 or recoverability_pressure > 0.50:
        mode = "CAUTIOUS"
    else:
        mode = "NOMINAL"

    return SelfAwarenessScore(
        trust=trust,
        uncertainty_pressure=uncertainty_pressure,
        risk_pressure=risk_pressure,
        recoverability_pressure=recoverability_pressure,
        recommended_mode=mode,
    )


def binary_entropy(probability: float) -> float:
    """Return Bernoulli entropy in bits."""
    if not 0.0 <= probability <= 1.0:
        raise ValueError(f"probability must be in [0, 1], got {probability!r}")
    if probability in (0.0, 1.0):
        return 0.0
    return -probability * math.log2(probability) - (1.0 - probability) * math.log2(
        1.0 - probability
    )


def expected_information_gain(
    path: Sequence[GridCell],
    occupancy_belief: Mapping[GridCell, float],
    sensor_radius: int = 1,
) -> float:
    """Estimate normalized map information gain along a path."""
    if sensor_radius < 0:
        raise ValueError("sensor_radius must be non-negative")
    if not path or not occupancy_belief:
        return 0.0

    visible: set[GridCell] = set()
    for x, y in path:
        for dx in range(-sensor_radius, sensor_radius + 1):
            for dy in range(-sensor_radius, sensor_radius + 1):
                if abs(dx) + abs(dy) <= sensor_radius:
                    cell = (x + dx, y + dy)
                    if cell in occupancy_belief:
                        visible.add(cell)

    if not visible:
        return 0.0

    entropy_sum = sum(binary_entropy(occupancy_belief[cell]) for cell in visible)
    return entropy_sum / len(visible)


def self_aware_path_cost(
    evaluation: PathEvaluation,
    weights: SelfAwareCostWeights | None = None,
) -> float:
    """Return the scalar cost for a candidate path; lower values are better."""
    evaluation.validate()
    weights = weights or SelfAwareCostWeights()
    weights.validate()

    irreversibility = 1.0 - evaluation.recoverability
    return (
        weights.alpha_length * evaluation.path_length
        + weights.beta_expected_risk * evaluation.expected_collision_risk
        + weights.gamma_cvar_risk * evaluation.cvar_tail_risk
        + weights.delta_localization_uncertainty * evaluation.localization_uncertainty
        + weights.eta_map_uncertainty * evaluation.map_uncertainty
        + weights.zeta_irreversibility * irreversibility
        - weights.kappa_information_gain * evaluation.information_gain
    )
