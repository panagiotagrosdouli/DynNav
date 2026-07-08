"""ROS 2 integration boundary for DynNav.

This module intentionally avoids importing ROS 2 packages at module import time so
the core research package remains testable in non-ROS CI environments. Concrete
adapters should live behind optional dependencies and convert ROS messages into
`dynnav.core` primitives.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dynnav.core import GridMap, Pose, Trajectory


@dataclass(frozen=True, slots=True)
class Ros2NavigationCommand:
    """Middleware-neutral command emitted by DynNav before ROS conversion."""

    mode: str
    target: Pose | None
    reason: str = ""


class Ros2Adapter:
    """Boundary class for future ROS 2 / Nav2 integration."""

    def occupancy_from_message(self, message: Any) -> GridMap:
        """Convert a ROS occupancy message into a DynNav grid.

        This placeholder documents the integration contract. A concrete adapter
        should parse nav_msgs/OccupancyGrid and preserve unknown cells as
        probabilities rather than forcing a binary map.
        """
        raise NotImplementedError("ROS 2 message conversion requires optional ROS dependencies")

    def command_from_trajectory(self, trajectory: Trajectory, mode: str = "nominal") -> Ros2NavigationCommand:
        """Convert a trajectory into a middleware-neutral navigation command."""
        target = trajectory.poses[1] if len(trajectory.poses) > 1 else None
        return Ros2NavigationCommand(mode=mode, target=target)
