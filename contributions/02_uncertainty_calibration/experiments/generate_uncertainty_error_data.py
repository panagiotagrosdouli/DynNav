from __future__ import annotations

import csv
import heapq
import random
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[3]
C01 = ROOT / "contributions" / "01_learned_astar"
CODE = C01 / "code"
MODELS = C01 / "models"
OUT = ROOT / "contributions" / "02_uncertainty_calibration" / "phd_experiments" / "uncertainty_error_data.csv"

sys.path.insert(0, str(CODE))
from learned_heuristic_uncertainty import HeuristicNetUncertainty  # noqa: E402


class GridWorld:
    def __init__(self, width, height, start, goal, obstacles):
        self.width = width
        self.height = height
        self.start = start
        self.goal = goal
        self.obstacles = set(obstacles)

    def successors(self, s):
        x, y = s
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nxt = (x + dx, y + dy)
            if 0 <= nxt[0] < self.width and 0 <= nxt[1] < self.height and nxt not in self.obstacles:
                yield nxt, 1.0


def dijkstra_from_goal(problem):
    goal = problem.goal
    dist = {goal: 0.0}
    pq = [(0.0, goal)]
    while pq:
        d, s = heapq.heappop(pq)
        if d > dist[s]:
            continue
        for nxt, cost in problem.successors(s):
            nd = d + cost
            if nxt not in dist or nd < dist[nxt]:
                dist[nxt] = nd
                heapq.heappush(pq, (nd, nxt))
    return dist


def make_grid(width, height, density):
    obs = set()
    for x in range(width):
        for y in range(height):
            if random.random() < density:
                obs.add((x, y))
    start = (0, 0)
    goal = (width - 1, height - 1)
    obs.discard(start)
    obs.discard(goal)
    return GridWorld(width, height, start, goal, obs)


def main():
    model_path = MODELS / "heuristic_net_unc.pt"
    stats_path = MODELS / "planner_dataset_norm_stats.npz"
    if not model_path.exists():
        raise FileNotFoundError(model_path)
    if not stats_path.exists():
        raise FileNotFoundError(stats_path)

    net = HeuristicNetUncertainty()
    net.load_state_dict(torch.load(model_path, map_location="cpu"))
    net.eval()
    stats = np.load(stats_path)
    mean = stats["mean"].astype(np.float32)
    std = stats["std"].astype(np.float32)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["instance_id", "state_x", "state_y", "h_star", "mu", "sigma", "error", "abs_error", "rel_error", "grid_size"]
    random.seed(0)
    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for inst in range(1, 31):
            problem = make_grid(32, 32, 0.15)
            h_star_map = dijkstra_from_goal(problem)
            for (x, y), h_star in h_star_map.items():
                feat = np.array([[x, y, problem.goal[0], problem.goal[1]]], dtype=np.float32)
                feat = (feat - mean) / std
                with torch.no_grad():
                    mu, log_var = net(torch.tensor(feat, dtype=torch.float32))
                mu = float(mu.squeeze().item())
                log_var = float(np.clip(log_var.squeeze().item(), -20.0, 20.0))
                sigma = float(np.sqrt(np.exp(log_var)))
                err = mu - h_star
                writer.writerow({
                    "instance_id": inst,
                    "state_x": x,
                    "state_y": y,
                    "h_star": h_star,
                    "mu": mu,
                    "sigma": sigma,
                    "error": err,
                    "abs_error": abs(err),
                    "rel_error": err / (h_star + 1e-6),
                    "grid_size": 32,
                })
            print(f"[INFO] instance {inst}/30 processed")
    print(f"[INFO] Saved normalized uncertainty-error data to {OUT}")


if __name__ == "__main__":
    main()
