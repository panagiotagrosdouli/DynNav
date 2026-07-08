"""Risk-aware planning, rerouting, and planner-switching prototypes."""

from __future__ import annotations

import heapq
from dataclasses import dataclass

from dynnav.core import GridMap, Pose, Trajectory
from dynnav.risk import mission_risk


def manhattan(a: Pose, b: Pose) -> int:
    """Return Manhattan distance between two grid poses."""
    return abs(a.x - b.x) + abs(a.y - b.y)


@dataclass(frozen=True, slots=True)
class PlanningMetrics:
    """Metrics emitted by planners and benchmarks."""

    expanded_nodes: int
    replans: int
    path_found: bool
    terminal_risk: float


class NavigationPolicy:
    """Abstract navigation-policy interface."""

    def plan(
        self,
        grid: GridMap,
        start: Pose,
        goal: Pose,
    ) -> tuple[Trajectory, PlanningMetrics]:
        """Plan a trajectory. Subclasses should override this method."""
        raise NotImplementedError


@dataclass(slots=True)
class RiskAwareAStar(NavigationPolicy):
    """A* planner with occupancy-risk and returnability penalties."""

    risk_weight: float = 4.0
    returnability_weight: float = 1.5
    alpha: float = 0.9
    max_expansions: int = 10000
    estimate_recoverability: bool = True

    def plan(
        self,
        grid: GridMap,
        start: Pose,
        goal: Pose,
    ) -> tuple[Trajectory, PlanningMetrics]:
        """Plan a risk-aware trajectory from start to goal."""
        frontier: list[tuple[float, int, Pose]] = [(0.0, 0, start)]
        came_from: dict[Pose, Pose | None] = {start: None}
        cost_so_far: dict[Pose, float] = {start: 0.0}
        expanded = 0
        push_order = 0

        while frontier and expanded < self.max_expansions:
            _, _, current = heapq.heappop(frontier)
            expanded += 1
            if current == goal:
                break

            for neighbor in grid.neighbors4(current):
                occupancy = grid.probability(neighbor)
                if occupancy >= 0.98:
                    continue

                returnability_penalty = self._returnability_penalty(
                    grid,
                    neighbor,
                    start,
                )
                step_cost = 1.0 + self.risk_weight * occupancy + returnability_penalty
                new_cost = cost_so_far[current] + step_cost

                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    priority = new_cost + manhattan(neighbor, goal)
                    push_order += 1
                    heapq.heappush(frontier, (priority, push_order, neighbor))
                    came_from[neighbor] = current

        if goal not in came_from:
            traj = Trajectory((start,), float("inf"), 1.0, 0.0)
            return traj, PlanningMetrics(expanded, 0, False, 1.0)

        path = self._reconstruct(came_from, goal)
        probabilities = [grid.probability(pose) for pose in path]
        risk = mission_risk(probabilities, alpha=self.alpha)
        recoverability = 1.0
        if self.estimate_recoverability:
            recoverability = RecoverabilityEstimator().score(grid, path, start)
        traj = Trajectory(tuple(path), cost_so_far[goal], risk, recoverability)
        return traj, PlanningMetrics(expanded, 0, True, risk)

    def _returnability_penalty(self, grid: GridMap, pose: Pose, start: Pose) -> float:
        local_degree = sum(
            1 for n in grid.neighbors4(pose) if grid.probability(n) < 0.65
        )
        bottleneck = max(0, 2 - local_degree)
        distance = manhattan(pose, start)
        return self.returnability_weight * bottleneck * (1.0 + 0.01 * distance)

    @staticmethod
    def _reconstruct(came_from: dict[Pose, Pose | None], goal: Pose) -> list[Pose]:
        path = [goal]
        current = goal
        while came_from[current] is not None:
            current = came_from[current]  # type: ignore[assignment]
            path.append(current)
        path.reverse()
        return path


class RecoverabilityEstimator:
    """Estimate whether a path preserves a route back to a safe origin."""

    def score(self, grid: GridMap, path: list[Pose], origin: Pose) -> float:
        """Return a score in [0, 1], higher means easier recovery."""
        if not path:
            return 0.0

        planner = RiskAwareAStar(
            risk_weight=1.0,
            returnability_weight=0.0,
            max_expansions=3000,
            estimate_recoverability=False,
        )
        sample_step = max(1, len(path) // 8)
        sampled_poses = path[::sample_step]
        successes = 0

        for pose in sampled_poses:
            trajectory, metrics = planner.plan(grid, pose, origin)
            if metrics.path_found and trajectory.risk < 0.65:
                successes += 1

        return successes / max(len(sampled_poses), 1)


@dataclass(slots=True)
class DynamicRerouter:
    """Trigger replanning when risk or monitoring signals degrade."""

    planner: NavigationPolicy
    risk_threshold: float = 0.55
    recoverability_threshold: float = 0.40

    def maybe_replan(
        self,
        grid: GridMap,
        current: Pose,
        goal: Pose,
        active: Trajectory,
    ) -> tuple[Trajectory, bool]:
        """Return an updated trajectory and whether replanning occurred."""
        if (
            active.risk <= self.risk_threshold
            and active.recoverability >= self.recoverability_threshold
        ):
            return active, False
        trajectory, _ = self.planner.plan(grid, current, goal)
        return trajectory, True


@dataclass(slots=True)
class PlannerSwitch:
    """Select a planner according to runtime conditions."""

    nominal: NavigationPolicy
    conservative: NavigationPolicy
    risk_threshold: float = 0.5

    def select(self, estimated_risk: float) -> NavigationPolicy:
        """Return conservative planner when estimated risk is high."""
        if estimated_risk >= self.risk_threshold:
            return self.conservative
        return self.nominal
