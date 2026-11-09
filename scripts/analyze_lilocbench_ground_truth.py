#!/usr/bin/env python3
"""Summarize a LILocBench public ground-truth pose file (TUM format)."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import median
from typing import Any


SOURCE_URL = (
    "https://www.ipb.uni-bonn.de/html/projects/localization_benchmark/"
    "data/gt_poses_public/dynamics_0/gt_poses.txt"
)


def percentile(values: list[float], probability: float) -> float:
    """Return a linearly interpolated percentile."""
    if not values:
        raise ValueError("cannot calculate a percentile from an empty list")
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def read_tum_poses(path: Path) -> list[tuple[float, float, float, float]]:
    """Read timestamp, x, y, z from a TUM pose file."""
    poses: list[tuple[float, float, float, float]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        fields = stripped.split()
        if len(fields) != 8:
            raise ValueError(
                f"{path}:{line_number}: expected 8 TUM columns, found {len(fields)}"
            )
        try:
            timestamp, x, y, z = (float(value) for value in fields[:4])
        except ValueError as exc:
            raise ValueError(f"{path}:{line_number}: invalid numeric pose field") from exc
        if not all(math.isfinite(value) for value in (timestamp, x, y, z)):
            raise ValueError(f"{path}:{line_number}: pose contains a non-finite value")
        if poses and timestamp <= poses[-1][0]:
            raise ValueError(f"{path}:{line_number}: timestamps must increase strictly")
        poses.append((timestamp, x, y, z))
    if len(poses) < 2:
        raise ValueError("at least two valid poses are required")
    return poses


def analyze(path: Path) -> dict[str, Any]:
    """Compute trajectory and provenance metrics from recorded ground truth."""
    poses = read_tum_poses(path)
    timestamps = [pose[0] for pose in poses]
    intervals = [b - a for a, b in zip(timestamps, timestamps[1:])]
    steps = [
        math.hypot(next_pose[1] - pose[1], next_pose[2] - pose[2])
        for pose, next_pose in zip(poses, poses[1:])
    ]
    speeds = [distance / interval for distance, interval in zip(steps, intervals)]
    duration = timestamps[-1] - timestamps[0]
    total_distance = sum(steps)
    x_values = [pose[1] for pose in poses]
    y_values = [pose[2] for pose in poses]
    z_values = [pose[3] for pose in poses]

    return {
        "dataset": "LILocBench",
        "sequence": "dynamics_0",
        "data_kind": "recorded ground-truth robot trajectory; not a DynNav planner trial",
        "source_url": SOURCE_URL,
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "pose_format": "TUM: timestamp tx ty tz qx qy qz qw",
        "samples": len(poses),
        "duration_s": duration,
        "sampling_hz_mean": (len(intervals) / sum(intervals)),
        "sample_interval_s": {
            "min": min(intervals),
            "median": median(intervals),
            "max": max(intervals),
        },
        "xy_path_length_m": total_distance,
        "xy_straight_line_displacement_m": math.hypot(
            poses[-1][1] - poses[0][1], poses[-1][2] - poses[0][2]
        ),
        "xy_speed_m_s": {
            "mean": total_distance / duration,
            "median": median(speeds),
            "p95": percentile(speeds, 0.95),
            "max": max(speeds),
        },
        "position_bounds_m": {
            "x": [min(x_values), max(x_values)],
            "y": [min(y_values), max(y_values)],
            "z": [min(z_values), max(z_values)],
        },
        "license": "CC BY-NC-SA 4.0; cite Trekel et al., IROS 2025",
        "analysis_method": (
            "2D path length is the sum of Euclidean XY distances between consecutive "
            "ground-truth poses; speeds divide each segment by its timestamp interval."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("poses", type=Path, help="path to a LILocBench TUM ground-truth pose file")
    parser.add_argument("--output", type=Path, help="write JSON output to this path")
    args = parser.parse_args()

    result = analyze(args.poses)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
