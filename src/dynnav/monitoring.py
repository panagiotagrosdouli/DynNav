"""Runtime monitoring and safe-mode supervision."""

from __future__ import annotations

from dataclasses import dataclass

from dynnav.core import GridMap, Pose, Trajectory


@dataclass(frozen=True, slots=True)
class MonitorState:
    """Runtime monitor output."""

    safe: bool
    reason: str
    risk: float
    recoverability: float


@dataclass(slots=True)
class RuntimeMonitor:
    """Check trajectory risk and local obstacle probability online."""

    max_risk: float = 0.6
    min_recoverability: float = 0.35
    max_local_occupancy: float = 0.7

    def evaluate(
        self,
        grid: GridMap,
        pose: Pose,
        trajectory: Trajectory,
    ) -> MonitorState:
        """Evaluate safety invariants at the current pose."""
        local_probability = grid.probability(pose)
        if local_probability > self.max_local_occupancy:
            return MonitorState(
                False,
                "local_collision_probability",
                trajectory.risk,
                trajectory.recoverability,
            )
        if trajectory.risk > self.max_risk:
            return MonitorState(
                False,
                "mission_risk",
                trajectory.risk,
                trajectory.recoverability,
            )
        if trajectory.recoverability < self.min_recoverability:
            return MonitorState(
                False,
                "low_recoverability",
                trajectory.risk,
                trajectory.recoverability,
            )
        return MonitorState(True, "nominal", trajectory.risk, trajectory.recoverability)


@dataclass(slots=True)
class SafeModeSupervisor:
    """Conservative supervisor that switches behavior on monitor violations."""

    monitor: RuntimeMonitor

    def mode(self, grid: GridMap, pose: Pose, trajectory: Trajectory) -> str:
        """Return `nominal`, `slow`, or `stop` based on monitor state."""
        state = self.monitor.evaluate(grid, pose, trajectory)
        if state.safe:
            return "nominal"
        if state.reason in {"mission_risk", "low_recoverability"}:
            return "slow"
        return "stop"
