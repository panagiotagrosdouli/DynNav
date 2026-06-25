"""Core implementation for Contribution 01: Learned A* Heuristics.

The module deliberately separates three concepts that are often conflated in
learning-augmented planning:

1. A* optimality: guaranteed when the heuristic is admissible.
2. Learned efficiency: possible when the learned heuristic is more informative.
3. Empirical validity: checked by comparing path cost against an optimal A* run.

For a 4-neighbour unit-cost grid, Manhattan distance is an admissible baseline.
A raw neural heuristic may reduce expansions, but it is not automatically
admissible.  The ``manhattan_clipped`` mode is admissible because it returns
``min(h_theta, h_manhattan)`` after non-negativity clipping, but this mode is
conservative and should not be claimed to outperform Manhattan A* in general.
"""

from __future__ import annotations

import argparse
import heapq
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol

import matplotlib.pyplot as plt
import numpy as np

MODULE_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = MODULE_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

try:  # Torch is only required when a neural checkpoint is actually used.
    import torch
except Exception:  # pragma: no cover - keeps classical A* usable without torch.
    torch = None

try:
    from learned_heuristic import HeuristicNet
except Exception:  # pragma: no cover - useful for lightweight reproducibility.
    HeuristicNet = None

try:
    from heuristic_logger import HeuristicLogger
except Exception:  # pragma: no cover - logger is optional.
    HeuristicLogger = None

Grid = np.ndarray
Node = tuple[int, int]
PathLike = list[Node] | None


# ---------------- Grid world ----------------

def make_grid() -> Grid:
    """Create the fixed 40x40 benchmark grid used by the C01 demo."""
    height, width = 40, 40
    grid = np.zeros((height, width), dtype=np.int32)

    grid[5, 2:35] = 1
    grid[15, 5:30] = 1
    grid[10:30, 20] = 1
    grid[25:30, 8:15] = 1

    return grid


def in_bounds(grid: Grid, node: Node) -> bool:
    x, y = node
    height, width = grid.shape
    return 0 <= x < width and 0 <= y < height


def is_free(grid: Grid, node: Node) -> bool:
    x, y = node
    return in_bounds(grid, node) and grid[y, x] == 0


def manhattan(p: Node, q: Node) -> float:
    """Admissible and consistent heuristic for 4-neighbour unit-cost grids."""
    return float(abs(q[0] - p[0]) + abs(q[1] - p[1]))


def euclidean(p: Node, q: Node) -> float:
    dx = q[0] - p[0]
    dy = q[1] - p[1]
    return float((dx * dx + dy * dy) ** 0.5)


class Heuristic(Protocol):
    def __call__(self, node: Node, goal: Node, grid: Grid) -> float:
        ...


def reconstruct_path(parent: dict[Node, Node | None], goal: Node) -> list[Node]:
    path: list[Node] = []
    node: Node | None = goal
    while node is not None:
        path.append(node)
        node = parent[node]
    path.reverse()
    return path


def astar_search(grid: Grid, start: Node, goal: Node, heuristic: Heuristic) -> tuple[PathLike, int]:
    """Generic A* search for a 4-neighbour, unit-cost grid."""
    if not is_free(grid, start):
        raise ValueError(f"Start node {start} is outside the grid or blocked.")
    if not is_free(grid, goal):
        raise ValueError(f"Goal node {goal} is outside the grid or blocked.")

    neighbors_4 = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    g_score: dict[Node, float] = {start: 0.0}
    parent: dict[Node, Node | None] = {start: None}

    open_pq: list[tuple[float, float, Node]] = [(heuristic(start, goal, grid), 0.0, start)]
    closed: set[Node] = set()
    expansions = 0

    while open_pq:
        _, g_curr, curr = heapq.heappop(open_pq)
        if curr in closed:
            continue
        closed.add(curr)
        expansions += 1

        if curr == goal:
            return reconstruct_path(parent, goal), expansions

        x, y = curr
        for dx, dy in neighbors_4:
            neigh = (x + dx, y + dy)
            if not is_free(grid, neigh):
                continue

            tentative_g = g_curr + 1.0
            if tentative_g < g_score.get(neigh, float("inf")):
                g_score[neigh] = tentative_g
                parent[neigh] = curr
                h_val = heuristic(neigh, goal, grid)
                heapq.heappush(open_pq, (tentative_g + h_val, tentative_g, neigh))

    return None, expansions


# ---------------- Classic A* ----------------

def astar_classic(grid: Grid, start: Node, goal: Node) -> tuple[PathLike, int]:
    """Optimal A* baseline using Manhattan distance."""
    return astar_search(grid, start, goal, lambda node, target, _: manhattan(node, target))


# ---------------- True remaining cost map ----------------

def compute_true_remaining_cost(path: Iterable[Node] | None) -> dict[Node, int]:
    """Map each node on a path to its remaining number of steps to the goal."""
    if path is None:
        return {}
    path_list = list(path)
    length = len(path_list)
    return {node: length - i - 1 for i, node in enumerate(path_list)}


# ---------------- Learned heuristic wrapper ----------------

@dataclass
class LearnedHeuristicWrapper:
    """Neural heuristic wrapper with explicit admissibility mode.

    Parameters
    ----------
    model_path:
        Path to a PyTorch state_dict checkpoint for ``HeuristicNet``.
    logger:
        Optional logger with a ``record(features, node)`` method.
    mode:
        ``raw`` returns the non-negative neural estimate. This may improve
        efficiency but does not guarantee optimality.
        ``manhattan_clipped`` returns ``min(raw, Manhattan)``. This is admissible
        for 4-neighbour unit-cost grids but conservative.
        ``zero`` returns 0 and is useful as a Dijkstra-style sanity check.
    allow_missing_model:
        If true, missing model files fall back to Manhattan distance with a
        warning. This keeps the demo reproducible even before training.
    """

    model_path: str | Path = "heuristic_net_rich.pt"
    logger: object | None = None
    mode: str = "raw"
    allow_missing_model: bool = True

    def __post_init__(self) -> None:
        self.model_path = Path(self.model_path)
        self.device = torch.device("cpu") if torch is not None else None
        self.model = None

        valid_modes = {"raw", "manhattan_clipped", "zero"}
        if self.mode not in valid_modes:
            raise ValueError(f"Unknown heuristic mode {self.mode!r}. Expected one of {sorted(valid_modes)}.")

        if self.mode == "zero":
            return

        if torch is None or HeuristicNet is None or not self.model_path.exists():
            if not self.allow_missing_model:
                raise FileNotFoundError(
                    f"Cannot load learned heuristic from {self.model_path}. "
                    "Check that torch, learned_heuristic.py and the checkpoint exist."
                )
            print(
                "[WARN] Learned heuristic model is unavailable; falling back to Manhattan heuristic. "
                "Train or provide heuristic_net_rich.pt for learned evaluation."
            )
            return

        self.model = HeuristicNet(input_dim=11)
        try:
            state = torch.load(self.model_path, map_location=self.device, weights_only=True)
        except TypeError:  # Older PyTorch versions do not support weights_only.
            state = torch.load(self.model_path, map_location=self.device)
        self.model.load_state_dict(state)
        self.model.to(self.device)
        self.model.eval()

    def _compute_features(self, node: Node, goal: Node, grid: Grid) -> np.ndarray:
        x, y = node
        gx, gy = goal
        height, width = grid.shape

        dx = gx - x
        dy = gy - y
        abs_dx = abs(dx)
        abs_dy = abs(dy)

        free_neighbors = 0
        for nx, ny in [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]:
            if 0 <= nx < width and 0 <= ny < height and grid[ny, nx] == 0:
                free_neighbors += 1
        blocked_neighbors = 4 - free_neighbors

        x_min = max(0, x - 1)
        x_max = min(width, x + 2)
        y_min = max(0, y - 1)
        y_max = min(height, y + 2)
        window = grid[y_min:y_max, x_min:x_max]
        obstacle_density = float(np.mean(window != 0)) if window.size else 0.0
        is_near_obstacle = 1.0 if obstacle_density > 0 else 0.0

        return np.array(
            [
                dx,
                dy,
                euclidean(node, goal),
                manhattan(node, goal),
                max(abs_dx, abs_dy),
                free_neighbors,
                blocked_neighbors,
                obstacle_density,
                is_near_obstacle,
                x / max(width - 1, 1),
                y / max(height - 1, 1),
            ],
            dtype=np.float32,
        )

    def _raw_model_prediction(self, node: Node, goal: Node, grid: Grid) -> float:
        if self.model is None:
            return manhattan(node, goal)

        features = self._compute_features(node, goal, grid)
        with torch.no_grad():
            x_t = torch.from_numpy(features).to(self.device)
            out = self.model(x_t)
        raw = float(out.item())

        if self.logger is not None and hasattr(self.logger, "record"):
            self.logger.record(features, node)

        # Negative heuristics remain admissible but hurt efficiency; clamp to 0.
        return max(0.0, raw)

    def h(self, node: Node, goal: Node, grid: Grid) -> float:
        if self.mode == "zero":
            return 0.0

        raw = self._raw_model_prediction(node, goal, grid)
        if self.mode == "manhattan_clipped":
            return min(raw, manhattan(node, goal))
        return raw


# ---------------- Learned A* ----------------

def astar_learned(grid: Grid, start: Node, goal: Node, learned_h: LearnedHeuristicWrapper) -> tuple[PathLike, int]:
    return astar_search(grid, start, goal, learned_h.h)


# ---------------- Visualization ----------------

def plot_paths(grid: Grid, path_c: PathLike, path_l: PathLike, start: Node, goal: Node) -> None:
    if path_c is None or path_l is None:
        raise ValueError("Cannot plot missing paths.")

    height, width = grid.shape
    img = np.ones((height, width, 3), dtype=np.float32)
    img[grid == 1] = [0.0, 0.0, 0.0]

    plt.figure(figsize=(6, 6))
    plt.imshow(img, origin="lower")

    xs_c = [p[0] for p in path_c]
    ys_c = [p[1] for p in path_c]
    xs_l = [p[0] for p in path_l]
    ys_l = [p[1] for p in path_l]

    plt.plot(xs_c, ys_c, "g-", label="A* classic")
    plt.plot(xs_l, ys_l, "r--", label="A* learned")
    plt.scatter([start[0]], [start[1]], c="blue", marker="o", label="start")
    plt.scatter([goal[0]], [goal[1]], c="yellow", marker="*", label="goal")
    plt.legend()
    plt.title("Classic vs Learned A*")
    plt.tight_layout()
    plt.show()


# ---------------- Main ----------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--mode", choices=["raw", "manhattan_clipped", "zero"], default="raw")
    parser.add_argument("--model", default="heuristic_net_rich.pt")
    args = parser.parse_args()

    grid = make_grid()
    start = (1, 1)
    goal = (35, 35)

    print("Running A* classic...")
    path_c, exp_c = astar_classic(grid, start, goal)
    print(f"classic: path length={len(path_c) if path_c else 0}, expansions={exp_c}")

    logger = None
    if HeuristicLogger is not None and path_c is not None:
        true_cost_map = compute_true_remaining_cost(path_c)
        logger = HeuristicLogger("heuristic_logs.npz", true_cost_map=true_cost_map)

    print(f"Running A* with learned heuristic mode={args.mode!r}...")
    lh = LearnedHeuristicWrapper(model_path=args.model, logger=logger, mode=args.mode)
    path_l, exp_l = astar_learned(grid, start, goal, lh)
    print(f"learned: path length={len(path_l) if path_l else 0}, expansions={exp_l}")

    if logger is not None:
        logger.save()

    if args.demo:
        plot_paths(grid, path_c, path_l, start, goal)


if __name__ == "__main__":
    main()
