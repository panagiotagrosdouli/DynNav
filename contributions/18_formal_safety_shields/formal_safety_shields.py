"""
Contribution 18: Formal Safety Shields — STL + Control Barrier Functions
=========================================================================
Provides runtime monitoring and a single-integrator barrier-filter prototype by wrapping any navigation
planner with two complementary mechanisms:

1. Signal Temporal Logic (STL) monitor: evaluates temporal safety
   specifications over the robot's state trajectory and flags violations.

2. Control Barrier Function (CBF) filter: projects velocity commands against
   static-obstacle half-space constraints under a point-robot, continuous-time
   single-integrator model. This prototype does not establish a physical safety
   guarantee.

Research Question (RQ-Formal): Do STL+CBF safety shields reduce constraint
violations without significantly degrading navigation efficiency?

References:
    Donze & Maler (2010) "Robust Satisfaction of Temporal Logic Specifications"
    Ames et al. (2019) "Control Barrier Functions: Theory and Applications"
    Raman et al. (2015) "Model Predictive Control with Signal Temporal Logic Specs"
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Signal Temporal Logic (STL) primitives
# ---------------------------------------------------------------------------

class STLFormula:
    """Base class for STL formulae. Evaluates robustness ρ over a signal."""

    def robustness(self, signal: np.ndarray, t: int) -> float:
        raise NotImplementedError


class STLAtom(STLFormula):
    """Predicate μ(s) ≥ 0 evaluated at time t."""

    def __init__(self, predicate: Callable[[np.ndarray], float], name: str = ""):
        self.predicate = predicate
        self.name = name

    def robustness(self, signal: np.ndarray, t: int) -> float:
        return float(self.predicate(signal[t]))


class STLAlways(STLFormula):
    """□[a,b] φ  — Always φ holds in [t+a, t+b]."""

    def __init__(self, formula: STLFormula, a: int, b: int):
        self.formula = formula
        self.a, self.b = a, b

    def robustness(self, signal: np.ndarray, t: int) -> float:
        T = len(signal)
        rho_vals = [
            self.formula.robustness(signal, min(t + tau, T - 1))
            for tau in range(self.a, self.b + 1)
        ]
        return float(min(rho_vals)) if rho_vals else 0.0


class STLEventually(STLFormula):
    """◇[a,b] φ  — Eventually φ holds in [t+a, t+b]."""

    def __init__(self, formula: STLFormula, a: int, b: int):
        self.formula = formula
        self.a, self.b = a, b

    def robustness(self, signal: np.ndarray, t: int) -> float:
        T = len(signal)
        rho_vals = [
            self.formula.robustness(signal, min(t + tau, T - 1))
            for tau in range(self.a, self.b + 1)
        ]
        return float(max(rho_vals)) if rho_vals else 0.0


class STLAnd(STLFormula):
    """φ₁ ∧ φ₂"""

    def __init__(self, *formulae: STLFormula):
        self.formulae = formulae

    def robustness(self, signal: np.ndarray, t: int) -> float:
        return min(f.robustness(signal, t) for f in self.formulae)


class STLOr(STLFormula):
    """φ₁ ∨ φ₂"""

    def __init__(self, *formulae: STLFormula):
        self.formulae = formulae

    def robustness(self, signal: np.ndarray, t: int) -> float:
        return max(f.robustness(signal, t) for f in self.formulae)


# ---------------------------------------------------------------------------
# STL Safety Monitor
# ---------------------------------------------------------------------------

class STLMonitor:
    """
    Online STL monitor: evaluates a set of safety specifications over the
    robot's state trajectory and issues warnings / blocks actions.
    """

    def __init__(self, specs: list[tuple[str, STLFormula]],
                 robustness_margin: float = 0.0):
        self.specs = specs   # (name, formula)
        self.margin = robustness_margin
        self._trajectory: list[np.ndarray] = []
        self.violation_log: list[dict] = []

    def update(self, state: np.ndarray) -> dict[str, float]:
        """Append state and evaluate all specs at current time."""
        self._trajectory.append(state)
        signal = np.array(self._trajectory)
        t = len(signal) - 1
        results = {}
        for name, formula in self.specs:
            rho = formula.robustness(signal, max(0, t))
            results[name] = rho
            if rho < self.margin:
                entry = {"t": t, "spec": name, "rho": rho}
                self.violation_log.append(entry)
                logger.warning("STL violation | spec=%s ρ=%.4f", name, rho)
        return results

    def is_safe(self) -> bool:
        if not self._trajectory:
            return True
        signal = np.array(self._trajectory)
        t = len(signal) - 1
        return all(
            f.robustness(signal, t) >= self.margin
            for _, f in self.specs
        )

    def reset(self) -> None:
        self._trajectory.clear()
        self.violation_log.clear()


# ---------------------------------------------------------------------------
# Control Barrier Function (CBF) safety filter
# ---------------------------------------------------------------------------

@dataclass
class CBFConfig:
    safety_radius: float = 0.4       # minimum distance to obstacle (metres)
    alpha: float = 1.5               # CBF class-K function gain
    max_iter: int = 20               # cyclic half-space projection iterations

    def __post_init__(self) -> None:
        if not np.isfinite(self.safety_radius) or self.safety_radius <= 0:
            raise ValueError("safety_radius must be finite and positive")
        if not np.isfinite(self.alpha) or self.alpha <= 0:
            raise ValueError("alpha must be finite and positive")
        if self.max_iter < 1:
            raise ValueError("max_iter must be positive")


class CBFSafetyFilter:
    """
    Control Barrier Function filter for a unicycle / point robot.

    Given a desired velocity command u_des and a set of obstacle positions,
    projects a desired command onto static-obstacle half-spaces for
    h(x) = ||x - x_obs|| - r under x_dot = u. This is a sampled command-level
    check, not a proof of safety for a physical/dynamic robot.
    """

    def __init__(self, cfg: CBFConfig | None = None):
        self.cfg = cfg or CBFConfig()

    def h(self, robot_pos: np.ndarray, obs_pos: np.ndarray) -> float:
        """Barrier function: h(x) = ‖robot − obs‖ − r ≥ 0 means safe."""
        return float(np.linalg.norm(robot_pos - obs_pos) - self.cfg.safety_radius)

    def dh_dx(self, robot_pos: np.ndarray, obs_pos: np.ndarray) -> np.ndarray:
        """Gradient ∂h/∂x."""
        diff = robot_pos - obs_pos
        norm = np.linalg.norm(diff) + 1e-8
        return diff / norm

    def filter(self, u_des: np.ndarray,
               robot_pos: np.ndarray,
               obstacles: list[np.ndarray]) -> np.ndarray:
        """
        Cyclically project onto the linearized CBF half-spaces.

        For static obstacles and x_dot=u, each constraint is
        grad(h_i)·u >= -alpha*h_i. Feasibility is checked separately by
        ``batch_filter``; this method alone cannot certify a command.
        """
        u = np.asarray(u_des, dtype=float).reshape(-1).copy()
        pos = np.asarray(robot_pos, dtype=float).reshape(-1)
        obs_array = [np.asarray(obs, dtype=float).reshape(-1) for obs in obstacles]
        if u.size != 2 or pos.size != 2 or not np.all(np.isfinite(u)) or not np.all(np.isfinite(pos)):
            raise ValueError("desired command and robot position must be finite 2D vectors")
        if any(obs.size != 2 or not np.all(np.isfinite(obs)) for obs in obs_array):
            raise ValueError("obstacles must be finite 2D vectors")

        constraints = []
        for obs in obs_array:
            h_val = self.h(pos, obs)
            grad = self.dh_dx(pos, obs)
            rhs = -self.cfg.alpha * h_val
            constraints.append((grad, rhs))

        for _ in range(self.cfg.max_iter):
            max_violation = 0.0
            for grad, rhs in constraints:
                residual = float(grad @ u - rhs)
                if residual < 0 and float(grad @ grad) > 1e-16:
                    u += (-residual / float(grad @ grad)) * grad
                max_violation = max(max_violation, -residual)
            if max_violation <= 1e-8:
                break
        logger.debug("CBF projection complete | command=%s", u)
        return u

    def batch_filter(self, u_des: np.ndarray,
                     robot_pos: np.ndarray,
                     obstacles: list[np.ndarray],
                     robot_state: Optional[np.ndarray] = None
                     ) -> tuple[np.ndarray, dict]:
        """
        Filter command and return diagnostics.
        """
        u_des = np.asarray(u_des, dtype=float).reshape(-1)
        robot_pos = np.asarray(robot_pos, dtype=float).reshape(-1)
        obs_array = [np.asarray(obs, dtype=float).reshape(-1) for obs in obstacles]
        u_safe = self.filter(u_des, robot_pos, obs_array)
        correction = np.linalg.norm(u_safe - u_des)
        min_dist = min(
            np.linalg.norm(robot_pos - obs) for obs in obs_array
        ) if obs_array else np.inf
        residuals = [float(self.dh_dx(robot_pos, obs) @ u_safe + self.cfg.alpha * self.h(robot_pos, obs))
                     for obs in obs_array]
        min_residual = min(residuals) if residuals else np.inf

        info = {
            "correction_norm": round(float(correction), 5),
            "min_obstacle_dist": round(float(min_dist), 5),
            "safety_violated": min_dist < self.cfg.safety_radius,
            "cbf_constraints_satisfied": min_residual >= -1e-8,
            "min_cbf_residual": round(float(min_residual), 8),
        }
        if info["safety_violated"]:
            logger.warning(
                "CBF: robot at distance %.3f < safety radius %.3f",
                min_dist, self.cfg.safety_radius
            )
        return u_safe, info


# ---------------------------------------------------------------------------
# Combined safety shield
# ---------------------------------------------------------------------------

class SafetyShield:
    """
    Wraps a planner with both STL monitoring and CBF command filtering.
    Usage:
        shield = SafetyShield(stl_monitor, cbf_filter)
        u_safe = shield.step(u_desired, robot_pos, obstacles, robot_state)
    """

    def __init__(self, stl_monitor: STLMonitor,
                 cbf_filter: CBFSafetyFilter):
        self.stl = stl_monitor
        self.cbf = cbf_filter
        self.steps = 0
        self.total_corrections = 0.0

    def step(self, u_des: np.ndarray,
             robot_pos: np.ndarray,
             obstacles: list[np.ndarray],
             robot_state: Optional[np.ndarray] = None
             ) -> tuple[np.ndarray, dict]:
        """
        One control step:
        1. Update STL monitor.
        2. Apply CBF filter.
        3. Return safe command + diagnostics.
        """
        stl_state = robot_state if robot_state is not None else robot_pos
        stl_robustness = self.stl.update(stl_state)
        u_safe, cbf_info = self.cbf.batch_filter(u_des, robot_pos, obstacles)

        self.steps += 1
        self.total_corrections += cbf_info["correction_norm"]

        return u_safe, {
            "stl": stl_robustness,
            "cbf": cbf_info,
            "stl_safe": self.stl.is_safe(),
            "avg_correction": round(self.total_corrections / self.steps, 6),
        }
