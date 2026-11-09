"""Load ROS map_server trinary occupancy maps into DynNav's grid model."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import yaml
from PIL import Image

from dynnav.planners.grid_map import GridCell, GridMap


@dataclass(frozen=True)
class RosMap:
    """A DynNav grid with the ROS map's world-coordinate geometry."""

    grid: GridMap
    resolution: float
    origin_x: float
    origin_y: float
    origin_yaw: float

    def world_to_cell(self, x: float, y: float) -> GridCell:
        """Convert a map-frame point to a row-major DynNav cell."""
        dx = x - self.origin_x
        dy = y - self.origin_y
        cosine = math.cos(self.origin_yaw)
        sine = math.sin(self.origin_yaw)
        local_x = cosine * dx + sine * dy
        local_y = -sine * dx + cosine * dy
        return (math.floor(local_x / self.resolution), math.floor(local_y / self.resolution))

    def cell_center(self, cell: GridCell) -> tuple[float, float]:
        """Convert a DynNav cell to its map-frame center point."""
        cell_x, cell_y = cell
        local_x = (cell_x + 0.5) * self.resolution
        local_y = (cell_y + 0.5) * self.resolution
        cosine = math.cos(self.origin_yaw)
        sine = math.sin(self.origin_yaw)
        return (
            self.origin_x + cosine * local_x - sine * local_y,
            self.origin_y + sine * local_x + cosine * local_y,
        )


def load_ros_map(yaml_path: str | Path, *, unknown_as_obstacle: bool = True) -> RosMap:
    """Load a ROS map_server trinary map and conservatively handle unknowns.

    ROS occupancy images are stored with the image origin at the top-left,
    while ROS map coordinates start at the bottom-left. This function flips
    that axis and applies the YAML ``negate`` and occupancy thresholds.
    """
    metadata_path = Path(yaml_path).expanduser().resolve()
    with metadata_path.open(encoding="utf-8") as stream:
        metadata = yaml.safe_load(stream)
    if not isinstance(metadata, dict):
        raise ValueError("ROS map YAML must contain a mapping")

    mode = metadata.get("mode", "trinary")
    if mode != "trinary":
        raise ValueError(f"only ROS trinary maps are supported, got mode={mode!r}")

    image_name = metadata.get("image")
    if not isinstance(image_name, str) or not image_name:
        raise ValueError("ROS map YAML must define a non-empty image path")
    image_path = (metadata_path.parent / image_name).resolve()
    resolution = float(metadata["resolution"])
    origin = metadata["origin"]
    if not isinstance(origin, list) or len(origin) != 3:
        raise ValueError("ROS map origin must contain [x, y, yaw]")
    origin_x, origin_y, origin_yaw = (float(value) for value in origin)
    free_threshold = float(metadata.get("free_thresh", 0.196))
    occupied_threshold = float(metadata.get("occupied_thresh", 0.65))
    if not 0.0 <= free_threshold < occupied_threshold <= 1.0:
        raise ValueError("ROS map thresholds must satisfy 0 <= free < occupied <= 1")
    if not math.isfinite(resolution) or resolution <= 0.0:
        raise ValueError("ROS map resolution must be finite and positive")
    if any(not math.isfinite(value) for value in (origin_x, origin_y, origin_yaw)):
        raise ValueError("ROS map origin values must be finite")

    with Image.open(image_path) as image:
        pixels = np.asarray(image.convert("L"), dtype=np.float64)
    occupancy = pixels / 255.0 if bool(metadata.get("negate", 0)) else (255.0 - pixels) / 255.0
    occupancy = np.flipud(occupancy)
    occupied = occupancy >= occupied_threshold
    free = occupancy <= free_threshold
    unknown = ~(occupied | free)
    if unknown_as_obstacle:
        blocked = occupied | unknown
    else:
        blocked = occupied

    height, width = occupancy.shape
    obstacle_indices = np.argwhere(blocked)
    obstacles = frozenset((int(column), int(row)) for row, column in obstacle_indices)
    return RosMap(
        grid=GridMap.from_obstacles(width=width, height=height, obstacles=obstacles),
        resolution=resolution,
        origin_x=origin_x,
        origin_y=origin_y,
        origin_yaw=origin_yaw,
    )
