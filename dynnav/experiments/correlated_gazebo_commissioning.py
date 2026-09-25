"""Commission a two-blocker Gazebo dependence geometry from retained evidence.

This module never reads comparative outcomes from the new robust planner.  It
uses two retained 2026-08-11 global-costmap snapshots, each containing a
different pre-existing dynamic blocker, to reconstruct a conservative static
baseline by cell-wise minimum.  Candidate second blocker poses are then scored
only by deterministic return-connectivity truth tables.

The preferred geometry is parallel-redundant:
    f00 = f10 = f01 = 1, f11 = 0,
so the two closures are individually survivable but jointly disconnect return
and the dependence interaction kappa is -1.
"""

from __future__ import annotations

import gzip
import json
import math
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CostmapSnapshot:
    resolution: float
    width: int
    height: int
    origin_x: float
    origin_y: float
    data: tuple[int, ...]


@dataclass(frozen=True)
class CommissionedGeometry:
    candidate_cell: tuple[int, int]
    candidate_world: tuple[float, float]
    f00: int
    f10: int
    f01: int
    f11: int
    interaction: int
    distance_to_anchor_m: float
    first_blocked_cells: int
    second_blocked_cells: int


def load_costmap_snapshot(path: str | Path) -> CostmapSnapshot:
    source = Path(path)
    with gzip.open(source, "rt", encoding="utf-8") as handle:
        payload = json.load(handle)
    width = int(payload["size_x"])
    height = int(payload["size_y"])
    data = tuple(int(value) for value in payload["data"])
    if len(data) != width * height:
        raise ValueError("costmap data length does not match dimensions")
    return CostmapSnapshot(
        resolution=float(payload["resolution"]),
        width=width,
        height=height,
        origin_x=float(payload["origin"]["x"]),
        origin_y=float(payload["origin"]["y"]),
        data=data,
    )


def reconstruct_static_baseline(
    first: CostmapSnapshot,
    second: CostmapSnapshot,
) -> CostmapSnapshot:
    for name in ("resolution", "width", "height", "origin_x", "origin_y"):
        if not math.isclose(
            float(getattr(first, name)),
            float(getattr(second, name)),
            rel_tol=0.0,
            abs_tol=1.0e-12,
        ):
            raise ValueError(f"snapshot metadata mismatch: {name}")
    return CostmapSnapshot(
        resolution=first.resolution,
        width=first.width,
        height=first.height,
        origin_x=first.origin_x,
        origin_y=first.origin_y,
        data=tuple(min(a, b) for a, b in zip(first.data, second.data, strict=True)),
    )


def world_to_cell(
    snapshot: CostmapSnapshot,
    x: float,
    y: float,
) -> tuple[int, int]:
    return (
        math.floor((x - snapshot.origin_x) / snapshot.resolution),
        math.floor((y - snapshot.origin_y) / snapshot.resolution),
    )


def cell_center(
    snapshot: CostmapSnapshot,
    cell: tuple[int, int],
) -> tuple[float, float]:
    x, y = cell
    return (
        snapshot.origin_x + (x + 0.5) * snapshot.resolution,
        snapshot.origin_y + (y + 0.5) * snapshot.resolution,
    )


def blocker_footprint_cells(
    snapshot: CostmapSnapshot,
    *,
    center_x: float,
    center_y: float,
    size_x: float,
    size_y: float,
) -> frozenset[int]:
    if size_x <= 0.0 or size_y <= 0.0:
        raise ValueError("blocker dimensions must be positive")
    half_x = size_x / 2.0
    half_y = size_y / 2.0
    min_x, min_y = world_to_cell(snapshot, center_x - half_x, center_y - half_y)
    max_x, max_y = world_to_cell(snapshot, center_x + half_x, center_y + half_y)
    indices: set[int] = set()
    for y in range(max(0, min_y - 1), min(snapshot.height, max_y + 2)):
        for x in range(max(0, min_x - 1), min(snapshot.width, max_x + 2)):
            wx, wy = cell_center(snapshot, (x, y))
            if abs(wx - center_x) <= half_x and abs(wy - center_y) <= half_y:
                indices.add(y * snapshot.width + x)
    return frozenset(indices)


def _reachable(
    snapshot: CostmapSnapshot,
    start: tuple[int, int],
    safe_indices: frozenset[int],
    additionally_blocked: frozenset[int],
    *,
    lethal_threshold: int = 253,
) -> bool:
    sx, sy = start
    if not (0 <= sx < snapshot.width and 0 <= sy < snapshot.height):
        return False
    start_index = sy * snapshot.width + sx
    if start_index in safe_indices:
        return True
    queue: deque[int] = deque([start_index])
    visited = {start_index}
    while queue:
        current = queue.popleft()
        x = current % snapshot.width
        y = current // snapshot.width
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if not (0 <= nx < snapshot.width and 0 <= ny < snapshot.height):
                continue
            index = ny * snapshot.width + nx
            if index in visited or index in additionally_blocked:
                continue
            if snapshot.data[index] >= lethal_threshold:
                continue
            if index in safe_indices:
                return True
            visited.add(index)
            queue.append(index)
    return False


def _safe_region_indices(
    snapshot: CostmapSnapshot,
    *,
    center_x: float,
    center_y: float,
    radius_m: float,
) -> frozenset[int]:
    if radius_m < 0.0:
        raise ValueError("safe-region radius must be non-negative")
    cx, cy = world_to_cell(snapshot, center_x, center_y)
    radius_cells = math.ceil(radius_m / snapshot.resolution) + 1
    result: set[int] = set()
    for y in range(max(0, cy - radius_cells), min(snapshot.height, cy + radius_cells + 1)):
        for x in range(max(0, cx - radius_cells), min(snapshot.width, cx + radius_cells + 1)):
            wx, wy = cell_center(snapshot, (x, y))
            if math.hypot(wx - center_x, wy - center_y) <= radius_m:
                index = y * snapshot.width + x
                if snapshot.data[index] < 253:
                    result.add(index)
    if not result:
        raise ValueError("safe region contains no traversable costmap cells")
    return frozenset(result)


def commission_second_blocker(
    *,
    return_snapshot_path: str | Path,
    forward_snapshot_path: str | Path,
    first_blocker_pose: tuple[float, float] = (-0.95, -0.425),
    blocker_size: tuple[float, float] = (0.35, 1.20),
    query_world: tuple[float, float] = (1.75, 1.0),
    safe_center: tuple[float, float] = (-2.0, -0.5),
    safe_radius_m: float = 0.35,
    anchor_world: tuple[float, float] = (0.9, -0.1),
    search_radius_m: float = 2.5,
) -> dict[str, Any]:
    """Return deterministic commissioning candidates from retained costmaps."""

    first_snapshot = load_costmap_snapshot(return_snapshot_path)
    second_snapshot = load_costmap_snapshot(forward_snapshot_path)
    baseline = reconstruct_static_baseline(first_snapshot, second_snapshot)
    first_closed = blocker_footprint_cells(
        baseline,
        center_x=first_blocker_pose[0],
        center_y=first_blocker_pose[1],
        size_x=blocker_size[0],
        size_y=blocker_size[1],
    )
    query_cell = world_to_cell(baseline, *query_world)
    safe = _safe_region_indices(
        baseline,
        center_x=safe_center[0],
        center_y=safe_center[1],
        radius_m=safe_radius_m,
    )
    if not _reachable(baseline, query_cell, safe, frozenset()):
        raise ValueError("baseline does not connect the query state to the safe region")

    candidates: list[CommissionedGeometry] = []
    for y in range(baseline.height):
        for x in range(baseline.width):
            index = y * baseline.width + x
            if baseline.data[index] >= 253:
                continue
            wx, wy = cell_center(baseline, (x, y))
            distance = math.hypot(wx - anchor_world[0], wy - anchor_world[1])
            if distance > search_radius_m:
                continue
            second_closed = blocker_footprint_cells(
                baseline,
                center_x=wx,
                center_y=wy,
                size_x=blocker_size[0],
                size_y=blocker_size[1],
            )
            if not second_closed or first_closed & second_closed:
                continue
            if any(value in safe for value in second_closed):
                continue
            query_index = query_cell[1] * baseline.width + query_cell[0]
            if query_index in second_closed:
                continue

            f00 = int(_reachable(baseline, query_cell, safe, frozenset()))
            f10 = int(_reachable(baseline, query_cell, safe, first_closed))
            f01 = int(_reachable(baseline, query_cell, safe, second_closed))
            f11 = int(_reachable(baseline, query_cell, safe, first_closed | second_closed))
            interaction = f00 - f10 - f01 + f11
            if interaction == 0:
                continue
            candidates.append(
                CommissionedGeometry(
                    candidate_cell=(x, y),
                    candidate_world=(wx, wy),
                    f00=f00,
                    f10=f10,
                    f01=f01,
                    f11=f11,
                    interaction=interaction,
                    distance_to_anchor_m=distance,
                    first_blocked_cells=len(first_closed),
                    second_blocked_cells=len(second_closed),
                )
            )

    negative = [row for row in candidates if row.interaction < 0]
    positive = [row for row in candidates if row.interaction > 0]
    preferred_pool = [
        row
        for row in negative
        if (row.f00, row.f10, row.f01, row.f11) == (1, 1, 1, 0)
    ]
    preferred = min(
        preferred_pool,
        key=lambda row: (row.distance_to_anchor_m, row.candidate_cell),
        default=None,
    )
    return {
        "source": {
            "return_snapshot": str(return_snapshot_path),
            "forward_snapshot": str(forward_snapshot_path),
            "baseline_rule": "cellwise_minimum_of_two_distinct_single-blocker_retained_snapshots",
        },
        "query_world": list(query_world),
        "query_cell": list(query_cell),
        "safe_center": list(safe_center),
        "safe_radius_m": safe_radius_m,
        "first_blocker_pose": list(first_blocker_pose),
        "blocker_size": list(blocker_size),
        "anchor_world": list(anchor_world),
        "candidate_count_nonzero_interaction": len(candidates),
        "negative_interaction_count": len(negative),
        "positive_interaction_count": len(positive),
        "preferred_parallel_redundant": (
            None if preferred is None else asdict(preferred)
        ),
        "nearest_negative_candidates": [
            asdict(row)
            for row in sorted(
                negative,
                key=lambda row: (row.distance_to_anchor_m, row.candidate_cell),
            )[:20]
        ],
        "nearest_positive_candidates": [
            asdict(row)
            for row in sorted(
                positive,
                key=lambda row: (row.distance_to_anchor_m, row.candidate_cell),
            )[:20]
        ],
    }
