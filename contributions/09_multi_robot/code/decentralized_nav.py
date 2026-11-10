"""
decentralized_nav.py

Decentralized multi-robot navigation with local coordination.

Each robot:
  - Plans independently using A*
  - Broadcasts its (position, intent/next_waypoint) to neighbours within
    communication range
  - Avoids collisions using a priority-based reservation scheme:
      lower robot_id has priority; others yield

Risk sharing
------------
Each robot maintains a local risk map. When a robot detects high-risk cells
(obstacle proximity, uncertainty), it shares that information.
Other robots adjust their cost function accordingly.

Comparison: centralised vs decentralised
-----------------------------------------
Centralised   : joint A* over combined state space (exponential — approximated
                here by sequential planning with full map knowledge)
Decentralised : each robot plans independently with local info exchange
"""

from __future__ import annotations

import heapq
import math
import random
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

NEIGHBORS_4 = [(1, 0), (-1, 0), (0, 1), (0, -1)]


# ---------------------------------------------------------------------------
# Robot agent
# ---------------------------------------------------------------------------

@dataclass
class RobotAgent:
    robot_id: int
    pos: tuple[int, int]
    goal: tuple[int, int]
    comm_range: float = 10.0      # communication radius
    path: list[tuple[int, int]] = field(default_factory=list)
    reached_goal: bool = False
    steps: int = 0
    replans: int = 0
    collision_avoidance_events: int = 0
    shared_risk: dict[tuple[int, int], float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Local A* with risk map
# ---------------------------------------------------------------------------

def _astar_with_risk(
    grid: np.ndarray,
    start: tuple[int, int],
    goal: tuple[int, int],
    risk_map: dict[tuple[int, int], float],
    reserved: set[tuple[int, int]],
    lambda_risk: float = 1.0,
) -> Optional[list[tuple[int, int]]]:
    H, W = grid.shape

    def free(x, y):
        return 0 <= x < W and 0 <= y < H and int(grid[y, x]) == 0

    dist = lambda a, b: math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)
    g: dict = {start: 0.0}
    parent: dict = {start: None}
    open_pq = [(dist(start, goal), 0.0, start)]
    closed: set = set()

    while open_pq:
        _, g_c, curr = heapq.heappop(open_pq)
        if curr in closed:
            continue
        closed.add(curr)
        if curr == goal:
            path, node = [], curr
            while node:
                path.append(node); node = parent[node]
            path.reverse()
            return path

        x, y = curr
        for dx, dy in NEIGHBORS_4:
            nx, ny = x + dx, y + dy
            if not free(nx, ny):
                continue
            neigh = (nx, ny)
            if neigh in reserved:
                continue  # yield to higher priority
            risk = risk_map.get(neigh, 0.0)
            tg = g_c + 1.0 + lambda_risk * risk
            if neigh not in g or tg < g[neigh]:
                g[neigh] = tg
                parent[neigh] = curr
                heapq.heappush(open_pq, (tg + dist(neigh, goal), tg, neigh))

    return None


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

@dataclass
class DecentralizedResult:
    strategy: str
    all_reached: bool
    total_steps: int
    total_replans: int
    collision_events: int  # blocked/avoided intents, NOT actual physical collisions
    avg_path_length: float


def run_decentralized(
    grid: np.ndarray,
    robots: list[RobotAgent],
    max_steps: int = 300,
    share_risk: bool = True,
    lambda_risk: float = 0.5,
) -> DecentralizedResult:
    """
    Decentralised execution: each robot plans independently.
    Priority: lower robot_id always has right-of-way.
    """
    H, W = grid.shape
    if len(set(r.robot_id for r in robots)) != len(robots):
        raise ValueError("Duplicate robot_id is unsafe for multi-robot scheduling")
    if len(set(r.pos for r in robots)) != len(robots):
        raise ValueError("Multiple robots occupy one initial grid cell")
    for robot in robots:
        for x,y in (robot.pos, robot.goal):
            if not (0<=x<W and 0<=y<H) or grid[y,x]:
                raise ValueError("Robot start or goal is blocked/outside map")
        robot.reached_goal = robot.pos == robot.goal
        robot.path = _astar_with_risk(grid, robot.pos, robot.goal, {}, set(), lambda_risk) or [robot.pos]
    collision_events = 0

    for step in range(max_steps):
        if all(r.reached_goal for r in robots):
            break

        # Conservative discrete safety barrier: a robot may NOT enter ANY
        # other agent's position occupied at the beginning of this tick.
        # This also excludes head-on swaps, even when an occupant intends
        # to leave. It can cause deadlock; collision safety != liveness.
        positions = {r.robot_id: r.pos for r in robots}
        occupied = set(positions.values())
        intended: dict[int, tuple[int,int]] = {}
        reserved: set[tuple[int,int]] = set()
        for robot in sorted(robots,key=lambda r:r.robot_id):
            if robot.reached_goal:
                intended[robot.robot_id] = robot.pos
                reserved.add(robot.pos)
                continue
            next_cell = robot.path[1] if len(robot.path)>1 else robot.pos
            blocked = (next_cell in (occupied-{robot.pos})) or next_cell in reserved
            if blocked or next_cell==robot.pos:
                unavailable=(occupied-{robot.pos})|reserved
                # Replan but never execute a new cell in the same tick:
                # the reservation/barrier must be reevaluated next tick.
                replacement=_astar_with_risk(grid,robot.pos,robot.goal,
                                             robot.shared_risk,unavailable,lambda_risk)
                if replacement:
                    robot.path=replacement
                robot.replans+=1
                robot.collision_avoidance_events+=int(blocked)
                collision_events+=int(blocked)
                intended[robot.robot_id]=robot.pos
            else:
                intended[robot.robot_id]=next_cell
            reserved.add(intended[robot.robot_id])
        # Fail closed if any future modification defeats the intent barrier.
        if len(set(intended.values())) != len(robots):
            raise RuntimeError("C09 unresolved vertex collision; refusing to step")
        if any(intended[r.robot_id] in occupied-{r.pos} for r in robots):
            raise RuntimeError("C09 occupied-cell incursion; refusing to step")

        # Apply moves and share risk
        for robot in robots:
            if robot.reached_goal:
                continue
            new_pos = intended.get(robot.robot_id, robot.pos)
            robot.pos = new_pos
            robot.steps += 1
            if robot.path and len(robot.path) > 1 and robot.path[1] == new_pos:
                robot.path = robot.path[1:]

            if robot.pos == robot.goal:
                robot.reached_goal = True

        # Risk sharing: broadcast high-risk observations to nearby robots
        if share_risk:
            for r in robots:
                x, y = r.pos
                local_risk = 0.0
                for dx, dy in NEIGHBORS_4:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H and int(grid[ny, nx]) == 1:
                        local_risk += 0.25
                if local_risk > 0:
                    for other in robots:
                        if other.robot_id != r.robot_id:
                            d = math.dist(r.pos, other.pos)
                            if d <= r.comm_range:
                                other.shared_risk[r.pos] = local_risk

    all_reached = all(r.reached_goal for r in robots)
    total_steps = sum(r.steps for r in robots)
    total_replans = sum(r.replans for r in robots)
    avg_path = total_steps / max(len(robots), 1)

    return DecentralizedResult(
        strategy="decentralized",
        all_reached=all_reached,
        total_steps=total_steps,
        total_replans=total_replans,
        collision_events=collision_events,
        avg_path_length=avg_path,
    )


def run_centralized(
    grid: np.ndarray,
    robots: list[RobotAgent],
    max_steps: int = 300,
    lambda_risk: float = 0.5,
) -> DecentralizedResult:
    """Central sequential baseline (NOT optimal joint-state MAPF).

    This implementation executes exactly one robot at a time, treating
    all other robot positions as occupied static obstacles. This avoids
    vertex overlap/head-on edge swaps but can deadlock on narrow passages
    and cannot be called a globally optimal centralized MAPF solver.
    """
    H, W = grid.shape
    if len({r.robot_id for r in robots}) != len(robots):
        raise ValueError("Duplicate robot_id is unsafe")
    if len({r.pos for r in robots}) != len(robots):
        raise ValueError("Overlapping robot starts are unsafe")
    for r in robots:
        for x,y in (r.pos,r.goal):
            if not (0<=x<W and 0<=y<H) or grid[y,x]:
                raise ValueError("Robot start or goal is blocked/outside map")
        r.reached_goal=r.pos==r.goal

    blocked_requests=0
    for robot in sorted(robots,key=lambda r:r.robot_id):
        if robot.reached_goal:
            continue
        occupied={r.pos for r in robots if r.robot_id!=robot.robot_id}
        path=_astar_with_risk(grid,robot.pos,robot.goal,{},occupied,lambda_risk)
        if path is None:
            blocked_requests+=1
            robot.replans+=1
            continue
        robot.path=path
        for nxt in path[1:max_steps+1]:
            if nxt in {r.pos for r in robots if r.robot_id!=robot.robot_id}:
                raise RuntimeError("Unsafe centralized baseline: occupied-cell violation")
            robot.pos=nxt
            robot.steps+=1
        robot.reached_goal=robot.pos==robot.goal
    return DecentralizedResult(
        strategy="centralized_sequential_static_reservations",
        all_reached=all(r.reached_goal for r in robots),
        total_steps=sum(r.steps for r in robots),
        total_replans=sum(r.replans for r in robots),
        collision_events=blocked_requests,
        avg_path_length=sum(r.steps for r in robots)/max(len(robots),1),
    )
