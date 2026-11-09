"""Inspect a real ROS map and optionally measure a route through it."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml

from dynnav.mapping.ros_map import load_ros_map
from dynnav.planners.astar import astar


def _point(value: str) -> tuple[float, float]:
    try:
        x_text, y_text = value.split(",", maxsplit=1)
        return float(x_text), float(y_text)
    except ValueError as error:
        raise argparse.ArgumentTypeError("point must be written as X,Y") from error


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map_yaml", type=Path, help="ROS map_server YAML metadata file")
    parser.add_argument("--start", type=_point, help="start point in map-frame metres, X,Y")
    parser.add_argument("--goal", type=_point, help="goal point in map-frame metres, X,Y")
    parser.add_argument(
        "--allow-unknown",
        action="store_true",
        help="treat unknown map cells as traversable instead of blocked",
    )
    args = parser.parse_args()
    if (args.start is None) != (args.goal is None):
        parser.error("--start and --goal must be supplied together")

    map_yaml = args.map_yaml.expanduser().resolve()
    ros_map = load_ros_map(map_yaml, unknown_as_obstacle=not args.allow_unknown)
    image_path = map_yaml.parent / yaml.safe_load(map_yaml.read_text(encoding="utf-8"))["image"]
    output: dict[str, object] = {
        "map_yaml": str(map_yaml),
        "image_sha256": hashlib.sha256(image_path.read_bytes()).hexdigest(),
        "width_cells": ros_map.grid.width,
        "height_cells": ros_map.grid.height,
        "resolution_m": ros_map.resolution,
        "origin": [ros_map.origin_x, ros_map.origin_y, ros_map.origin_yaw],
        "occupied_or_unknown_cells": len(ros_map.grid.obstacles),
        "unknown_policy": "free" if args.allow_unknown else "blocked",
    }
    if args.start is not None and args.goal is not None:
        start = ros_map.world_to_cell(*args.start)
        goal = ros_map.world_to_cell(*args.goal)
        result = astar(ros_map.grid, start, goal)
        output["route"] = {
            "start_cell": list(start),
            "goal_cell": list(goal),
            "reachable": result.success,
            "length_m": result.cost * ros_map.resolution if result.success else None,
            "nodes_expanded": result.nodes_expanded,
        }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
