"""Helpers for converting DynNav grid paths to ROS path messages."""

from __future__ import annotations


def grid_cell_to_world(cell: tuple[int, int], resolution_m: float) -> tuple[float, float]:
    """Convert a grid cell center to a map-frame world coordinate."""
    if resolution_m <= 0.0:
        raise ValueError("resolution_m must be positive")
    x, y = cell
    return (x + 0.5) * resolution_m, (y + 0.5) * resolution_m


def grid_path_to_world(path: list[tuple[int, int]], resolution_m: float) -> list[tuple[float, float]]:
    """Convert a grid-cell path to world coordinates."""
    return [grid_cell_to_world(cell, resolution_m) for cell in path]


def build_nav_path_message(path, frame_id: str, resolution_m: float, stamp=None):
    """Build a nav_msgs/Path message from grid cells.

    ROS message imports are local so this helper can be imported in non-ROS test
    environments for the pure coordinate-conversion functions.
    """
    from geometry_msgs.msg import PoseStamped
    from nav_msgs.msg import Path

    msg = Path()
    msg.header.frame_id = frame_id
    if stamp is not None:
        msg.header.stamp = stamp

    for cell in path:
        pose = PoseStamped()
        pose.header.frame_id = frame_id
        if stamp is not None:
            pose.header.stamp = stamp
        x, y = grid_cell_to_world(cell, resolution_m)
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = 0.0
        pose.pose.orientation.w = 1.0
        msg.poses.append(pose)
    return msg
