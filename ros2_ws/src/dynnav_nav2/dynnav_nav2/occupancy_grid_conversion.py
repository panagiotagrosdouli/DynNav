"""Conversion helpers from ROS OccupancyGrid-style data to DynNav GridMap."""

from __future__ import annotations

from dataclasses import dataclass

from dynnav.planners import GridMap


@dataclass(frozen=True)
class OccupancyGridSpec:
    """ROS-like occupancy grid data without requiring ROS message imports."""

    width: int
    height: int
    data: tuple[int, ...]
    occupied_threshold: int = 65
    unknown_is_obstacle: bool = False

    def validate(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("width and height must be positive")
        if len(self.data) != self.width * self.height:
            raise ValueError("data length must equal width * height")
        if not 0 <= self.occupied_threshold <= 100:
            raise ValueError("occupied_threshold must be in [0, 100]")


def occupancy_index_to_cell(index: int, width: int) -> tuple[int, int]:
    """Convert row-major OccupancyGrid index to `(x, y)` cell."""
    if width <= 0:
        raise ValueError("width must be positive")
    return index % width, index // width


def occupancy_value_to_risk(value: int) -> float:
    """Map occupancy value to normalized risk.

    ROS OccupancyGrid convention:
    - -1 means unknown;
    - 0 means free;
    - 100 means occupied.
    """
    if value < 0:
        return 0.5
    return max(0.0, min(1.0, value / 100.0))


def occupancy_grid_spec_to_grid_map(spec: OccupancyGridSpec) -> GridMap:
    """Convert a ROS-like occupancy grid spec to DynNav GridMap."""
    spec.validate()
    obstacles: set[tuple[int, int]] = set()
    risk: dict[tuple[int, int], float] = {}
    uncertainty: dict[tuple[int, int], float] = {}

    for index, value in enumerate(spec.data):
        cell = occupancy_index_to_cell(index, spec.width)
        if value < 0:
            uncertainty[cell] = 1.0
            risk[cell] = 0.5
            if spec.unknown_is_obstacle:
                obstacles.add(cell)
        else:
            risk[cell] = occupancy_value_to_risk(value)
            uncertainty[cell] = 0.0
            if value >= spec.occupied_threshold:
                obstacles.add(cell)

    return GridMap.from_obstacles(
        width=spec.width,
        height=spec.height,
        obstacles=obstacles,
        risk=risk,
        uncertainty=uncertainty,
    )


def occupancy_grid_msg_to_spec(msg, occupied_threshold: int = 65, unknown_is_obstacle: bool = False) -> OccupancyGridSpec:
    """Convert a nav_msgs/OccupancyGrid message into a ROS-free spec."""
    return OccupancyGridSpec(
        width=int(msg.info.width),
        height=int(msg.info.height),
        data=tuple(int(value) for value in msg.data),
        occupied_threshold=occupied_threshold,
        unknown_is_obstacle=unknown_is_obstacle,
    )
