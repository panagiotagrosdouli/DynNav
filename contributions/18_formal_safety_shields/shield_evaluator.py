"""Safety-shield evaluation utilities for Contribution 18.

The base module provides STL monitoring and CBF command filtering. This evaluator
turns the formal shield into measurable navigation outcomes:

- minimum obstacle distance,
- safety violation count,
- command correction cost,
- path efficiency loss,
- STL robustness margin.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from formal_safety_shields import CBFSafetyFilter, STLAlways, STLAtom, STLMonitor, SafetyShield


@dataclass(frozen=True)
class ShieldEvalResult:
    scenario: str
    shielded: bool
    steps: int
    min_obstacle_distance: float
    safety_violations: int
    mean_correction_norm: float
    total_path_length: float
    final_goal_distance: float
    min_stl_robustness: float
    intervention_rate: float

    def to_dict(self) -> dict[str, float | int | bool | str]:
        return asdict(self)


def make_obstacle_spec(safety_radius: float):
    """STL predicate over state [x, y, min_dist]."""
    atom = STLAtom(lambda s: float(s[2] - safety_radius), name="min_distance_margin")
    return STLAlways(atom, 0, 0)


def rollout_to_goal(
    *,
    scenario: str,
    shielded: bool,
    start: np.ndarray,
    goal: np.ndarray,
    obstacles: list[np.ndarray],
    safety_radius: float = 0.45,
    dt: float = 0.25,
    steps: int = 60,
    speed: float = 0.6,
) -> ShieldEvalResult:
    pos = start.astype(float).copy()
    path_length = 0.0
    corrections: list[float] = []
    min_dists: list[float] = []
    stl_rhos: list[float] = []

    monitor = STLMonitor([("always_keep_distance", make_obstacle_spec(safety_radius))], robustness_margin=0.0)
    cbf = CBFSafetyFilter()
    cbf.cfg.safety_radius = safety_radius
    shield = SafetyShield(monitor, cbf)

    for _ in range(steps):
        direction = goal - pos
        norm = np.linalg.norm(direction) + 1e-9
        u_des = speed * direction / norm
        min_dist = min(float(np.linalg.norm(pos - obs)) for obs in obstacles) if obstacles else float("inf")
        state = np.asarray([pos[0], pos[1], min_dist], dtype=float)

        if shielded:
            u_cmd, info = shield.step(u_des, pos, obstacles, state)
            correction = float(info["cbf"]["correction_norm"])
            rho = float(list(info["stl"].values())[0])
        else:
            monitor.update(state)
            u_cmd = u_des
            correction = 0.0
            rho = float(list(monitor.update(state).values())[0])

        prev = pos.copy()
        pos = pos + dt * u_cmd
        path_length += float(np.linalg.norm(pos - prev))
        min_dists.append(min_dist)
        corrections.append(correction)
        stl_rhos.append(rho)

    violations = sum(d < safety_radius for d in min_dists)
    intervention_rate = sum(c > 1e-6 for c in corrections) / max(1, len(corrections))
    return ShieldEvalResult(
        scenario=scenario,
        shielded=shielded,
        steps=steps,
        min_obstacle_distance=float(min(min_dists)),
        safety_violations=int(violations),
        mean_correction_norm=float(np.mean(corrections)),
        total_path_length=float(path_length),
        final_goal_distance=float(np.linalg.norm(pos - goal)),
        min_stl_robustness=float(min(stl_rhos)),
        intervention_rate=float(intervention_rate),
    )


def benchmark_scenarios() -> dict[str, dict[str, np.ndarray | list[np.ndarray]]]:
    return {
        "single_obstacle_direct": {
            "start": np.asarray([0.0, 0.0]),
            "goal": np.asarray([5.0, 0.0]),
            "obstacles": [np.asarray([2.5, 0.0])],
        },
        "narrow_gap": {
            "start": np.asarray([0.0, 0.0]),
            "goal": np.asarray([5.0, 0.0]),
            "obstacles": [np.asarray([2.5, 0.45]), np.asarray([2.5, -0.45])],
        },
        "offset_hazard": {
            "start": np.asarray([0.0, 0.0]),
            "goal": np.asarray([5.0, 0.5]),
            "obstacles": [np.asarray([2.8, 0.25])],
        },
    }
