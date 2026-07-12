"""Probabilistic occupancy-grid mapping for DynNav.

The implementation is middleware-independent so it can be tested deterministically and
adapted to ROS 2 messages without importing ROS packages into the algorithmic core.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final

import numpy as np
from numpy.typing import NDArray

GridIndex = tuple[int, int]
WorldPoint = tuple[float, float]
FloatGrid = NDArray[np.float64]
BoolGrid = NDArray[np.bool_]
Int8Grid = NDArray[np.int8]

_EPSILON: Final[float] = 1.0e-12


@dataclass(frozen=True, slots=True)
class OccupancyGridMetadata:
    """Geometry and coordinate-frame metadata for an occupancy grid."""

    width: int
    height: int
    resolution: float
    origin_x: float = 0.0
    origin_y: float = 0.0
    frame_id: str = "map"

    def __post_init__(self) -> None:
        """Validate grid dimensions and coordinate metadata."""
        if self.width <= 0 or self.height <= 0:
            raise ValueError("width and height must be positive")
        if not math.isfinite(self.resolution) or self.resolution <= 0.0:
            raise ValueError("resolution must be finite and positive")
        if not math.isfinite(self.origin_x) or not math.isfinite(self.origin_y):
            raise ValueError("grid origin must be finite")
        if not self.frame_id:
            raise ValueError("frame_id must be non-empty")


@dataclass(frozen=True, slots=True)
class InverseSensorModel:
    """Log-odds inverse sensor model for planar range measurements."""

    free_probability: float = 0.30
    occupied_probability: float = 0.70
    prior_probability: float = 0.50
    minimum_probability: float = 0.03
    maximum_probability: float = 0.97

    def __post_init__(self) -> None:
        """Validate probability ordering and numerical bounds."""
        probabilities = (
            self.free_probability,
            self.occupied_probability,
            self.prior_probability,
            self.minimum_probability,
            self.maximum_probability,
        )
        if any(not math.isfinite(value) or not 0.0 < value < 1.0 for value in probabilities):
            raise ValueError(
                "sensor-model probabilities must be finite and strictly inside (0, 1)"
            )
        if self.free_probability >= self.prior_probability:
            raise ValueError("free_probability must be lower than prior_probability")
        if self.occupied_probability <= self.prior_probability:
            raise ValueError("occupied_probability must exceed prior_probability")
        if self.minimum_probability >= self.prior_probability:
            raise ValueError("minimum_probability must be lower than prior_probability")
        if self.maximum_probability <= self.prior_probability:
            raise ValueError("maximum_probability must exceed prior_probability")
        if self.minimum_probability >= self.maximum_probability:
            raise ValueError("minimum_probability must be lower than maximum_probability")

    @staticmethod
    def _logit(probability: float) -> float:
        return math.log(probability / (1.0 - probability))

    @property
    def prior_log_odds(self) -> float:
        """Return the prior occupancy belief in log-odds form."""
        return self._logit(self.prior_probability)

    @property
    def free_increment(self) -> float:
        """Return additive free-space evidence relative to the prior."""
        return self._logit(self.free_probability) - self.prior_log_odds

    @property
    def occupied_increment(self) -> float:
        """Return additive occupied-space evidence relative to the prior."""
        return self._logit(self.occupied_probability) - self.prior_log_odds

    @property
    def minimum_log_odds(self) -> float:
        """Return the lower saturation bound in log-odds form."""
        return self._logit(self.minimum_probability)

    @property
    def maximum_log_odds(self) -> float:
        """Return the upper saturation bound in log-odds form."""
        return self._logit(self.maximum_probability)


@dataclass(frozen=True, slots=True)
class PlanarLaserScan:
    """Middleware-neutral planar laser scan."""

    ranges: tuple[float, ...]
    angle_min: float
    angle_increment: float
    range_min: float
    range_max: float
    timestamp: float

    def __post_init__(self) -> None:
        """Validate scan geometry and timestamps."""
        if not self.ranges:
            raise ValueError("ranges must not be empty")
        metadata = (
            self.angle_min,
            self.angle_increment,
            self.range_min,
            self.range_max,
            self.timestamp,
        )
        if any(not math.isfinite(value) for value in metadata):
            raise ValueError("scan metadata must be finite")
        if self.angle_increment == 0.0:
            raise ValueError("angle_increment must be non-zero")
        if self.range_min < 0.0 or self.range_max <= self.range_min:
            raise ValueError("range bounds are invalid")


@dataclass(frozen=True, slots=True)
class MappingUpdateStats:
    """Diagnostics emitted by one occupancy-grid update."""

    processed_beams: int
    ignored_beams: int
    free_cell_updates: int
    occupied_cell_updates: int
    touched_cells: int


class OccupancyBeliefGrid:
    """Bayesian occupancy belief grid using bounded additive log odds."""

    def __init__(
        self,
        metadata: OccupancyGridMetadata,
        sensor_model: InverseSensorModel | None = None,
    ) -> None:
        """Create a grid initialized to the configured prior probability."""
        self.metadata = metadata
        self.sensor_model = sensor_model or InverseSensorModel()
        shape = (metadata.height, metadata.width)
        self._log_odds: FloatGrid = np.full(
            shape,
            self.sensor_model.prior_log_odds,
            dtype=np.float64,
        )
        self._observed: BoolGrid = np.zeros(shape, dtype=np.bool_)
        self._last_observed: FloatGrid = np.full(shape, -np.inf, dtype=np.float64)

    @property
    def shape(self) -> tuple[int, int]:
        """Return array shape as ``(height, width)``."""
        return self.metadata.height, self.metadata.width

    @property
    def log_odds(self) -> FloatGrid:
        """Return a read-only view of the log-odds field."""
        view = self._log_odds.view()
        view.flags.writeable = False
        return view

    @property
    def observed_mask(self) -> BoolGrid:
        """Return a read-only Boolean view of cells observed at least once."""
        view = self._observed.view()
        view.flags.writeable = False
        return view

    def in_bounds(self, index: GridIndex) -> bool:
        """Return whether ``index`` lies inside the grid."""
        x, y = index
        return 0 <= x < self.metadata.width and 0 <= y < self.metadata.height

    def world_to_grid(self, point: WorldPoint) -> GridIndex | None:
        """Convert a world coordinate to a grid index, or return ``None`` outside."""
        x, y = point
        if not math.isfinite(x) or not math.isfinite(y):
            raise ValueError("world coordinates must be finite")
        grid_x = math.floor((x - self.metadata.origin_x) / self.metadata.resolution)
        grid_y = math.floor((y - self.metadata.origin_y) / self.metadata.resolution)
        index = (grid_x, grid_y)
        return index if self.in_bounds(index) else None

    def grid_to_world(self, index: GridIndex) -> WorldPoint:
        """Return the world coordinate of a cell center."""
        if not self.in_bounds(index):
            raise IndexError(f"grid index outside map: {index!r}")
        x, y = index
        return (
            self.metadata.origin_x + (x + 0.5) * self.metadata.resolution,
            self.metadata.origin_y + (y + 0.5) * self.metadata.resolution,
        )

    def probability(self, index: GridIndex) -> float:
        """Return the occupancy probability at a grid index."""
        if not self.in_bounds(index):
            raise IndexError(f"grid index outside map: {index!r}")
        x, y = index
        value = float(self._log_odds[y, x])
        return 1.0 / (1.0 + math.exp(-value))

    def probability_grid(self) -> FloatGrid:
        """Return a copy of all occupancy probabilities."""
        positive = self._log_odds >= 0.0
        probabilities: FloatGrid = np.empty_like(self._log_odds)
        probabilities[positive] = 1.0 / (1.0 + np.exp(-self._log_odds[positive]))
        exponential = np.exp(self._log_odds[~positive])
        probabilities[~positive] = exponential / (1.0 + exponential)
        return probabilities

    def occupancy_values(
        self,
        free_threshold: float = 0.35,
        occupied_threshold: float = 0.65,
    ) -> Int8Grid:
        """Return ROS-compatible values: unknown ``-1``, free ``0``, occupied ``100``."""
        if not 0.0 <= free_threshold < occupied_threshold <= 1.0:
            raise ValueError("thresholds must satisfy 0 <= free < occupied <= 1")
        probabilities = self.probability_grid()
        values: Int8Grid = np.rint(probabilities * 100.0).astype(np.int8)
        values[probabilities <= free_threshold] = 0
        values[probabilities >= occupied_threshold] = 100
        values[~self._observed] = -1
        return values

    def update_scan(
        self,
        sensor_position: WorldPoint,
        sensor_yaw: float,
        scan: PlanarLaserScan,
    ) -> MappingUpdateStats:
        """Fuse one planar scan into the map."""
        if not math.isfinite(sensor_yaw):
            raise ValueError("sensor_yaw must be finite")
        origin = self.world_to_grid(sensor_position)
        if origin is None:
            raise ValueError("sensor_position lies outside the occupancy grid")

        processed = 0
        ignored = 0
        free_updates = 0
        occupied_updates = 0
        touched: set[GridIndex] = set()

        for beam_index, measured_range in enumerate(scan.ranges):
            if (
                math.isnan(measured_range)
                or measured_range <= 0.0
                or measured_range < scan.range_min
            ):
                ignored += 1
                continue

            has_hit = math.isfinite(measured_range) and measured_range < scan.range_max
            effective_range = (
                min(measured_range, scan.range_max)
                if math.isfinite(measured_range)
                else scan.range_max
            )
            angle = sensor_yaw + scan.angle_min + beam_index * scan.angle_increment
            endpoint_world = (
                sensor_position[0] + effective_range * math.cos(angle),
                sensor_position[1] + effective_range * math.sin(angle),
            )
            endpoint = self.world_to_grid(endpoint_world)
            if endpoint is None:
                endpoint = self._clip_endpoint(origin, endpoint_world)
                has_hit = False
            if endpoint is None:
                ignored += 1
                continue

            ray = self._bresenham(origin, endpoint)
            free_cells = ray[1:-1] if has_hit else ray[1:]
            for cell in free_cells:
                self._add_evidence(cell, self.sensor_model.free_increment, scan.timestamp)
                free_updates += 1
                touched.add(cell)

            if has_hit and endpoint != origin:
                self._add_evidence(
                    endpoint,
                    self.sensor_model.occupied_increment,
                    scan.timestamp,
                )
                occupied_updates += 1
                touched.add(endpoint)
            processed += 1

        return MappingUpdateStats(
            processed_beams=processed,
            ignored_beams=ignored,
            free_cell_updates=free_updates,
            occupied_cell_updates=occupied_updates,
            touched_cells=len(touched),
        )

    def decay_dynamic_evidence(
        self,
        current_time: float,
        half_life: float,
        stale_after: float = 0.0,
    ) -> int:
        """Exponentially relax stale evidence toward the prior belief."""
        if not math.isfinite(current_time):
            raise ValueError("current_time must be finite")
        if not math.isfinite(half_life) or half_life <= 0.0:
            raise ValueError("half_life must be finite and positive")
        if not math.isfinite(stale_after) or stale_after < 0.0:
            raise ValueError("stale_after must be finite and non-negative")

        age = current_time - self._last_observed
        stale = self._observed & (age > stale_after)
        if not bool(np.any(stale)):
            return 0
        effective_age = np.maximum(age[stale] - stale_after, 0.0)
        retention = np.exp2(-effective_age / half_life)
        prior = self.sensor_model.prior_log_odds
        self._log_odds[stale] = prior + (self._log_odds[stale] - prior) * retention
        return int(np.count_nonzero(stale))

    def _add_evidence(self, index: GridIndex, increment: float, timestamp: float) -> None:
        x, y = index
        updated = float(self._log_odds[y, x]) + increment
        self._log_odds[y, x] = np.float64(
            min(
                max(updated, self.sensor_model.minimum_log_odds),
                self.sensor_model.maximum_log_odds,
            )
        )
        self._observed[y, x] = True
        self._last_observed[y, x] = max(float(self._last_observed[y, x]), timestamp)

    def _clip_endpoint(
        self,
        origin: GridIndex,
        endpoint_world: WorldPoint,
    ) -> GridIndex | None:
        """Return the final in-bounds cell along a ray leaving the map."""
        origin_world = self.grid_to_world(origin)
        delta_x = endpoint_world[0] - origin_world[0]
        delta_y = endpoint_world[1] - origin_world[1]
        distance = math.hypot(delta_x, delta_y)
        if distance <= _EPSILON:
            return origin
        steps = max(1, math.ceil(distance / (0.5 * self.metadata.resolution)))
        last_inside: GridIndex | None = origin
        for step in range(1, steps + 1):
            ratio = step / steps
            candidate = self.world_to_grid(
                (
                    origin_world[0] + ratio * delta_x,
                    origin_world[1] + ratio * delta_y,
                )
            )
            if candidate is None:
                break
            last_inside = candidate
        return last_inside

    @staticmethod
    def _bresenham(start: GridIndex, end: GridIndex) -> list[GridIndex]:
        """Return every integer grid cell intersected by a discrete line segment."""
        x0, y0 = start
        x1, y1 = end
        cells: list[GridIndex] = []
        delta_x = abs(x1 - x0)
        step_x = 1 if x0 < x1 else -1
        delta_y = -abs(y1 - y0)
        step_y = 1 if y0 < y1 else -1
        error = delta_x + delta_y

        while True:
            cells.append((x0, y0))
            if x0 == x1 and y0 == y1:
                break
            doubled_error = 2 * error
            if doubled_error >= delta_y:
                error += delta_y
                x0 += step_x
            if doubled_error <= delta_x:
                error += delta_x
                y0 += step_y
        return cells
