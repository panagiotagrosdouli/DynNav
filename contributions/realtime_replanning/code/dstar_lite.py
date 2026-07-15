"""Incremental D* Lite replanning on a four-connected occupancy grid.

The implementation follows Koenig and Likhachev (AAAI 2002). Priority-queue
entries use lazy deletion, but exactly one key is considered active for each
node. Stale heap entries are never processed as current work.
"""

from __future__ import annotations

import heapq
import math
from typing import Optional

import numpy as np

INF = float("inf")
NEIGHBORS_4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
Node = tuple[int, int]
Key = tuple[float, float]


def _heuristic(a: Node, b: Node) -> float:
    """Consistent Euclidean heuristic for unit-cost four-connected motion."""

    return math.hypot(a[0] - b[0], a[1] - b[1])


class DStarLite:
    """D* Lite planner for a binary ``(height, width)`` occupancy grid."""

    def __init__(self, grid: np.ndarray, start: Node, goal: Node):
        if grid.ndim != 2:
            raise ValueError("grid must be a two-dimensional array")

        self.grid = grid.copy().astype(np.int32)
        self.H, self.W = self.grid.shape
        self._validate_node(start, "start")
        self._validate_node(goal, "goal")

        self.start = start
        self.goal = goal
        self.g: dict[Node, float] = {}
        self.rhs: dict[Node, float] = {}
        self.km = 0.0
        self._heap: list[tuple[float, float, Node]] = []
        self._active_keys: dict[Node, Key] = {}
        self.expansions = 0
        self.replan_count = 0
        self._initialize()

    def _validate_node(self, node: Node, name: str) -> None:
        x, y = node
        if not (0 <= x < self.W and 0 <= y < self.H):
            raise ValueError(f"{name} {node!r} is outside the grid")

    def _g(self, node: Node) -> float:
        return self.g.get(node, INF)

    def _rhs(self, node: Node) -> float:
        return self.rhs.get(node, INF)

    def _key(self, node: Node) -> Key:
        value = min(self._g(node), self._rhs(node))
        return value + _heuristic(self.start, node) + self.km, value

    def _in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.W and 0 <= y < self.H

    def _free(self, x: int, y: int) -> bool:
        return self._in_bounds(x, y) and int(self.grid[y, x]) == 0

    def _neighbors(self, node: Node) -> list[Node]:
        x, y = node
        return [
            (x + dx, y + dy)
            for dx, dy in NEIGHBORS_4
            if self._free(x + dx, y + dy)
        ]

    def _adjacent(self, node: Node) -> list[Node]:
        x, y = node
        return [
            (x + dx, y + dy)
            for dx, dy in NEIGHBORS_4
            if self._in_bounds(x + dx, y + dy)
        ]

    def _cost(self, _source: Node, destination: Node) -> float:
        x, y = destination
        return 1.0 if self._free(x, y) else INF

    def _remove(self, node: Node) -> None:
        self._active_keys.pop(node, None)

    def _push(self, node: Node) -> None:
        key = self._key(node)
        self._active_keys[node] = key
        heapq.heappush(self._heap, (key[0], key[1], node))

    def _discard_stale_head(self) -> None:
        while self._heap:
            key1, key2, node = self._heap[0]
            if self._active_keys.get(node) == (key1, key2):
                return
            heapq.heappop(self._heap)

    def _top_key(self) -> Key:
        self._discard_stale_head()
        if not self._heap:
            return INF, INF
        key1, key2, _ = self._heap[0]
        return key1, key2

    def _pop(self) -> Optional[tuple[Node, Key]]:
        while self._heap:
            key1, key2, node = heapq.heappop(self._heap)
            key = (key1, key2)
            if self._active_keys.get(node) != key:
                continue
            del self._active_keys[node]
            return node, key
        return None

    def _update_vertex(self, node: Node) -> None:
        if node != self.goal:
            successors = self._neighbors(node)
            self.rhs[node] = min(
                (
                    self._cost(node, successor) + self._g(successor)
                    for successor in successors
                ),
                default=INF,
            )

        self._remove(node)
        if self._g(node) != self._rhs(node):
            self._push(node)

    def _initialize(self) -> None:
        self.rhs[self.goal] = 0.0
        self.g[self.goal] = INF
        self._push(self.goal)

    def _compute_shortest_path(self) -> None:
        max_expansions = max(1, self.H * self.W * 50)
        expansions_this_call = 0

        while (
            self._top_key() < self._key(self.start)
            or self._rhs(self.start) != self._g(self.start)
        ):
            result = self._pop()
            if result is None:
                break

            node, old_key = result
            new_key = self._key(node)
            if old_key < new_key:
                self._push(node)
            elif self._g(node) > self._rhs(node):
                self.g[node] = self._rhs(node)
                for predecessor in self._adjacent(node):
                    self._update_vertex(predecessor)
            else:
                self.g[node] = INF
                self._update_vertex(node)
                for predecessor in self._adjacent(node):
                    self._update_vertex(predecessor)

            self.expansions += 1
            expansions_this_call += 1
            if expansions_this_call > max_expansions:
                raise RuntimeError(
                    "D* Lite failed to converge within the finite-grid expansion bound"
                )

    def plan(self) -> Optional[list[Node]]:
        """Compute and return an initial path from start to goal."""

        if not self._free(*self.start) or not self._free(*self.goal):
            return None
        self._compute_shortest_path()
        return self._extract_path()

    def update_edge(self, x: int, y: int, blocked: bool) -> None:
        """Mark one cell blocked or free; call :meth:`replan` afterwards."""

        self._validate_node((x, y), "updated cell")
        new_value = 1 if blocked else 0
        if int(self.grid[y, x]) == new_value:
            return

        self.grid[y, x] = new_value
        changed = (x, y)
        for node in [changed, *self._adjacent(changed)]:
            self._update_vertex(node)

    def replan(self, new_start: Optional[Node] = None) -> Optional[list[Node]]:
        """Incrementally repair the path, optionally from a moved start."""

        if new_start is not None:
            self._validate_node(new_start, "new start")
            if new_start != self.start:
                self.km += _heuristic(self.start, new_start)
                self.start = new_start

        self.replan_count += 1
        if not self._free(*self.start) or not self._free(*self.goal):
            return None
        self._compute_shortest_path()
        return self._extract_path()

    def _extract_path(self) -> Optional[list[Node]]:
        """Extract a loop-free greedy path from the current value function."""

        if self._g(self.start) == INF:
            return None

        path = [self.start]
        current = self.start
        visited = {current}

        for _ in range(self.H * self.W):
            if current == self.goal:
                return path

            neighbors = self._neighbors(current)
            if not neighbors:
                return None

            next_node = min(
                neighbors,
                key=lambda node: (
                    self._cost(current, node) + self._g(node),
                    node,
                ),
            )
            if self._cost(current, next_node) + self._g(next_node) == INF:
                return None
            if next_node in visited:
                return None

            path.append(next_node)
            visited.add(next_node)
            current = next_node

        return None
