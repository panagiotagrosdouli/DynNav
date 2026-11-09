#!/usr/bin/env python3
"""Generate a licensed SVG overlay of the LILocBench map, GT track, and static A* route."""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import math
from pathlib import Path

import numpy as np
import yaml
from dynnav.mapping.ros_map import RosMap, load_ros_map
from dynnav.planners.astar import AStarResult, astar

LICENSE = "CC BY-NC-SA 4.0"
LICENSE_URL = "https://creativecommons.org/licenses/by-nc-sa/4.0/"
PAPER_CITATION = (
    "N. Trekel et al., Benchmark for Evaluating Long-Term Localization in Indoor Environments "
    "Under Substantial Static and Dynamic Scene Changes, IROS 2025."
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def map_pixel(cell: tuple[int, int], ros_map: RosMap, *, left: int, top: int) -> tuple[float, float]:
    """Convert bottom-left ROS cell indices to top-left SVG image coordinates."""
    x, y = cell
    return left + x + 0.5, top + ros_map.grid.height - y - 0.5


def path_data(cells: list[tuple[int, int]], ros_map: RosMap, *, left: int, top: int) -> str:
    points = [map_pixel(cell, ros_map, left=left, top=top) for cell in cells]
    return " ".join(f'{"M" if index == 0 else "L"}{x:.2f},{y:.2f}' for index, (x, y) in enumerate(points))


def write_path_csv(path: Path, cells: list[tuple[int, int]], ros_map: RosMap) -> None:
    """Write the planned cell centers in map-frame metres with stable LF endings."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("step", "cell_x", "cell_y", "world_x_m", "world_y_m"))
        for step, cell in enumerate(cells):
            world_x, world_y = ros_map.cell_center(cell)
            writer.writerow((step, cell[0], cell[1], world_x, world_y))


def generate_overlay(
    map_yaml: Path,
    ground_truth_path: Path,
    output: Path,
    map_archive: Path | None = None,
    path_csv: Path | None = None,
) -> dict[str, object]:
    """Validate map-frame samples, run endpoint A*, and write an attributed SVG overlay."""
    map_yaml = map_yaml.expanduser().resolve()
    ground_truth_path = ground_truth_path.expanduser().resolve()
    output = output.expanduser().resolve()
    metadata = yaml.safe_load(map_yaml.read_text(encoding="utf-8"))
    image_path = (map_yaml.parent / metadata["image"]).resolve()
    ros_map = load_ros_map(map_yaml, unknown_as_obstacle=True)
    poses = np.loadtxt(ground_truth_path, dtype=np.float64)
    if poses.ndim != 2 or poses.shape[1] != 8 or len(poses) < 2:
        raise ValueError("ground-truth input must contain at least two 8-column TUM poses")
    if not np.all(np.isfinite(poses)) or np.any(np.diff(poses[:, 0]) <= 0):
        raise ValueError("ground-truth timestamps must increase and all pose fields must be finite")

    gt_cells = [ros_map.world_to_cell(float(row[1]), float(row[2])) for row in poses]
    if any(not ros_map.grid.passable(cell) for cell in gt_cells):
        blocked = sum(not ros_map.grid.passable(cell) for cell in gt_cells)
        raise ValueError(
            f"refusing to create a verified overlay: {blocked}/{len(gt_cells)} ground-truth samples "
            "map to occupied or unknown cells"
        )
    route: AStarResult = astar(ros_map.grid, gt_cells[0], gt_cells[-1])
    if not route.success:
        raise ValueError("static A* cannot connect the first and last ground-truth cells")

    observed_length = float(
        sum(
            math.hypot(poses[index, 1] - poses[index - 1, 1], poses[index, 2] - poses[index - 1, 2])
            for index in range(1, len(poses))
        )
    )
    gt_sha = digest(ground_truth_path)
    yaml_sha = digest(map_yaml)
    image_sha = digest(image_path)
    archive_sha = digest(map_archive.expanduser().resolve()) if map_archive is not None else "not supplied"

    left, top, width, header = 100, 170, ros_map.grid.width, 155
    gt_svg_cells = gt_cells[::4]
    if gt_svg_cells[-1] != gt_cells[-1]:
        gt_svg_cells.append(gt_cells[-1])
    gt_d = path_data(gt_svg_cells, ros_map, left=left, top=top)
    route_d = path_data(route.path, ros_map, left=left, top=top)
    start_x, start_y = map_pixel(gt_cells[0], ros_map, left=left, top=top)
    goal_x, goal_y = map_pixel(gt_cells[-1], ros_map, left=left, top=top)
    route_length = route.cost * ros_map.resolution
    height = header + ros_map.grid.height + 205
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 {height}" role="img" aria-labelledby="title desc">
<title id="title">LILocBench dynamics_0 verified occupancy map and ground-truth overlay</title>
<desc id="desc">Dataset map with all {len(poses)} ground-truth poses in known-free cells. Pink line is the recorded trajectory; cyan line is a static four-neighbour A-star path between its first and last cells. Not closed-loop navigation evidence.</desc>
<metadata>Dataset=LILocBench dynamics_0. Metric=GT path {observed_length:.3f} m; static A-star {route_length:.3f} m, {len(route.path)} cells, {route.nodes_expanded} expansions. Evidence=verified map ingestion and shared-global-frame overlay; not closed loop. Map YAML SHA256={yaml_sha}; map image SHA256={image_sha}; GT SHA256={gt_sha}; map archive SHA256={archive_sha}. License={LICENSE}. {PAPER_CITATION}</metadata>
<!-- LILocBench map image is adapted under {LICENSE}. Attribution: {PAPER_CITATION} -->
<rect width="1200" height="{height}" fill="#07111b"/>
<text x="60" y="48" fill="#eef4f8" font-family="system-ui,sans-serif" font-size="25" font-weight="700">LILocBench dynamics_0 · verified map-frame overlay</text>
<text x="60" y="80" fill="#c2cfdb" font-family="system-ui,sans-serif" font-size="15">Metric: GT path {observed_length:.2f} m · static A* route {route_length:.2f} m · {len(poses)} poses · {route.nodes_expanded} A* expansions</text>
<text x="60" y="108" fill="#65e6d5" font-family="system-ui,sans-serif" font-size="13">Evidence: dataset global-frame provenance + {len(poses)}/{len(poses)} poses in known-free cells; no fitted transform; not closed loop</text>
<image x="{left}" y="{top}" width="{width}" height="{ros_map.grid.height}" preserveAspectRatio="none" href="data:image/png;base64,{base64.b64encode(image_path.read_bytes()).decode('ascii')}"/>
<path d="{route_d}" fill="none" stroke="#38bdf8" stroke-width="3" stroke-linejoin="round" stroke-linecap="round" opacity=".94"/>
<path d="{gt_d}" fill="none" stroke="#ff4fa3" stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round" opacity=".94"/>
<circle cx="{start_x:.2f}" cy="{start_y:.2f}" r="8" fill="#65e6d5" stroke="#061018" stroke-width="3"/>
<circle cx="{goal_x:.2f}" cy="{goal_y:.2f}" r="8" fill="#facc15" stroke="#061018" stroke-width="3"/>
<rect x="60" y="{top + ros_map.grid.height + 28}" width="1080" height="42" rx="8" fill="#101b27" stroke="#33475d"/>
<line x1="82" y1="{top + ros_map.grid.height + 49}" x2="122" y2="{top + ros_map.grid.height + 49}" stroke="#ff4fa3" stroke-width="4"/><text x="134" y="{top + ros_map.grid.height + 54}" fill="#e6edf4" font-family="system-ui,sans-serif" font-size="14">Recorded ground-truth XY path</text>
<line x1="390" y1="{top + ros_map.grid.height + 49}" x2="430" y2="{top + ros_map.grid.height + 49}" stroke="#38bdf8" stroke-width="4"/><text x="442" y="{top + ros_map.grid.height + 54}" fill="#e6edf4" font-family="system-ui,sans-serif" font-size="14">DynNav static A* path</text>
<circle cx="720" cy="{top + ros_map.grid.height + 49}" r="7" fill="#65e6d5"/><text x="734" y="{top + ros_map.grid.height + 54}" fill="#e6edf4" font-family="system-ui,sans-serif" font-size="14">Start</text>
<circle cx="800" cy="{top + ros_map.grid.height + 49}" r="7" fill="#facc15"/><text x="814" y="{top + ros_map.grid.height + 54}" fill="#e6edf4" font-family="system-ui,sans-serif" font-size="14">Goal</text>
<text x="60" y="{top + ros_map.grid.height + 98}" fill="#cbd5df" font-family="system-ui,sans-serif" font-size="11">Sources: map_office.yaml SHA256 {yaml_sha} · map_office.png SHA256 {image_sha}</text>
<text x="60" y="{top + ros_map.grid.height + 120}" fill="#cbd5df" font-family="system-ui,sans-serif" font-size="11">dynamics_0 gt_poses.txt SHA256 {gt_sha}</text>
<text x="60" y="{top + ros_map.grid.height + 151}" fill="#9eacba" font-family="system-ui,sans-serif" font-size="10">Dataset: CC BY-NC-SA 4.0 · {PAPER_CITATION}</text>
</svg>
'''
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg, encoding="utf-8")
    if path_csv is not None:
        write_path_csv(path_csv.expanduser().resolve(), route.path, ros_map)
    return {
        "output": str(output),
        "ground_truth_pose_count": len(poses),
        "ground_truth_known_free_cells": len(gt_cells),
        "ground_truth_path_length_m": observed_length,
        "static_astar_path_length_m": route_length,
        "static_astar_cells": len(route.path),
        "static_astar_nodes_expanded": route.nodes_expanded,
        "map_yaml_sha256": yaml_sha,
        "map_image_sha256": image_sha,
        "ground_truth_sha256": gt_sha,
        "map_archive_sha256": archive_sha,
        "license": LICENSE,
        "license_url": LICENSE_URL,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map_yaml", type=Path, help="extracted official map_office.yaml")
    parser.add_argument("ground_truth", type=Path, help="public TUM dynamics_0 ground truth")
    parser.add_argument("output", type=Path, help="destination SVG path")
    parser.add_argument("--map-archive", type=Path, help="official map_office.zip for provenance SHA-256")
    parser.add_argument("--path-csv", type=Path, help="optional A* route cells and map-frame centers CSV")
    args = parser.parse_args()
    print(
        __import__("json").dumps(
            generate_overlay(args.map_yaml, args.ground_truth, args.output, args.map_archive, args.path_csv),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
