"""ROS 2 integration boundary for DynNav.

The adapter deliberately avoids importing ROS 2 packages at module import time so
the canonical research package remains usable in non-ROS environments.  Message
objects are consumed through the small attribute surface exposed by
``nav_msgs/msg/OccupancyGrid``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from dynnav.core import GridMap, Pose, Trajectory


@dataclass(frozen=True, slots=True)
class Ros2NavigationCommand:
    """Middleware-neutral command emitted by DynNav before ROS conversion."""

    mode: str
    target: Pose | None
    reason: str = ""


class Ros2Adapter:
    """Dependency-light conversion boundary between ROS 2 messages and DynNav."""

    def occupancy_from_message(self, message: Any) -> GridMap:
        """Convert a ROS OccupancyGrid-like message into the canonical grid.

        The conversion follows the ROS row-major occupancy convention. Values in
        ``[0, 100]`` become probabilities in ``[0, 1]``, while unknown
        cells (``-1``) retain uncertainty as probability ``0.5``.  Only the
        standard ``message.info.width``, ``height``, ``resolution`` and
        ``message.data`` attributes are required, so this function remains
        testable without ROS installed.
        """
        try:
            width = int(message.info.width)
            height = int(message.info.height)
            resolution = float(message.info.resolution)
            raw = np.asarray(tuple(message.data), dtype=float)
        except (AttributeError, TypeError, ValueError) as exc:
            raise ValueError("message must provide OccupancyGrid-compatible info and data") from exc

        if width <= 0 or height <= 0:
            raise ValueError("occupancy grid width and height must be positive")
        if raw.size != width * height:
            raise ValueError("occupancy grid data length must equal width * height")

        occupancy = raw.reshape((height, width))
        occupancy = np.where(occupancy < 0.0, 0.5, np.clip(occupancy / 100.0, 0.0, 1.0))
        return GridMap(occupancy=occupancy, resolution=resolution)

    def command_from_trajectory(
        self,
        trajectory: Trajectory,
        mode: str = "nominal",
    ) -> Ros2NavigationCommand:
        """Convert a trajectory into a middleware-neutral navigation command."""
        target = trajectory.poses[1] if len(trajectory.poses) > 1 else None
        return Ros2NavigationCommand(mode=mode, target=target)
