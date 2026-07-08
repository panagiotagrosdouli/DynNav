"""Lab-grade navigation primitives for DynNav.

This module intentionally contains compact, dependency-light research building
blocks that are safe to run in CI. The algorithms are implemented as deterministic
prototypes: they are suitable for reproducible experiments, but they are not a
formal safety certificate and are not a complete ROS 2/Nav2 plugin implementation.
"""

from __future__ import annotations

import heapq
import time
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from dynnav.core import GridMap, Pose, Trajectory
from dynnav.planning import RiskAwareAStar, manhattan
from dynnav.risk import entropy, mission_risk


class FeatureMaturity(str, Enum):
    """Scientifically honest feature status labels."""

    IMPLEMENTED = "Implemented"
    PROTOTYPE = "Prototype"
    PLANNED = "Planned"


@dataclass(frozen=True, slots=True)
class DynNavFeature:
    """Repository feature and its evidence level."""

    name: str
    maturity: FeatureMaturity
    evidence: str
    limitation: str


FEATURE_REGISTRY: tuple[DynNavFeature, ...] = (
    DynNavFeature(
        "Risk-aware A* over occupancy-belief grids",
        FeatureMaturity.IMPLEMENTED,
        "src/dynnav/planning.py plus pytest coverage",
        "Validated on deterministic grid scenarios, not on hardware logs.",
    ),
    DynNavFeature(
        "ROS 2/Nav2 plugin integration",
        FeatureMaturity.PROTOTYPE,
        "documentation and package scaffolds",
        "No compiled Nav2 planner plugin is claimed yet.",
    ),
    DynNavFeature(
        "Formal safety guarantees",
        FeatureMaturity.PLANNED,
        "roadmap only",
        "Requires proofs and hardware validation before being claimed.",
    ),
)


@dataclass(frozen=True, slots=True)
class PlanningRequest:
    """Canonical planning input for benchmark and ROS-facing adapters."""

    start: Pose
    goal: Pose
    occupancy: GridMap
    dynamic_obstacles: tuple[Pose, ...] = ()
    seed: int = 7


@dataclass(frozen=True, slots=True)
class FieldBundle:
    """Risk, uncertainty, and recoverability fields for a grid map."""

    risk: np.ndarray
    uncertainty: np.ndarray
    recoverability: np.ndarray

    def validate(self) -> None:
        """Validate field shapes and normalized ranges."""
        if not (self.risk.shape == self.uncertainty.shape == self.recoverability.shape):
            raise ValueError("all fields must share the same shape")
        for name, values in (
            ("risk", self.risk),
            ("uncertainty", self.uncertainty),
            ("recoverability", self.recoverability),
        ):
            if np.any(values < 0.0) or np.any(values > 1.0):
                raise ValueError(f"{name} must be normalized to [0, 1]")


@dataclass(frozen=True, slots=True)
class RerouteDecision:
    """Decision emitted by the rerouting supervisor."""

    should_reroute: bool
    reason: str
    risk: float
    uncertainty: float
    recoverability: float
    cooldown_active: bool = False


@dataclass(frozen=True, slots=True)
class SafetyAction:
    """High-level safety action for mission supervision."""

    mode: str
    velocity_scale: float
    requires_replan: bool
    reason: str


@dataclass(slots=True)
class PlannerRegistry:
    """Small registry for deterministic planner selection."""

    planners: dict[str, object] = field(default_factory=dict)

    def register(self, name: str, planner: object) -> None:
        """Register a planner under a stable name."""
        if not name:
            raise ValueError("planner name must be non-empty")
        if not hasattr(planner, "plan"):
            raise TypeError("planner must expose a plan(grid, start, goal) method")
        self.planners[name] = planner

    def get(self, name: str) -> object:
        """Return a registered planner."""
        try:
            return self.planners[name]
        except KeyError as exc:
            raise KeyError(f"unknown planner {name!r}") from exc


def dijkstra_plan(grid: GridMap, start: Pose, goal: Pose) -> tuple[Trajectory, int]:
    """Plan a shortest feasible four-connected path with Dijkstra search."""
    frontier: list[tuple[float, int, Pose]] = [(0.0, 0, start)]
    came_from: dict[Pose, Pose | None] = {start: None}
    cost_so_far: dict[Pose, float] = {start: 0.0}
    expanded = 0
    order = 0

    while frontier:
        _, _, current = heapq.heappop(frontier)
        expanded += 1
        if current == goal:
            break
        for neighbor in grid.neighbors4(current):
            if grid.probability(neighbor) >= 0.98:
                continue
            new_cost = cost_so_far[current] + 1.0
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                order += 1
                heapq.heappush(frontier, (new_cost, order, neighbor))
                came_from[neighbor] = current

    if goal not in came_from:
        return Trajectory((start,), float("inf"), 1.0, 0.0), expanded

    path = _reconstruct(came_from, goal)
    risk = mission_risk([grid.probability(p) for p in path])
    return Trajectory(tuple(path), cost_so_far[goal], risk, 1.0), expanded


def astar_plan(grid: GridMap, start: Pose, goal: Pose) -> tuple[Trajectory, int]:
    """Plan a shortest feasible path with Manhattan A*."""
    frontier: list[tuple[float, int, Pose]] = [(0.0, 0, start)]
    came_from: dict[Pose, Pose | None] = {start: None}
    cost_so_far: dict[Pose, float] = {start: 0.0}
    expanded = 0
    order = 0

    while frontier:
        _, _, current = heapq.heappop(frontier)
        expanded += 1
        if current == goal:
            break
        for neighbor in grid.neighbors4(current):
            if grid.probability(neighbor) >= 0.98:
                continue
            new_cost = cost_so_far[current] + 1.0
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                order += 1
                priority = new_cost + manhattan(neighbor, goal)
                heapq.heappush(frontier, (priority, order, neighbor))
                came_from[neighbor] = current

    if goal not in came_from:
        return Trajectory((start,), float("inf"), 1.0, 0.0), expanded
    path = _reconstruct(came_from, goal)
    risk = mission_risk([grid.probability(p) for p in path])
    return Trajectory(tuple(path), cost_so_far[goal], risk, 1.0), expanded


def _reconstruct(came_from: Mapping[Pose, Pose | None], goal: Pose) -> list[Pose]:
    path = [goal]
    current = goal
    while came_from[current] is not None:
        current = came_from[current]  # type: ignore[index,assignment]
        path.append(current)
    path.reverse()
    return path


def compute_uncertainty_field(grid: GridMap) -> np.ndarray:
    """Return normalized map uncertainty from Bernoulli entropy."""
    ent = entropy(grid.occupancy)
    max_ent = float(entropy(np.asarray([0.5]))[0])
    return np.clip(ent / max_ent, 0.0, 1.0)


def compute_proximity_risk(grid: GridMap, dynamic_obstacles: Iterable[Pose] = ()) -> np.ndarray:
    """Compute obstacle-proximity and dynamic-obstacle risk on a grid."""
    height, width = grid.shape
    risk = np.array(grid.occupancy, dtype=float)
    occupied = np.argwhere(grid.occupancy >= 0.98)
    yy, xx = np.mgrid[0:height, 0:width]

    for y, x in occupied:
        dist = np.abs(xx - x) + np.abs(yy - y)
        risk = np.maximum(risk, np.exp(-0.7 * dist))

    for obstacle in dynamic_obstacles:
        dist = np.abs(xx - obstacle.x) + np.abs(yy - obstacle.y)
        risk = np.maximum(risk, 0.85 * np.exp(-0.5 * dist))

    return np.clip(risk, 0.0, 1.0)


def compute_recoverability_field(grid: GridMap, origin: Pose) -> np.ndarray:
    """Estimate returnability to an origin using Dijkstra reachability."""
    height, width = grid.shape
    values = np.zeros((height, width), dtype=float)
    for y in range(height):
        for x in range(width):
            pose = Pose(x, y)
            if grid.probability(pose) >= 0.98:
                values[y, x] = 0.0
                continue
            trajectory, _ = dijkstra_plan(grid, pose, origin)
            values[y, x] = 0.0 if not np.isfinite(trajectory.cost) else 1.0 / (1.0 + 0.05 * trajectory.cost)
    return np.clip(values, 0.0, 1.0)


def build_fields(request: PlanningRequest) -> FieldBundle:
    """Build risk, uncertainty, and recoverability fields for a request."""
    fields = FieldBundle(
        risk=compute_proximity_risk(request.occupancy, request.dynamic_obstacles),
        uncertainty=compute_uncertainty_field(request.occupancy),
        recoverability=compute_recoverability_field(request.occupancy, request.start),
    )
    fields.validate()
    return fields


def blocked_path(path: Sequence[Pose], grid: GridMap, dynamic_obstacles: Iterable[Pose] = ()) -> bool:
    """Return whether an active path is blocked by occupancy or dynamic obstacles."""
    obstacle_set = set(dynamic_obstacles)
    return any(grid.probability(pose) >= 0.98 or pose in obstacle_set for pose in path)


@dataclass(slots=True)
class ReroutingSupervisor:
    """Threshold-based rerouting rule with deterministic cooldown."""

    risk_threshold: float = 0.55
    uncertainty_threshold: float = 0.65
    recoverability_threshold: float = 0.35
    cooldown_steps: int = 2
    _last_reroute_step: int = field(default=-10_000, init=False)

    def evaluate(
        self,
        step: int,
        trajectory: Trajectory,
        fields: FieldBundle,
        current: Pose,
        active_path: Sequence[Pose],
        dynamic_obstacles: Iterable[Pose] = (),
    ) -> RerouteDecision:
        """Evaluate whether the mission should reroute."""
        fields.validate()
        cooldown_active = step - self._last_reroute_step < self.cooldown_steps
        local_uncertainty = float(fields.uncertainty[current.y, current.x])
        local_recoverability = float(fields.recoverability[current.y, current.x])
        path_blocked = blocked_path(active_path, GridMap(fields.risk >= 0.98), dynamic_obstacles)

        reasons: list[str] = []
        if path_blocked:
            reasons.append("blocked_path")
        if trajectory.risk > self.risk_threshold:
            reasons.append("risk_threshold")
        if local_uncertainty > self.uncertainty_threshold:
            reasons.append("uncertainty_threshold")
        if local_recoverability < self.recoverability_threshold:
            reasons.append("recoverability_threshold")

        should = bool(reasons) and not cooldown_active
        if should:
            self._last_reroute_step = step
        return RerouteDecision(
            should_reroute=should,
            reason="+".join(reasons) if reasons else "nominal",
            risk=trajectory.risk,
            uncertainty=local_uncertainty,
            recoverability=local_recoverability,
            cooldown_active=cooldown_active,
        )


@dataclass(frozen=True, slots=True)
class SafetySupervisor:
    """Mission-level safety supervisor.

    The thresholds are intentionally conservative and explicit. They encode a
    prototype policy, not a certified control barrier function.
    """

    stop_risk: float = 0.85
    stop_uncertainty: float = 0.90
    replan_risk: float = 0.55
    replan_uncertainty: float = 0.70
    min_recoverability: float = 0.30

    def decide(self, risk: float, uncertainty: float, recoverability: float) -> SafetyAction:
        """Return safe-stop, slow-down, replan, or nominal behavior."""
        if risk >= self.stop_risk or uncertainty >= self.stop_uncertainty:
            return SafetyAction("SAFE_STOP", 0.0, False, "risk_or_uncertainty_stop")
        if recoverability <= self.min_recoverability:
            return SafetyAction("SAFE_MODE", 0.25, True, "low_recoverability")
        if risk >= self.replan_risk or uncertainty >= self.replan_uncertainty:
            return SafetyAction("REPLAN", 0.50, True, "risk_or_uncertainty_replan")
        return SafetyAction("NOMINAL", 1.0, False, "within_thresholds")


def run_single_research_episode(request: PlanningRequest) -> dict[str, float | int | str | bool]:
    """Run one deterministic planning episode and return benchmark metrics."""
    start_time = time.perf_counter()
    fields = build_fields(request)
    planner = RiskAwareAStar()
    trajectory, metrics = planner.plan(request.occupancy, request.start, request.goal)
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    supervisor = SafetySupervisor()
    terminal = trajectory.poses[-1] if trajectory.poses else request.start
    action = supervisor.decide(
        trajectory.risk,
        float(fields.uncertainty[terminal.y, terminal.x]),
        trajectory.recoverability,
    )
    return {
        "seed": request.seed,
        "path_found": metrics.path_found,
        "path_length": trajectory.length,
        "planning_cost": trajectory.cost,
        "expanded_nodes": metrics.expanded_nodes,
        "terminal_risk": trajectory.risk,
        "terminal_recoverability": trajectory.recoverability,
        "planning_time_ms": elapsed_ms,
        "safety_mode": action.mode,
    }
