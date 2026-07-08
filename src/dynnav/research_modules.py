"""Integrated research modules for DynNav.

This module exposes deterministic, dependency-light implementations of the
research concepts used throughout the repository. The algorithms are intentionally
simple enough to audit in an MSc/PhD portfolio while still producing measurable
signals for benchmarks, figures, and ROS2 integration scaffolds.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import Enum

import numpy as np

from dynnav.core import GridMap, Pose, Trajectory
from dynnav.planning import DynamicRerouter, NavigationPolicy, PlannerSwitch, RiskAwareAStar
from dynnav.risk import mission_risk

LOGGER = logging.getLogger(__name__)


class SafetyMode(str, Enum):
    """Runtime navigation modes emitted by the supervisor."""

    NOMINAL = "nominal"
    CAUTIOUS = "cautious"
    REPLAN = "replan"
    SAFE_MODE = "safe_mode"
    SAFE_STOP = "safe_stop"


@dataclass(frozen=True, slots=True)
class UncertaintyState:
    """Uncertainty channels used by planning and monitoring."""

    map_entropy: float
    localization_std: float
    obstacle_velocity_std: float
    perception_dropout: float

    def normalized_pressure(self) -> float:
        """Return a bounded aggregate uncertainty pressure."""
        value = (
            0.35 * self.map_entropy
            + 0.30 * self.localization_std
            + 0.20 * self.obstacle_velocity_std
            + 0.15 * self.perception_dropout
        )
        return float(np.clip(value, 0.0, 1.0))


@dataclass(frozen=True, slots=True)
class MissionRiskReport:
    """Mission-level summary used for publication tables and supervisors."""

    expected_collision_risk: float
    cvar_tail_risk: float
    uncertainty_pressure: float
    recoverability: float
    mission_score: float
    recommended_mode: SafetyMode


@dataclass(frozen=True, slots=True)
class RuntimeObservation:
    """Signals sampled at one navigation timestep."""

    step: int
    pose: Pose
    path_risk: float
    recoverability: float
    uncertainty: UncertaintyState
    blocked: bool = False


@dataclass(frozen=True, slots=True)
class MonitorEvent:
    """Decision emitted by the runtime monitor."""

    step: int
    mode: SafetyMode
    reason: str
    risk: float
    uncertainty: float
    recoverability: float


class UncertaintyPropagator:
    """Propagate occupancy uncertainty with conservative local diffusion."""

    def __init__(self, diffusion: float = 0.08, process_noise: float = 0.02) -> None:
        if not 0.0 <= diffusion <= 1.0:
            raise ValueError("diffusion must be in [0, 1]")
        if process_noise < 0.0:
            raise ValueError("process_noise must be non-negative")
        self.diffusion = diffusion
        self.process_noise = process_noise

    def propagate(self, grid: GridMap, dynamic_cells: Iterable[Pose] = ()) -> GridMap:
        """Return a new grid after one uncertainty-propagation step."""
        occ = grid.occupancy
        padded = np.pad(occ, pad_width=1, mode="edge")
        local_mean = (
            padded[1:-1, 1:-1]
            + padded[:-2, 1:-1]
            + padded[2:, 1:-1]
            + padded[1:-1, :-2]
            + padded[1:-1, 2:]
        ) / 5.0
        propagated = (1.0 - self.diffusion) * occ + self.diffusion * local_mean
        propagated = np.clip(propagated + self.process_noise, 0.0, 1.0)
        for cell in dynamic_cells:
            if grid.in_bounds(cell):
                propagated[cell.y, cell.x] = min(1.0, propagated[cell.y, cell.x] + 0.25)
        return GridMap(propagated, resolution=grid.resolution)


class RiskEstimator:
    """Estimate cell and trajectory risk from belief and uncertainty fields."""

    def __init__(self, uncertainty_weight: float = 0.35) -> None:
        if uncertainty_weight < 0.0:
            raise ValueError("uncertainty_weight must be non-negative")
        self.uncertainty_weight = uncertainty_weight

    def risk_field(self, grid: GridMap, uncertainty: np.ndarray | None = None) -> np.ndarray:
        """Return a bounded risk field aligned with the occupancy grid."""
        base = grid.occupancy.copy()
        if uncertainty is not None:
            if uncertainty.shape != grid.shape:
                raise ValueError("uncertainty must match grid shape")
            base = base + self.uncertainty_weight * np.clip(uncertainty, 0.0, 1.0)
        return np.clip(base, 0.0, 1.0)

    def trajectory_risk(self, grid: GridMap, path: Sequence[Pose], alpha: float = 0.9) -> float:
        """Return CVaR-like mission risk along a trajectory."""
        return mission_risk([grid.probability(pose) for pose in path], alpha=alpha)


class ReturnabilityAnalyzer:
    """Analyze whether a planned path preserves escape routes to the origin."""

    def __init__(self, planner: NavigationPolicy | None = None) -> None:
        self.planner = planner or RiskAwareAStar(risk_weight=1.0, returnability_weight=0.0)

    def score(self, grid: GridMap, path: Sequence[Pose], origin: Pose) -> float:
        """Return the fraction of sampled path states that can safely return."""
        if not path:
            return 0.0
        sample_step = max(1, len(path) // 10)
        sampled = path[::sample_step]
        safe_returns = 0
        for pose in sampled:
            trajectory, metrics = self.planner.plan(grid, pose, origin)
            if metrics.path_found and trajectory.risk <= 0.60:
                safe_returns += 1
        return safe_returns / len(sampled)


class SafeModeSupervisor:
    """Map risk, uncertainty, and recoverability signals to safety modes."""

    def __init__(
        self,
        replan_risk: float = 0.50,
        safe_mode_risk: float = 0.70,
        safe_stop_risk: float = 0.88,
        min_recoverability: float = 0.35,
    ) -> None:
        self.replan_risk = replan_risk
        self.safe_mode_risk = safe_mode_risk
        self.safe_stop_risk = safe_stop_risk
        self.min_recoverability = min_recoverability

    def decide(self, report: MissionRiskReport, blocked: bool = False) -> SafetyMode:
        """Return the least aggressive mode that satisfies safety thresholds."""
        if blocked or report.expected_collision_risk >= self.safe_stop_risk:
            return SafetyMode.SAFE_STOP
        if report.cvar_tail_risk >= self.safe_mode_risk:
            return SafetyMode.SAFE_MODE
        if report.recoverability < self.min_recoverability:
            return SafetyMode.SAFE_MODE
        if report.expected_collision_risk >= self.replan_risk:
            return SafetyMode.REPLAN
        if report.uncertainty_pressure >= 0.55:
            return SafetyMode.CAUTIOUS
        return SafetyMode.NOMINAL


class MissionRiskEstimator:
    """Combine trajectory risk, uncertainty, and returnability into one report."""

    def __init__(self, supervisor: SafeModeSupervisor | None = None) -> None:
        self.supervisor = supervisor or SafeModeSupervisor()

    def evaluate(
        self,
        trajectory: Trajectory,
        uncertainty: UncertaintyState,
        blocked: bool = False,
    ) -> MissionRiskReport:
        """Return an interpretable mission risk report."""
        uncertainty_pressure = uncertainty.normalized_pressure()
        expected = float(np.clip(trajectory.risk, 0.0, 1.0))
        cvar_tail = float(np.clip(0.65 * expected + 0.35 * uncertainty_pressure, 0.0, 1.0))
        score = float(
            np.clip(
                1.0
                - 0.45 * expected
                - 0.25 * cvar_tail
                - 0.20 * uncertainty_pressure
                + 0.10 * trajectory.recoverability,
                0.0,
                1.0,
            )
        )
        provisional = MissionRiskReport(
            expected_collision_risk=expected,
            cvar_tail_risk=cvar_tail,
            uncertainty_pressure=uncertainty_pressure,
            recoverability=trajectory.recoverability,
            mission_score=score,
            recommended_mode=SafetyMode.NOMINAL,
        )
        mode = self.supervisor.decide(provisional, blocked=blocked)
        return MissionRiskReport(
            expected_collision_risk=expected,
            cvar_tail_risk=cvar_tail,
            uncertainty_pressure=uncertainty_pressure,
            recoverability=trajectory.recoverability,
            mission_score=score,
            recommended_mode=mode,
        )


class RuntimeMonitor:
    """Stateful runtime monitor with cooldown-aware replanning decisions."""

    def __init__(self, estimator: MissionRiskEstimator | None = None, cooldown: int = 3) -> None:
        if cooldown < 0:
            raise ValueError("cooldown must be non-negative")
        self.estimator = estimator or MissionRiskEstimator()
        self.cooldown = cooldown
        self._last_replan_step = -10_000

    def observe(self, observation: RuntimeObservation, trajectory: Trajectory) -> MonitorEvent:
        """Evaluate one runtime observation and emit a monitor event."""
        report = self.estimator.evaluate(trajectory, observation.uncertainty, observation.blocked)
        mode = report.recommended_mode
        reason = "thresholds nominal"
        if mode == SafetyMode.REPLAN:
            if observation.step - self._last_replan_step < self.cooldown:
                mode = SafetyMode.CAUTIOUS
                reason = "replan suppressed by cooldown"
            else:
                self._last_replan_step = observation.step
                reason = "risk threshold exceeded"
        elif mode == SafetyMode.SAFE_MODE:
            reason = "tail risk or recoverability threshold exceeded"
        elif mode == SafetyMode.SAFE_STOP:
            reason = "blocked path or severe risk threshold exceeded"
        elif mode == SafetyMode.CAUTIOUS:
            reason = "uncertainty threshold exceeded"
        LOGGER.info("runtime_monitor step=%s mode=%s reason=%s", observation.step, mode, reason)
        return MonitorEvent(
            step=observation.step,
            mode=mode,
            reason=reason,
            risk=report.expected_collision_risk,
            uncertainty=report.uncertainty_pressure,
            recoverability=report.recoverability,
        )


@dataclass(slots=True)
class DynNavResearchStack:
    """Convenience facade wiring planning, rerouting, monitoring, and switching."""

    nominal_planner: NavigationPolicy = RiskAwareAStar(risk_weight=2.5, returnability_weight=0.8)
    conservative_planner: NavigationPolicy = RiskAwareAStar(risk_weight=6.0, returnability_weight=2.0)

    def __post_init__(self) -> None:
        self.switch = PlannerSwitch(self.nominal_planner, self.conservative_planner)
        self.rerouter = DynamicRerouter(self.conservative_planner)
        self.monitor = RuntimeMonitor()

    def plan_and_evaluate(
        self,
        grid: GridMap,
        start: Pose,
        goal: Pose,
        uncertainty: UncertaintyState,
    ) -> tuple[Trajectory, MissionRiskReport]:
        """Plan with policy switching and return the mission-risk report."""
        estimated_risk = uncertainty.normalized_pressure()
        planner = self.switch.select(estimated_risk)
        trajectory, metrics = planner.plan(grid, start, goal)
        if not metrics.path_found:
            LOGGER.warning("planner failed to find a path from %s to %s", start, goal)
        report = MissionRiskEstimator().evaluate(trajectory, uncertainty)
        return trajectory, report
