from __future__ import annotations

from collections import deque
from pathlib import Path

import yaml

from dynnav_nav2_benchmark.correlated_history_execution import (
    blocker_footprint_cells,
    load_correlated_history_execution_suite,
    quantized_hazard_transitions,
)
from dynnav_nav2_benchmark.history_execution import world_to_cell


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def _load_p2(path: Path) -> tuple[int, int, list[int]]:
    tokens = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            tokens.extend(line.split())
    assert tokens[0] == "P2"
    width = int(tokens[1])
    height = int(tokens[2])
    max_value = int(tokens[3])
    assert max_value == 255
    values = [int(value) for value in tokens[4:]]
    assert len(values) == width * height
    return width, height, values


def _grid_free_from_map() -> tuple[int, int, set[tuple[int, int]]]:
    map_yaml = yaml.safe_load(
        (PACKAGE_ROOT / "maps" / "g1_parallel_corridor.yaml").read_text(
            encoding="utf-8"
        )
    )
    width, height, pixels = _load_p2(
        PACKAGE_ROOT / "maps" / map_yaml["image"]
    )
    free: set[tuple[int, int]] = set()
    # ROS map images store row zero at the top; map-grid y=0 is at the bottom.
    for image_row in range(height):
        grid_y = height - 1 - image_row
        for x in range(width):
            pixel = pixels[image_row * width + x]
            if pixel >= 250:
                free.add((x, grid_y))
    return width, height, free


def _reachable(
    width: int,
    height: int,
    free: set[tuple[int, int]],
    start: tuple[int, int],
    safe: set[tuple[int, int]],
    blocked: set[tuple[int, int]],
) -> bool:
    if start in safe:
        return True
    if start not in free or start in blocked:
        return False
    frontier = deque([start])
    visited = {start}
    while frontier:
        x, y = frontier.popleft()
        for nxt in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            nx, ny = nxt
            if not (0 <= nx < width and 0 <= ny < height):
                continue
            if nxt in visited or nxt not in free or nxt in blocked:
                continue
            if nxt in safe:
                return True
            visited.add(nxt)
            frontier.append(nxt)
    return False


def test_canonical_g1_assets_have_parallel_return_interaction() -> None:
    suite = load_correlated_history_execution_suite(
        PACKAGE_ROOT / "config" / "g1_parallel_corridor_correlated.yaml"
    )
    map_yaml = yaml.safe_load(
        (PACKAGE_ROOT / "maps" / "g1_parallel_corridor.yaml").read_text(
            encoding="utf-8"
        )
    )
    resolution = float(map_yaml["resolution"])
    origin_x = float(map_yaml["origin"][0])
    origin_y = float(map_yaml["origin"][1])

    width, height, free = _grid_free_from_map()
    scenario = suite.scenario
    query = world_to_cell(
        scenario.goal,
        origin_x=origin_x,
        origin_y=origin_y,
        resolution=resolution,
    )
    safe_center = world_to_cell(
        scenario.safe_region.center,
        origin_x=origin_x,
        origin_y=origin_y,
        resolution=resolution,
    )
    radius_cells = int(scenario.safe_region.radius_m / resolution)
    safe = {
        (x, y)
        for x in range(safe_center[0] - radius_cells, safe_center[0] + radius_cells + 1)
        for y in range(safe_center[1] - radius_cells, safe_center[1] + radius_cells + 1)
        if (x, y) in free
        and ((x - safe_center[0]) ** 2 + (y - safe_center[1]) ** 2) ** 0.5
        <= radius_cells
    }

    closures = [
        set(
            blocker_footprint_cells(
                center=hazard.blocker_pose,
                size_xy=(suite.blocker_size[0], suite.blocker_size[1]),
                origin_x=origin_x,
                origin_y=origin_y,
                resolution=resolution,
            )
        )
        for hazard in scenario.hazards
    ]

    f00 = int(_reachable(width, height, free, query, safe, set()))
    f10 = int(_reachable(width, height, free, query, safe, closures[0]))
    f01 = int(_reachable(width, height, free, query, safe, closures[1]))
    f11 = int(_reachable(width, height, free, query, safe, closures[0] | closures[1]))
    assert (f00, f10, f01, f11) == (1, 1, 1, 0)
    assert f00 - f10 - f01 + f11 == -1

    triggers = quantized_hazard_transitions(
        suite,
        origin_x=origin_x,
        origin_y=origin_y,
        resolution=resolution,
    )
    for source, target in triggers:
        assert source in free
        assert target in free
        assert abs(source[0] - target[0]) + abs(source[1] - target[1]) == 1
