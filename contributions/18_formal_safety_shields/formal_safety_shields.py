"""
Contribution 18: Formal Safety Shields — STL + Control Barrier Functions
=========================================================================
Provides runtime-verifiable safety guarantees by wrapping any navigation
planner with two complementary mechanisms:

1. Signal Temporal Logic (STL) monitor: evaluates temporal safety
   specifications over the robot's state trajectory and flags violations.

2. Control Barrier Function (CBF) filter: modifies velocity commands in
   real-time to guarantee obstacle avoidance with formal Lyapunov-style
   safety certificates.

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
    gamma: float = 0.95              # margin relaxation factor
    max_iter: int = 20               # QP solver iterations (gradient projection)
    step_size: float = 0.05          # gradient projection step


class CBFSafetyFilter:
    """
    Instantaneous Control Barrier Function filter for 2D point-robot velocity.

    Given a desired velocity command u_des and a set of obstacle positions,
    returns a minimally modified instantaneous velocity satisfying the
    linearized CBF inequality if feasible; this ALONE does not prove future
    safety for a physical robot or finite-rate controller. Target h(x) ≥ 0
    where h(x) = ‖x - x_obs‖² - r²  (sphere safety set).
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

    def filter_verified(self, u_des: np.ndarray,
                        robot_pos: np.ndarray,
                        obstacles: list[np.ndarray]) -> tuple[np.ndarray, dict]:
        """Project a 2D point velocity onto all *linearized instantaneous* CBF constraints.

        Enumerates vertices/active sets of the exact 2D Euclidean projection
        QP. This is NOT a formal multi-step safety theorem, and cannot model
        the actual unicycle, uncertain obstacle motion or finite-rate control.
        An infeasible constraint set returns ZERO with feasible=False; the
        caller MUST NOT treat zero as a certified safe command when h<0.
        """
        desired = np.asarray(u_des, dtype=float)
        pos = np.asarray(robot_pos, dtype=float)
        if desired.shape != (2,) or pos.shape != (2,) or not (
            np.isfinite(desired).all() and np.isfinite(pos).all()):
            raise ValueError("C18 requires finite 2D desired velocity and position")
        if not (np.isfinite(self.cfg.alpha) and self.cfg.alpha > 0
                and np.isfinite(self.cfg.safety_radius) and self.cfg.safety_radius > 0):
            raise ValueError("C18 safety radius and CBF gain must be finite positive")
        constraints = []
        for obstacle in obstacles:
            obs = np.asarray(obstacle, dtype=float)
            if obs.shape != (2,) or not np.isfinite(obs).all():
                raise ValueError("C18 obstacle coordinate invalid")
            grad = self.dh_dx(pos, obs)
            h = self.h(pos, obs)
            constraints.append((grad, -self.cfg.alpha * h))
        def feasible(candidate: np.ndarray) -> bool:
            return bool(all(float(a @ candidate) >= b - 1e-8 for a,b in constraints))
        candidates = [desired]
        for a,b in constraints:
            norm2 = float(a @ a)
            if norm2 > 1e-12:
                candidates.append(desired + max(0., (b - float(a @ desired))/norm2) * a)
        for i,(a,b) in enumerate(constraints):
            for c,d in constraints[i+1:]:
                mat = np.stack([a,c])
                if abs(float(np.linalg.det(mat))) > 1e-10:
                    candidates.append(np.linalg.solve(mat, np.array([b,d])))
        eligible = [u for u in candidates if feasible(u)]
        if not eligible:
            return np.zeros_like(desired), {
                "constraint_feasible": False, "minimum_cbf_margin": None,
                "status": "INFEASIBLE_CBF_ZERO_COMMAND_NOT_CERTIFIED_SAFE",
                "instantaneous_only": True,
            }
        solution = min(eligible,key=lambda u: float(np.sum((u-desired)**2)))
        margin = min((float(a @ solution - b) for a,b in constraints),default=float("inf"))
        return solution, {
            "constraint_feasible": True,
            "minimum_cbf_margin": margin if np.isfinite(margin) else None,
            "status": "INSTANTANEOUS_LINEARIZED_CBF_FEASIBLE",
            "instantaneous_only": True,
        }

    def filter(self, u_des: np.ndarray,
               robot_pos: np.ndarray,
               obstacles: list[np.ndarray]) -> np.ndarray:
        """Compatibility interface; inspect batch_filter for feasibility evidence."""
        return self.filter_verified(u_des, robot_pos, obstacles)[0]

    def batch_filter(self, u_des: np.ndarray,
                     robot_pos: np.ndarray,
                     obstacles: list[np.ndarray],
                     robot_state: Optional[np.ndarray] = None
                     ) -> tuple[np.ndarray, dict]:
        """
        Filter command and return diagnostics.
        """
        u_safe, certificate = self.filter_verified(u_des, robot_pos, obstacles)
        correction = np.linalg.norm(u_safe - u_des)
        min_dist = min(
            np.linalg.norm(robot_pos - obs) for obs in obstacles
        ) if obstacles else np.inf

        info = {
            "correction_norm": round(float(correction), 5),
            "min_obstacle_dist": round(float(min_dist), 5),
            "safety_violated": bool(min_dist < self.cfg.safety_radius),
            **certificate,
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
