"""ROS OccupancyGrid geometry for C01. Pure Python; no ROS import.

This produces planning-only paths, NOT robot motion or certified clearance.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
import numpy as np

Node = tuple[int, int]


@dataclass(frozen=True)
class GridGeometry:
    resolution: float
    origin_x: float
    origin_y: float
    origin_yaw: float
    frame_id: str

    def __post_init__(self):
        if not math.isfinite(self.resolution) or self.resolution <= 0:
            raise ValueError("resolution must be finite and positive")
        if not all(math.isfinite(x) for x in (self.origin_x, self.origin_y, self.origin_yaw)):
            raise ValueError("origin must be finite")
        if not self.frame_id:
            raise ValueError("frame_id is required")

    def world_to_cell(self, x: float, y: float) -> Node:
        if not all(math.isfinite(v) for v in (x, y)):
            raise ValueError("world coordinates must be finite")
        dx, dy = x - self.origin_x, y - self.origin_y
        c, s = math.cos(self.origin_yaw), math.sin(self.origin_yaw)
        return (math.floor((c*dx + s*dy) / self.resolution),
                math.floor((-s*dx + c*dy) / self.resolution))

    def cell_to_world(self, x: int, y: int) -> tuple[float, float]:
        lx, ly = (x + 0.5)*self.resolution, (y + 0.5)*self.resolution
        c, s = math.cos(self.origin_yaw), math.sin(self.origin_yaw)
        return self.origin_x + c*lx - s*ly, self.origin_y + s*lx + c*ly


def quaternion_yaw(x: float, y: float, z: float, w: float) -> float:
    norm = math.sqrt(x*x + y*y + z*z + w*w)
    if not math.isfinite(norm) or norm < 1e-10:
        raise ValueError("invalid ROS origin quaternion")
    x, y, z, w = x/norm, y/norm, z/norm, w/norm
    roll = math.atan2(2*(w*x + y*z), 1 - 2*(x*x + y*y))
    pitch_sin = 2*(w*y-z*x)
    if abs(roll) > 1e-5 or abs(pitch_sin) > 1e-5:
        raise ValueError("2D map origin must have zero roll and pitch")
    return math.atan2(2*(w*z+x*y), 1 - 2*(y*y+z*z))


def grid_from_occupancy(flat, width: int, height: int, *,
                        lethal_threshold: int = 50, inflation_cells: int = 0) -> np.ndarray:
    """Unknown (-1) is blocked. Values are ROS row-major, increasing y by row."""
    if width < 1 or height < 1 or width*height != len(flat):
        raise ValueError("OccupancyGrid shape and data disagree")
    if not 1 <= lethal_threshold <= 100:
        raise ValueError("lethal threshold must be in [1,100]")
    if not 0 <= inflation_cells <= 20:
        raise ValueError("inflation radius must be in [0,20] cells")
    raw = np.asarray(flat, dtype=np.int16).reshape(height, width)
    if np.any(raw < -1) or np.any(raw > 100):
        raise ValueError("invalid OccupancyGrid probability")
    blocked = np.logical_or(raw < 0, raw >= lethal_threshold)
    grid = blocked.copy()
    for dy in range(-inflation_cells, inflation_cells+1):
        for dx in range(-inflation_cells, inflation_cells+1):
            if dx*dx+dy*dy > inflation_cells*inflation_cells:
                continue
            dst_y = slice(max(0,dy), height+min(0,dy))
            dst_x = slice(max(0,dx), width+min(0,dx))
            src_y = slice(max(0,-dy), height-max(0,dy))
            src_x = slice(max(0,-dx), width-max(0,dx))
            grid[dst_y,dst_x] |= blocked[src_y,src_x]
    return grid.astype(np.uint8)


def validated_plan(grid: np.ndarray, start: Node, goal: Node, planner):
    if not isinstance(grid, np.ndarray) or grid.ndim != 2 or not grid.size:
        raise ValueError("nonempty 2D occupancy grid required")
    height, width = grid.shape
    for label, (x,y) in (("start",start),("goal",goal)):
        if not (0<=x<width and 0<=y<height) or grid[y,x] != 0:
            raise ValueError(f"{label} is blocked or outside the grid")
    path, expansions = planner(grid,start,goal)
    if path:
        if path[0] != start or path[-1] != goal:
            raise AssertionError("wrong planning endpoints")
        if any(abs(a[0]-b[0])+abs(a[1]-b[1]) != 1 for a,b in zip(path,path[1:])):
            raise AssertionError("nonadjacent path")
        if any(grid[y,x] != 0 for x,y in path):
            raise AssertionError("path intersects an obstacle")
    return path, expansions
