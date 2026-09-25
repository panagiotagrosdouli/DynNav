"""Static contract checks for the canonical G1 parallel-corridor environment."""

from __future__ import annotations

import heapq
import math
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

from dynnav_nav2_benchmark.correlated_history_execution import (
    blocker_footprint_cells,
    load_correlated_history_execution_suite,
    quantized_hazard_transitions,
    quantized_hazard_trigger_gates,
)
from dynnav_nav2_benchmark.history_execution import world_to_cell


@dataclass(frozen=True)
class CanonicalG1RoutePlan:
    steps: int
    total_cost: float
    final_active_mask: int
    trigger_crossings: tuple[bool, bool]
    minimum_grid_y: int


@dataclass(frozen=True)
class CanonicalG1TopologyContract:
    f00: int
    f10: int
    f01: int
    f11: int
    interaction: int
    trigger_cells: tuple[
        tuple[tuple[int, int], tuple[int, int]],
        tuple[tuple[int, int], tuple[int, int]],
    ]
    blocker_cell_counts: tuple[int, int]
    trigger_gate_edge_counts: tuple[int, int]
    trigger_gate_full_corridor_cuts: tuple[bool, bool]
    goal_cell: tuple[int, int]
    safe_cell_count: int
    independence_route: CanonicalG1RoutePlan
    robust_route: CanonicalG1RoutePlan

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class _Map:
    width: int
    height: int
    resolution: float
    origin_x: float
    origin_y: float
    occupied: frozenset[tuple[int, int]]


def _load_p2_map(map_yaml: str | Path) -> _Map:
    yaml_path = Path(map_yaml)
    meta = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    if not isinstance(meta, dict):
        raise ValueError("map YAML must be a mapping")
    image = yaml_path.parent / str(meta["image"])
    tokens: list[str] = []
    for line in image.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        tokens.extend(stripped.split())
    if len(tokens) < 4 or tokens[0] != "P2":
        raise ValueError("canonical map must use ASCII P2 PGM")
    width = int(tokens[1])
    height = int(tokens[2])
    max_value = int(tokens[3])
    pixels = [int(value) for value in tokens[4:]]
    if max_value <= 0 or len(pixels) != width * height:
        raise ValueError("invalid PGM dimensions or pixel count")

    negate = int(meta.get("negate", 0))
    occupied_thresh = float(meta["occupied_thresh"])
    occupied: set[tuple[int, int]] = set()
    for image_row in range(height):
        grid_y = height - 1 - image_row
        for x in range(width):
            pixel = pixels[image_row * width + x]
            occupancy = (
                pixel / max_value if negate else (max_value - pixel) / max_value
            )
            if occupancy >= occupied_thresh:
                occupied.add((x, grid_y))

    origin = meta["origin"]
    return _Map(
        width=width,
        height=height,
        resolution=float(meta["resolution"]),
        origin_x=float(origin[0]),
        origin_y=float(origin[1]),
        occupied=frozenset(occupied),
    )


def _safe_cells(grid: _Map, center_x: float, center_y: float, radius_m: float):
    result = set()
    for y in range(grid.height):
        wy = grid.origin_y + (y + 0.5) * grid.resolution
        for x in range(grid.width):
            if (x, y) in grid.occupied:
                continue
            wx = grid.origin_x + (x + 0.5) * grid.resolution
            if math.hypot(wx - center_x, wy - center_y) <= radius_m:
                result.add((x, y))
    if not result:
        raise ValueError("safe region contains no free map cells")
    return frozenset(result)


def _reachable(
    grid: _Map,
    start: tuple[int, int],
    safe: frozenset[tuple[int, int]],
    blocked: frozenset[tuple[int, int]],
) -> bool:
    if start in grid.occupied or start in blocked:
        return False
    if start in safe:
        return True
    queue: deque[tuple[int, int]] = deque([start])
    visited = {start}
    while queue:
        x, y = queue.popleft()
        for next_cell in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            nx, ny = next_cell
            if not (0 <= nx < grid.width and 0 <= ny < grid.height):
                continue
            if next_cell in visited or next_cell in grid.occupied or next_cell in blocked:
                continue
            if next_cell in safe:
                return True
            visited.add(next_cell)
            queue.append(next_cell)
    return False


def _corridor_edges_containing_trigger(
    grid: _Map,
    trigger: tuple[tuple[int, int], tuple[int, int]],
) -> frozenset[tuple[tuple[int, int], tuple[int, int]]]:
    """Return the full contiguous free x-boundary corridor around a trigger."""

    (sx, sy), (tx, ty) = trigger
    if sy != ty or abs(tx - sx) != 1:
        raise ValueError("canonical trigger must be one horizontal grid edge")

    free_rows = {
        y
        for y in range(grid.height)
        if (sx, y) not in grid.occupied and (tx, y) not in grid.occupied
    }
    if sy not in free_rows:
        raise ValueError("canonical trigger is not inside a free corridor")

    low = sy
    while low - 1 in free_rows:
        low -= 1
    high = sy
    while high + 1 in free_rows:
        high += 1
    return frozenset(((sx, y), (tx, y)) for y in range(low, high + 1))


def _reachable_component(
    grid: _Map,
    safe_cell: tuple[int, int],
    blocked: frozenset[tuple[int, int]],
) -> frozenset[tuple[int, int]]:
    if safe_cell in grid.occupied or safe_cell in blocked:
        return frozenset()
    queue: deque[tuple[int, int]] = deque([safe_cell])
    visited = {safe_cell}
    while queue:
        x, y = queue.popleft()
        for next_cell in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            nx, ny = next_cell
            if not (0 <= nx < grid.width and 0 <= ny < grid.height):
                continue
            if (
                next_cell in visited
                or next_cell in grid.occupied
                or next_cell in blocked
            ):
                continue
            visited.add(next_cell)
            queue.append(next_cell)
    return frozenset(visited)


def _route_plan(
    grid: _Map,
    *,
    start: tuple[int, int],
    goal: tuple[int, int],
    trigger_gates,
    blocker_sets,
    recoverability_weight: float,
    robust: bool,
    pairwise_joint_lower: float,
    pairwise_joint_upper: float,
) -> CanonicalG1RoutePlan:
    """Replicate the two-hazard C++ augmented-state objective on the raw map."""

    realizations = (
        (False, False),
        (True, False),
        (False, True),
        (True, True),
    )
    components = {}
    for first_closed, second_closed in realizations:
        blocked: set[tuple[int, int]] = set()
        if first_closed:
            blocked.update(blocker_sets[0])
        if second_closed:
            blocked.update(blocker_sets[1])
        components[(first_closed, second_closed)] = _reachable_component(
            grid,
            start,
            frozenset(blocked),
        )

    def connected(cell, realization) -> float:
        return float(cell in components[realization])

    def return_probability(cell, mask: int) -> float:
        if mask == 0:
            return 1.0
        if mask == 1:
            return 0.5 * connected(cell, (False, False)) + 0.5 * connected(
                cell, (True, False)
            )
        if mask == 2:
            return 0.5 * connected(cell, (False, False)) + 0.5 * connected(
                cell, (False, True)
            )

        f00 = connected(cell, (False, False))
        f10 = connected(cell, (True, False))
        f01 = connected(cell, (False, True))
        f11 = connected(cell, (True, True))
        if not robust:
            return 0.25 * (f00 + f10 + f01 + f11)

        interaction = f00 - f10 - f01 + f11
        frechet_lower = 0.0
        frechet_upper = 0.5
        q_lower = max(frechet_lower, pairwise_joint_lower)
        q_upper = min(frechet_upper, pairwise_joint_upper)
        q = q_upper if interaction < 0.0 else q_lower
        return (
            q * f00
            + (0.5 - q) * f10
            + (0.5 - q) * f01
            + q * f11
        )

    gate_sets = (frozenset(trigger_gates[0]), frozenset(trigger_gates[1]))

    def activate(
        cell: tuple[int, int],
        next_cell: tuple[int, int],
        mask: int,
    ) -> int:
        for index, gate in enumerate(gate_sets):
            if (cell, next_cell) in gate:
                mask |= 1 << index
        return mask

    start_state = (start, 0)
    distance = {start_state: 0.0}
    parent: dict[
        tuple[tuple[int, int], int],
        tuple[tuple[int, int], int],
    ] = {}
    frontier: list[tuple[float, float, int, int, int]] = []
    order = 0
    heapq.heappush(
        frontier,
        (
            float(abs(start[0] - goal[0]) + abs(start[1] - goal[1])),
            0.0,
            order,
            start[0] + start[1] * grid.width,
            0,
        ),
    )

    final_state = None
    while frontier:
        _priority, known_cost, _order, flat, mask = heapq.heappop(frontier)
        cell = (flat % grid.width, flat // grid.width)
        state = (cell, mask)
        if abs(known_cost - distance.get(state, math.inf)) > 1.0e-12:
            continue
        if cell == goal:
            final_state = state
            break

        x, y = cell
        for next_cell in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            nx, ny = next_cell
            if not (0 <= nx < grid.width and 0 <= ny < grid.height):
                continue
            if next_cell in grid.occupied:
                continue
            next_mask = activate(cell, next_cell, mask)
            r = return_probability(next_cell, next_mask)
            candidate = known_cost + 1.0 + recoverability_weight * (1.0 - r)
            next_state = (next_cell, next_mask)
            if candidate + 1.0e-12 >= distance.get(next_state, math.inf):
                continue
            distance[next_state] = candidate
            parent[next_state] = state
            order += 1
            heuristic = abs(nx - goal[0]) + abs(ny - goal[1])
            heapq.heappush(
                frontier,
                (
                    candidate + float(heuristic),
                    candidate,
                    order,
                    nx + ny * grid.width,
                    next_mask,
                ),
            )

    if final_state is None:
        raise ValueError("canonical planner contract could not find a path")

    states = [final_state]
    while states[-1] != start_state:
        states.append(parent[states[-1]])
    states.reverse()
    cells = [cell for cell, _mask in states]
    crossings = tuple(
        any((left, right) in gate for left, right in zip(cells, cells[1:], strict=False))
        for gate in gate_sets
    )
    return CanonicalG1RoutePlan(
        steps=len(cells) - 1,
        total_cost=distance[final_state],
        final_active_mask=final_state[1],
        trigger_crossings=(bool(crossings[0]), bool(crossings[1])),
        minimum_grid_y=min(cell[1] for cell in cells),
    )


def evaluate_canonical_g1_topology(
    *,
    map_yaml: str | Path,
    scenario_yaml: str | Path,
) -> CanonicalG1TopologyContract:
    grid = _load_p2_map(map_yaml)
    suite = load_correlated_history_execution_suite(scenario_yaml)
    scenario = suite.scenario

    triggers = quantized_hazard_transitions(
        suite,
        origin_x=grid.origin_x,
        origin_y=grid.origin_y,
        resolution=grid.resolution,
    )
    trigger_gates = quantized_hazard_trigger_gates(
        suite,
        origin_x=grid.origin_x,
        origin_y=grid.origin_y,
        resolution=grid.resolution,
    )
    blocker_sets = tuple(
        frozenset(
            blocker_footprint_cells(
                center=hazard.blocker_pose,
                size_xy=(suite.blocker_size[0], suite.blocker_size[1]),
                origin_x=grid.origin_x,
                origin_y=grid.origin_y,
                resolution=grid.resolution,
            )
        )
        for hazard in scenario.hazards
    )
    safe = _safe_cells(
        grid,
        scenario.safe_region.center.x,
        scenario.safe_region.center.y,
        scenario.safe_region.radius_m,
    )
    goal = world_to_cell(
        scenario.goal,
        origin_x=grid.origin_x,
        origin_y=grid.origin_y,
        resolution=grid.resolution,
    )

    for trigger in triggers:
        for cell in trigger:
            if cell in grid.occupied:
                raise ValueError(f"trigger cell lies in static obstacle: {cell}")
    for gate in trigger_gates:
        for edge in gate:
            for cell in edge:
                if cell in grid.occupied:
                    raise ValueError(
                        f"trigger-gate cell lies in static obstacle: {cell}"
                    )
    if goal in grid.occupied:
        raise ValueError("goal lies in a static obstacle")
    if goal in blocker_sets[0] or goal in blocker_sets[1]:
        raise ValueError("goal intersects a dynamic blocker footprint")

    expected_gate_edges = tuple(
        _corridor_edges_containing_trigger(grid, trigger)
        for trigger in triggers
    )
    gate_full_corridor = tuple(
        frozenset(gate) == expected
        for gate, expected in zip(trigger_gates, expected_gate_edges, strict=True)
    )

    f00 = int(_reachable(grid, goal, safe, frozenset()))
    f10 = int(_reachable(grid, goal, safe, blocker_sets[0]))
    f01 = int(_reachable(grid, goal, safe, blocker_sets[1]))
    f11 = int(_reachable(grid, goal, safe, blocker_sets[0] | blocker_sets[1]))

    planner_safe_cell = world_to_cell(
        scenario.safe_region.center,
        origin_x=grid.origin_x,
        origin_y=grid.origin_y,
        resolution=grid.resolution,
    )
    independence_route = _route_plan(
        grid,
        start=planner_safe_cell,
        goal=goal,
        trigger_gates=trigger_gates,
        blocker_sets=blocker_sets,
        recoverability_weight=scenario.recoverability_weight,
        robust=False,
        pairwise_joint_lower=scenario.pairwise_joint_lower,
        pairwise_joint_upper=scenario.pairwise_joint_upper,
    )
    robust_route = _route_plan(
        grid,
        start=planner_safe_cell,
        goal=goal,
        trigger_gates=trigger_gates,
        blocker_sets=blocker_sets,
        recoverability_weight=scenario.recoverability_weight,
        robust=True,
        pairwise_joint_lower=scenario.pairwise_joint_lower,
        pairwise_joint_upper=scenario.pairwise_joint_upper,
    )

    return CanonicalG1TopologyContract(
        f00=f00,
        f10=f10,
        f01=f01,
        f11=f11,
        interaction=f00 - f10 - f01 + f11,
        trigger_cells=triggers,
        blocker_cell_counts=(len(blocker_sets[0]), len(blocker_sets[1])),
        trigger_gate_edge_counts=(len(trigger_gates[0]), len(trigger_gates[1])),
        trigger_gate_full_corridor_cuts=(
            bool(gate_full_corridor[0]),
            bool(gate_full_corridor[1]),
        ),
        goal_cell=goal,
        safe_cell_count=len(safe),
        independence_route=independence_route,
        robust_route=robust_route,
    )
