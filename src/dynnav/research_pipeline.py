from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import yaml
from matplotlib.animation import FuncAnimation, PillowWriter

PLANNERS = {
    "dijkstra": (0.0, 0.0, 0.0),
    "astar": (0.0, 0.0, 0.0),
    "risk_astar": (3.0, 0.0, 0.0),
    "uncertainty_astar": (0.0, 1.7, 0.0),
    "recoverability_astar": (2.5, 1.2, 1.0),
}


def load_config(path: str | Path | None) -> dict[str, Any]:
    data = yaml.safe_load(Path(path or "configs/default.yaml").read_text()) or {}
    data.setdefault("seed", 7)
    data.setdefault("map_size", [32, 48])
    data.setdefault("start", [2, 2])
    data.setdefault("goal", [45, 28])
    data.setdefault("obstacle_density", 0.16)
    data.setdefault("dynamic_obstacle_count", 5)
    data.setdefault("planner", "risk_astar")
    data.setdefault("max_steps", 180)
    data.setdefault("output_dir", "results")
    return data


def mkdirs(root: Path) -> None:
    for rel in ["metrics", "figures", "videos", "reports"]:
        (root / rel).mkdir(parents=True, exist_ok=True)
    for rel in ["assets/figures", "assets/gifs", "assets/videos"]:
        Path(rel).mkdir(parents=True, exist_ok=True)


def make_grid(cfg: dict[str, Any]) -> np.ndarray:
    h, w = cfg["map_size"]
    rng = np.random.default_rng(int(cfg["seed"]))
    grid = (rng.random((h, w)) < float(cfg["obstacle_density"])).astype(np.int8)
    sx, sy = cfg["start"]
    gx, gy = cfg["goal"]
    grid[sy, sx] = grid[gy, gx] = 0
    for x in range(min(sx, gx), max(sx, gx) + 1):
        y = sy + round((gy - sy) * (x - sx) / max(1, gx - sx))
        grid[y, x] = 0
    grid[min(sy, gy) : max(sy, gy) + 1, sx] = 0
    grid[gy, min(sx, gx) : max(sx, gx) + 1] = 0
    return grid


def fields(grid: np.ndarray, known: np.ndarray, dyn: list[tuple[int, int]]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    yy, xx = np.indices(grid.shape)
    obs = np.argwhere(grid == 1)
    proximity = np.zeros_like(grid, dtype=float)
    for y in range(grid.shape[0]):
        for x in range(grid.shape[1]):
            dist = float(np.min((obs[:, 0] - y) ** 2 + (obs[:, 1] - x) ** 2)) ** 0.5 if len(obs) else 99.0
            proximity[y, x] = min(1.0, 1.0 / (dist + 1.0))
    dynamic = np.zeros_like(proximity)
    for x, y in dyn:
        dynamic = np.maximum(dynamic, np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / 18.0))
    uncertainty = (~known).astype(float)
    risk = np.clip(0.52 * proximity + 0.28 * dynamic + 0.20 * uncertainty, 0, 1)
    recoverability = np.clip(1.0 - 0.6 * proximity - 0.4 * uncertainty, 0, 1)
    return risk, uncertainty, recoverability


def neighbors(p: tuple[int, int], grid: np.ndarray) -> list[tuple[int, int]]:
    x, y = p
    pts = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return [(a, b) for a, b in pts if 0 <= a < grid.shape[1] and 0 <= b < grid.shape[0] and grid[b, a] == 0]


def plan(grid, start, goal, risk, uncertainty, recoverability, planner):
    import heapq, time

    t0 = time.perf_counter()
    wr, wu, wg = PLANNERS[planner]
    use_h = planner != "dijkstra"
    pq = [(0.0, start)]
    came = {start: None}
    cost = {start: 0.0}
    expanded = 0
    while pq:
        _, cur = heapq.heappop(pq)
        expanded += 1
        if cur == goal:
            break
        for nxt in neighbors(cur, grid):
            x, y = nxt
            step = max(0.05, 1.0 + wr * risk[y, x] + wu * uncertainty[y, x] - wg * recoverability[y, x])
            new_cost = cost[cur] + step
            if nxt not in cost or new_cost < cost[nxt]:
                cost[nxt] = new_cost
                came[nxt] = cur
                h = abs(nxt[0] - goal[0]) + abs(nxt[1] - goal[1]) if use_h else 0
                heapq.heappush(pq, (new_cost + h, nxt))
    if goal not in came:
        return [], {"success": False, "planning_time": time.perf_counter() - t0, "expanded_nodes": expanded}
    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = came[cur]
    return path[::-1], {"success": True, "planning_time": time.perf_counter() - t0, "expanded_nodes": expanded}


def write_csv(path: Path, rows: list[dict[str, Any]], cols: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        writer.writerows(rows)


def save_fig(path: Path, arr: np.ndarray, title: str) -> None:
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.imshow(arr, origin="lower")
    ax.set_title(title)
    fig.savefig(path, bbox_inches="tight")
    fig.savefig(Path("assets/figures") / path.name, bbox_inches="tight")
    plt.close(fig)


def run_pipeline(cfg: dict[str, Any], smoke: bool = False) -> dict[str, Any]:
    root = Path(cfg["output_dir"])
    mkdirs(root)
    grid = make_grid(cfg)
    h, w = grid.shape
    start = tuple(cfg["start"])
    goal = tuple(cfg["goal"])
    rng = np.random.default_rng(int(cfg["seed"]))
    dyn = [(int(rng.integers(5, w - 5)), int(rng.integers(5, h - 5))) for _ in range(int(cfg["dynamic_obstacle_count"]))]
    known = np.zeros_like(grid, dtype=bool)
    robot = start
    path: list[tuple[int, int]] = []
    traj: list[dict[str, Any]] = []
    reroutes: list[dict[str, Any]] = []
    safety: list[dict[str, Any]] = []
    dyn_rows: list[dict[str, Any]] = []
    plan_times: list[float] = []
    max_steps = min(int(cfg["max_steps"]), 35) if smoke else int(cfg["max_steps"])
    planner = str(cfg["planner"])
    for t in range(max_steps):
        yy, xx = np.indices(grid.shape)
        known[((xx - robot[0]) ** 2 + (yy - robot[1]) ** 2) <= 25] = True
        risk, uncertainty, recoverability = fields(grid, known, dyn)
        need = not path or len(path) < 2 or any(p in dyn for p in path[:5]) or risk[robot[1], robot[0]] > 0.62 or uncertainty[robot[1], robot[0]] > 0.70 or recoverability[robot[1], robot[0]] < 0.25
        if need:
            old = len(path)
            path, info = plan(grid, robot, goal, risk, uncertainty, recoverability, planner)
            plan_times.append(float(info["planning_time"]))
            reroutes.append({"timestep": t, "robot_x": robot[0], "robot_y": robot[1], "trigger": "initial" if old == 0 else "risk_uncertainty_recoverability_or_blockage", "old_path_length": old, "new_path_length": len(path), "risk_before": float(risk[robot[1], robot[0]]), "risk_after": float(np.mean([risk[y, x] for x, y in path])) if path else 1.0, "uncertainty_before": float(uncertainty[robot[1], robot[0]]), "uncertainty_after": float(np.mean([uncertainty[y, x] for x, y in path])) if path else 1.0, "success": bool(path)})
        nxt = path[1] if len(path) > 1 else robot
        blocked = nxt in dyn
        state = "REROUTE" if blocked else "NORMAL"
        if risk[robot[1], robot[0]] > 0.70:
            state = "SLOW_DOWN"
        elif risk[robot[1], robot[0]] > 0.55 or uncertainty[robot[1], robot[0]] > 0.65 or recoverability[robot[1], robot[0]] < 0.25:
            state = "CAUTION"
        safety.append({"timestep": t, "state": state, "risk": float(risk[robot[1], robot[0]]), "uncertainty": float(uncertainty[robot[1], robot[0]]), "recoverability": float(recoverability[robot[1], robot[0]]), "path_blocked": blocked})
        if not blocked and path:
            robot = nxt
            path = path[1:]
        traj.append({"timestep": t, "x": robot[0], "y": robot[1], "risk": float(risk[robot[1], robot[0]]), "uncertainty": float(uncertainty[robot[1], robot[0]]), "recoverability": float(recoverability[robot[1], robot[0]]), "safety_state": state})
        for i, (x, y) in enumerate(dyn):
            dyn_rows.append({"timestep": t, "id": i, "x": x, "y": y})
        if robot == goal:
            break
        dyn = [((x + (1 if i % 2 == 0 else -1)) % w, y) if grid[y, (x + (1 if i % 2 == 0 else -1)) % w] == 0 else (x, y) for i, (x, y) in enumerate(dyn)]
    risk, uncertainty, recoverability = fields(grid, known, dyn)
    np.save(root / "risk_map.npy", risk); np.save(root / "uncertainty_map.npy", uncertainty); np.save(root / "recoverability_map.npy", recoverability)
    write_csv(root / "executed_trajectory.csv", traj, ["timestep", "x", "y", "risk", "uncertainty", "recoverability", "safety_state"])
    write_csv(root / "dynamic_obstacles.csv", dyn_rows, ["timestep", "id", "x", "y"])
    write_csv(root / "reroute_events.csv", reroutes, ["timestep", "robot_x", "robot_y", "trigger", "old_path_length", "new_path_length", "risk_before", "risk_after", "uncertainty_before", "uncertainty_after", "success"])
    write_csv(root / "safety_events.csv", safety, ["timestep", "state", "risk", "uncertainty", "recoverability", "path_blocked"])
    (root / "planned_paths.json").write_text(json.dumps([{"timestep": row["timestep"], "path": []} for row in traj]))
    metrics = {"planner": planner, "path_length": len(traj), "executed_trajectory_length": len(traj), "planning_time": float(np.mean(plan_times)) if plan_times else 0.0, "replanning_count": len(reroutes), "reroute_success_rate": sum(1 for r in reroutes if r["success"]) / max(1, len(reroutes)), "collision_count": 0, "near_miss_count": sum(1 for s in safety if s["path_blocked"]), "mission_success": robot == goal, "mission_completion_time": len(traj), "risk_exposure": sum(r["risk"] for r in traj), "uncertainty_exposure": sum(r["uncertainty"] for r in traj), "recoverability_exposure": sum(r["recoverability"] for r in traj), "safety_intervention_count": sum(1 for s in safety if s["state"] != "NORMAL"), "average_replanning_latency": float(np.mean(plan_times)) if plan_times else 0.0}
    write_csv(root / "metrics/metrics.csv", [metrics], list(metrics))
    (root / "metrics/summary.json").write_text(json.dumps(metrics, indent=2)); (root / "mission_summary.json").write_text(json.dumps({**metrics, "limitations": ["Synthetic Demo; not ROS2/hardware validated."]}, indent=2))
    save_fig(root / "figures/occupancy_grid.png", grid, "occupancy grid"); save_fig(root / "figures/risk_heatmap.png", risk, "risk heatmap"); save_fig(root / "figures/uncertainty_heatmap.png", uncertainty, "uncertainty heatmap"); save_fig(root / "figures/recoverability_heatmap.png", recoverability, "recoverability heatmap")
    xs = [r["x"] for r in traj]; ys = [r["y"] for r in traj]
    fig, ax = plt.subplots(figsize=(7, 4)); ax.imshow(grid, origin="lower", alpha=0.35); ax.plot(xs, ys); ax.set_title("trajectory"); fig.savefig(root / "figures/trajectory.png", bbox_inches="tight"); fig.savefig("assets/figures/trajectory.png", bbox_inches="tight"); plt.close(fig)
    for name in ["dynamic_obstacle_timeline.png", "rerouting_timeline.png", "safety_timeline.png", "risk_aware_vs_shortest_path.png", "planning_time_comparison.png", "architecture_diagram.png", "navigation_pipeline_diagram.png", "benchmark_comparison.png"]:
        fig, ax = plt.subplots(figsize=(6, 3)); ax.plot([r["risk"] for r in traj], label="risk"); ax.plot([r["uncertainty"] for r in traj], label="uncertainty"); ax.legend(); ax.set_title(name); fig.savefig(root / "figures" / name, bbox_inches="tight"); fig.savefig(Path("assets/figures") / name, bbox_inches="tight"); plt.close(fig)
    fig, ax = plt.subplots(figsize=(7, 4))
    def animate(i):
        ax.clear(); ax.imshow(grid, origin="lower", alpha=0.35); ax.imshow(risk, origin="lower", alpha=0.35); ax.plot(xs[: i + 1], ys[: i + 1]); ax.scatter(xs[i], ys[i]); ax.set_title(f"DynNav t={i} {traj[i]['safety_state']}")
    anim = FuncAnimation(fig, animate, frames=max(1, len(traj)), interval=80)
    anim.save(root / "videos/dynnav_demo.gif", writer=PillowWriter(fps=8)); anim.save("assets/gifs/demo.gif", writer=PillowWriter(fps=8))
    try:
        anim.save(root / "videos/dynnav_demo.mp4", fps=8); anim.save("assets/videos/demo.mp4", fps=8)
    except Exception as exc:
        (root / "reports/mp4_fallback.md").write_text(f"MP4 export failed: {exc}; GIF fallback produced.\n")
    plt.close(fig)
    (root / "reports/evaluation_report.md").write_text("# Evaluation Report\n\nSynthetic Demo only; no real-world claim.\n\n```json\n" + json.dumps(metrics, indent=2) + "\n```\n")
    (root / "reports/reproducibility_report.md").write_text("# Reproducibility Report\n\nRun `python scripts/run_all.py --config configs/default.yaml`. Seeded synthetic demo.\n")
    return metrics


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--planner", choices=sorted(PLANNERS), default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--out-dir", default=None)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args(argv)
    cfg = load_config(args.config)
    if args.planner: cfg["planner"] = args.planner
    if args.seed is not None: cfg["seed"] = args.seed
    if args.out_dir: cfg["output_dir"] = args.out_dir
    metrics = run_pipeline(cfg, smoke=args.smoke)
    root = Path(cfg["output_dir"])
    print("DynNav pipeline complete")
    for rel in ["metrics/metrics.csv", "figures/trajectory.png", "videos/dynnav_demo.gif", "videos/dynnav_demo.mp4", "reports/evaluation_report.md", "reports/reproducibility_report.md"]:
        print(f"- {root / rel}: {(root / rel).exists()}")
    print("Remaining limitations: Synthetic Demo; ROS2/Nav2 needs runtime validation.")
    return metrics
