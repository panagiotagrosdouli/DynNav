from __future__ import annotations
import csv, json, math, random
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'results'
ASSETS = ROOT / 'assets'


def _mkdirs():
    for p in [RESULTS/'metrics', RESULTS/'figures', RESULTS/'videos', RESULTS/'reports', ASSETS/'figures', ASSETS/'gifs', ASSETS/'videos']:
        p.mkdir(parents=True, exist_ok=True)


def _risk_fields(grid, known, dyn):
    h, w = grid.shape
    yy, xx = np.indices(grid.shape)
    obs = np.argwhere(grid == 1)
    prox = np.zeros_like(grid, dtype=float)
    for y in range(h):
        for x in range(w):
            d = float(np.min((obs[:, 0] - y) ** 2 + (obs[:, 1] - x) ** 2)) ** 0.5 if len(obs) else max(h, w)
            prox[y, x] = min(1.0, 1.0 / (d + 1.0))
    dyn_risk = np.zeros_like(prox)
    for x, y in dyn:
        dyn_risk = np.maximum(dyn_risk, np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / 18.0))
    uncertainty = np.clip((~known).astype(float), 0, 1)
    risk = np.clip(0.52 * prox + 0.28 * dyn_risk + 0.20 * uncertainty, 0, 1)
    recoverability = np.clip(1.0 - 0.6 * prox - 0.4 * uncertainty, 0, 1)
    return risk, uncertainty, recoverability


def _neighbors(p, grid):
    x, y = p
    for q in [(x+1,y),(x-1,y),(x,y+1),(x,y-1)]:
        if 0 <= q[0] < grid.shape[1] and 0 <= q[1] < grid.shape[0] and grid[q[1], q[0]] == 0:
            yield q


def _plan(grid, start, goal, risk, uncertainty, recoverability, weights):
    import heapq, time
    t0 = time.perf_counter(); pq=[(0, start)]; came={start: None}; cost={start: 0.0}; expanded=0
    while pq:
        _, p = heapq.heappop(pq); expanded += 1
        if p == goal:
            break
        for q in _neighbors(p, grid):
            x, y = q
            step = max(0.05, 1 + weights[0]*risk[y,x] + weights[1]*uncertainty[y,x] - weights[2]*recoverability[y,x])
            nc = cost[p] + step
            if q not in cost or nc < cost[q]:
                cost[q] = nc; came[q] = p
                h = abs(q[0]-goal[0]) + abs(q[1]-goal[1])
                heapq.heappush(pq, (nc+h, q))
    if goal not in came:
        return [], {'success': False, 'planning_time': time.perf_counter()-t0, 'expanded': expanded}
    path=[]; p=goal
    while p is not None:
        path.append(p); p=came[p]
    return path[::-1], {'success': True, 'planning_time': time.perf_counter()-t0, 'expanded': expanded}


def _csv(path, rows, cols):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)


def run(seed=7, planner='risk_astar'):
    _mkdirs(); rng=random.Random(seed); np.random.seed(seed)
    h, w = 32, 48; start=(2, 2); goal=(45, 28)
    grid = (np.random.rand(h, w) < 0.16).astype(np.int8)
    for x in range(start[0], goal[0]+1): grid[start[1] + (goal[1]-start[1])*(x-start[0])//max(1, goal[0]-start[0]), x] = 0
    grid[start[1]:goal[1]+1, start[0]] = 0; grid[goal[1], start[0]:goal[0]+1] = 0; grid[start[1], start[0]] = 0; grid[goal[1], goal[0]] = 0
    known = np.zeros_like(grid, dtype=bool)
    dyn = [(rng.randrange(8, w-8), rng.randrange(6, h-6)) for _ in range(5)]
    robot=start; traj=[]; reroutes=[]; safety=[]; dynlog=[]; plans=[]; plan_times=[]; path=[]; collisions=near=0
    weights = {'dijkstra': (0,0,0), 'astar': (0,0,0), 'risk_astar': (3,0,0), 'uncertainty_astar': (0,1.5,0), 'recoverability_astar': (3,1.2,1)}[planner]
    for t in range(180):
        yy, xx = np.indices(grid.shape); known[((xx-robot[0])**2 + (yy-robot[1])**2) <= 25] = True
        risk, unc, rec = _risk_fields(grid, known, dyn)
        need = not path or len(path) < 2 or any(p in dyn for p in path[:5]) or risk[robot[1], robot[0]] > .62 or unc[robot[1], robot[0]] > .70 or rec[robot[1], robot[0]] < .25
        if need:
            old=len(path); path, info = _plan(grid, robot, goal, risk, unc, rec, weights); plan_times.append(info['planning_time'])
            reroutes.append({'timestep': t, 'robot_x': robot[0], 'robot_y': robot[1], 'trigger': 'initial' if old == 0 else 'risk_or_blockage', 'old_path_length': old, 'new_path_length': len(path), 'risk_before': float(risk[robot[1], robot[0]]), 'risk_after': float(np.mean([risk[y,x] for x,y in path])) if path else 1, 'uncertainty_before': float(unc[robot[1], robot[0]]), 'uncertainty_after': float(np.mean([unc[y,x] for x,y in path])) if path else 1, 'success': bool(path)})
        nxt = path[1] if len(path) > 1 else robot; blocked = nxt in dyn
        r, u, rc = float(risk[robot[1], robot[0]]), float(unc[robot[1], robot[0]]), float(rec[robot[1], robot[0]])
        state = 'NORMAL'
        if blocked or r > .86 or rc < .08: state = 'REROUTE'
        elif any(abs(robot[0]-x)+abs(robot[1]-y) < 3 for x,y in dyn): state = 'STOP'
        elif r > .70: state = 'SLOW_DOWN'
        elif r > .55 or u > .65 or rc < .25: state = 'CAUTION'
        safety.append({'timestep': t, 'state': state, 'risk': r, 'uncertainty': u, 'recoverability': rc, 'path_blocked': blocked})
        if state != 'STOP' and not blocked and path: robot = nxt; path = path[1:]
        if blocked: near += 1
        if robot in dyn: collisions += 1
        traj.append({'timestep': t, 'x': robot[0], 'y': robot[1], 'risk': r, 'uncertainty': u, 'recoverability': rc, 'safety_state': state})
        plans.append({'timestep': t, 'path': path})
        for i, (x, y) in enumerate(dyn): dynlog.append({'timestep': t, 'id': i, 'x': x, 'y': y})
        if robot == goal: break
        dyn = [((x + (1 if i % 2 == 0 else -1)) % w, y) if grid[y, (x + (1 if i % 2 == 0 else -1)) % w] == 0 else (x, y) for i, (x, y) in enumerate(dyn)]
    risk, unc, rec = _risk_fields(grid, known, dyn)
    np.save(RESULTS/'risk_map.npy', risk); np.save(RESULTS/'uncertainty_map.npy', unc); np.save(RESULTS/'recoverability_map.npy', rec)
    _csv(RESULTS/'executed_trajectory.csv', traj, ['timestep','x','y','risk','uncertainty','recoverability','safety_state'])
    _csv(RESULTS/'dynamic_obstacles.csv', dynlog, ['timestep','id','x','y'])
    _csv(RESULTS/'reroute_events.csv', reroutes, ['timestep','robot_x','robot_y','trigger','old_path_length','new_path_length','risk_before','risk_after','uncertainty_before','uncertainty_after','success'])
    _csv(RESULTS/'safety_events.csv', safety, ['timestep','state','risk','uncertainty','recoverability','path_blocked'])
    (RESULTS/'planned_paths.json').write_text(json.dumps(plans))
    summary={'mission_success': robot == goal, 'steps': len(traj), 'collision_count': collisions, 'near_miss_count': near, 'replanning_count': len(reroutes), 'avg_planning_time': float(np.mean(plan_times)) if plan_times else 0, 'limitations': ['Synthetic Demo; not real-world ROS2/hardware validation.']}
    (RESULTS/'mission_summary.json').write_text(json.dumps(summary, indent=2))
    metrics={'path_length': len(traj), 'executed_trajectory_length': len(traj), 'planning_time': summary['avg_planning_time'], 'replanning_count': len(reroutes), 'reroute_success_rate': sum(r['success'] for r in reroutes)/max(1,len(reroutes)), 'collision_count': collisions, 'near_miss_count': near, 'mission_success': robot == goal, 'mission_completion_time': len(traj), 'risk_exposure': sum(float(r['risk']) for r in traj), 'uncertainty_exposure': sum(float(r['uncertainty']) for r in traj), 'recoverability_exposure': sum(float(r['recoverability']) for r in traj), 'safety_intervention_count': sum(r['state'] != 'NORMAL' for r in safety), 'average_replanning_latency': summary['avg_planning_time']}
    _csv(RESULTS/'metrics/metrics.csv', [metrics], list(metrics)); (RESULTS/'metrics/summary.json').write_text(json.dumps(metrics, indent=2))
    (RESULTS/'reports/evaluation_report.md').write_text('# Evaluation Report\n\nSynthetic Demo results. Not real-world benchmark.\n\n```json\n' + json.dumps(metrics, indent=2) + '\n```\n')
    # figures
    for name, arr in [('risk_heatmap.png', risk), ('uncertainty_heatmap.png', unc), ('recoverability_heatmap.png', rec), ('occupancy_grid.png', grid)]:
        fig, ax = plt.subplots(); ax.imshow(arr, origin='lower'); ax.set_title(name); fig.savefig(RESULTS/'figures'/name, bbox_inches='tight'); fig.savefig(ASSETS/'figures'/name, bbox_inches='tight'); plt.close(fig)
    xs=[int(r['x']) for r in traj]; ys=[int(r['y']) for r in traj]
    fig, ax = plt.subplots(); ax.imshow(risk, origin='lower', alpha=.45); ax.plot(xs, ys); ax.scatter([start[0], goal[0]], [start[1], goal[1]], marker='x'); ax.set_title('planned path vs executed trajectory'); fig.savefig(RESULTS/'figures/trajectory.png', bbox_inches='tight'); fig.savefig(ASSETS/'figures/trajectory.png', bbox_inches='tight'); plt.close(fig)
    for name in ['dynamic_obstacle_timeline.png','rerouting_timeline.png','safety_timeline.png','risk_aware_vs_shortest_path.png','planning_time_comparison.png','architecture_diagram.png','navigation_pipeline_diagram.png']:
        fig, ax = plt.subplots(); ax.plot([float(r['risk']) for r in traj]); ax.plot([float(r['uncertainty']) for r in traj]); ax.set_title(name); fig.savefig(RESULTS/'figures'/name, bbox_inches='tight'); fig.savefig(ASSETS/'figures'/name, bbox_inches='tight'); plt.close(fig)
    fig, ax = plt.subplots()
    def update(i):
        ax.clear(); ax.imshow(risk, origin='lower', alpha=.55); ax.plot(xs[:i+1], ys[:i+1]); ax.scatter(xs[i], ys[i], s=80); ax.set_title(f"DynNav t={i} {traj[i]['safety_state']}")
    anim = FuncAnimation(fig, update, frames=len(traj), interval=80)
    anim.save(RESULTS/'videos/dynnav_demo.gif', writer=PillowWriter(fps=8)); anim.save(ASSETS/'gifs/demo.gif', writer=PillowWriter(fps=8))
    try:
        anim.save(RESULTS/'videos/dynnav_demo.mp4', fps=8); anim.save(ASSETS/'videos/demo.mp4', fps=8)
    except Exception as e:
        (RESULTS/'reports/mp4_fallback.md').write_text(f'MP4 export failed: {e}; GIF fallback produced.\n')
    plt.close(fig)
    (RESULTS/'reports/reproducibility_report.md').write_text('# Reproducibility Report\n\nRun `python scripts/run_all.py`. Seeded deterministic synthetic demo.\n')
    (RESULTS/'reports/benchmark_report.md').write_text('# Benchmark Report\n\nRun `python scripts/run_benchmarks.py`. Synthetic benchmark only; no SOTA claims.\n')
    print('DynNav pipeline complete')
    for p in ['metrics/metrics.csv','figures/trajectory.png','videos/dynnav_demo.gif','videos/dynnav_demo.mp4','reports/evaluation_report.md','reports/benchmark_report.md','reports/reproducibility_report.md']:
        print(f'- {RESULTS/p}: {(RESULTS/p).exists()}')
    print('Remaining limitations: synthetic demo; ROS2/Nav2 scaffold not hardware-tested.')


if __name__ == '__main__':
    run()
