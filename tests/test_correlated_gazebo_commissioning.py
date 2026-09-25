from __future__ import annotations

import gzip
import json
from pathlib import Path

from dynnav.experiments.correlated_gazebo_commissioning import (
    commission_second_blocker,
    load_costmap_snapshot,
)


def _write_snapshot(path: Path, *, data: list[int], width: int, height: int) -> None:
    payload = {
        "resolution": 1.0,
        "size_x": width,
        "size_y": height,
        "origin": {"x": 0.0, "y": 0.0},
        "data": data,
    }
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        json.dump(payload, handle)


def test_load_costmap_snapshot_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "snapshot.json.gz"
    _write_snapshot(path, data=[0, 0, 254, 0], width=2, height=2)
    snapshot = load_costmap_snapshot(path)
    assert snapshot.width == 2
    assert snapshot.height == 2
    assert snapshot.data == (0, 0, 254, 0)


def test_commissioner_runs_on_retained_style_snapshots(tmp_path: Path) -> None:
    width, height = 7, 5
    base = [254] * (width * height)
    # Two horizontal return corridors joined at left/right.
    for x in range(width):
        base[1 * width + x] = 0
        base[3 * width + x] = 0
    base[2 * width + 0] = 0
    base[2 * width + 6] = 0

    first = list(base)
    second = list(base)
    # Separate single-blocker snapshots; the cellwise minimum reconstructs base.
    first[1 * width + 3] = 254
    second[3 * width + 5] = 254

    p1 = tmp_path / "first.json.gz"
    p2 = tmp_path / "second.json.gz"
    _write_snapshot(p1, data=first, width=width, height=height)
    _write_snapshot(p2, data=second, width=width, height=height)

    result = commission_second_blocker(
        return_snapshot_path=p1,
        forward_snapshot_path=p2,
        first_blocker_pose=(3.5, 1.5),
        blocker_size=(0.9, 0.9),
        query_world=(6.5, 2.5),
        safe_center=(0.5, 2.5),
        safe_radius_m=0.49,
        anchor_world=(3.5, 3.5),
        search_radius_m=4.0,
    )
    preferred = result["preferred_parallel_redundant"]
    assert preferred is not None
    assert (
        preferred["f00"],
        preferred["f10"],
        preferred["f01"],
        preferred["f11"],
    ) == (1, 1, 1, 0)
    assert preferred["interaction"] == -1
