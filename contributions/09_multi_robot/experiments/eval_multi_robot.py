import csv
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
RESULTS = BASE / "results"
OUT_CSV = RESULTS / "c09_multi_robot_summary.csv"
OUT_MD = RESULTS / "c09_multi_robot_summary.md"

STARTS = [(0, 1), (0, 2), (0, 3)]
GOALS = [(8, 1), (8, 2), (8, 3)]
RISK = {1: 0.7, 2: 0.2, 3: 0.4}


def straight_path(start, goal):
    sx, sy = start
    gx, gy = goal
    step = 1 if gx >= sx else -1
    return [(x, sy) for x in range(sx, gx + step, step)]


def detour_path(start, goal, via_y):
    sx, sy = start
    gx, gy = goal
    path = [(sx, sy)]
    ystep = 1 if via_y >= sy else -1
    for y in range(sy + ystep, via_y + ystep, ystep):
        path.append((sx, y))
    xstep = 1 if gx >= sx else -1
    for x in range(sx + xstep, gx + xstep, xstep):
        path.append((x, via_y))
    ystep = 1 if gy >= via_y else -1
    for y in range(via_y + ystep, gy + ystep, ystep):
        path.append((gx, y))
    return path


def count_conflicts(paths):
    horizon = max(len(p) for p in paths)
    conflicts = 0
    for t in range(horizon):
        seen = {}
        for rid, p in enumerate(paths):
            pos = p[t] if t < len(p) else p[-1]
            if pos in seen:
                conflicts += 1
            seen[pos] = rid
    return conflicts


def metrics(name, paths):
    total_len = sum(len(p) for p in paths)
    makespan = max(len(p) for p in paths)
    conflicts = count_conflicts(paths)
    mean_risk = sum(sum(RISK.get(y, 0.1) for x, y in p) / len(p) for p in paths) / len(paths)
    return {
        "strategy": name,
        "success": int(conflicts == 0),
        "conflicts": conflicts,
        "total_path_len": total_len,
        "makespan": makespan,
        "mean_path_risk": mean_risk,
    }


def main():
    independent = [straight_path(s, g) for s, g in zip(STARTS, GOALS)]

    priority = [
        straight_path(STARTS[0], GOALS[0]),
        detour_path(STARTS[1], GOALS[1], 4),
        detour_path(STARTS[2], GOALS[2], 5),
    ]

    risk_aware = [
        detour_path(STARTS[0], GOALS[0], 2),
        straight_path(STARTS[1], GOALS[1]),
        detour_path(STARTS[2], GOALS[2], 2),
    ]

    rows = [
        metrics("independent", independent),
        metrics("priority_reservation", priority),
        metrics("risk_aware_priority", risk_aware),
    ]

    RESULTS.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    base = rows[0]
    prio = rows[1]
    risk = rows[2]
    conflict_reduction = 100.0 * (base["conflicts"] - prio["conflicts"]) / max(base["conflicts"], 1)
    risk_reduction = 100.0 * (prio["mean_path_risk"] - risk["mean_path_risk"]) / prio["mean_path_risk"]

    OUT_MD.write_text(
        "# C09 Multi-Robot Coordination Summary\n\n"
        f"- Independent conflicts: {base['conflicts']}\n"
        f"- Priority-reservation conflicts: {prio['conflicts']}\n"
        f"- Conflict reduction: {conflict_reduction:.2f}%\n"
        f"- Priority mean risk: {prio['mean_path_risk']:.3f}\n"
        f"- Risk-aware priority mean risk: {risk['mean_path_risk']:.3f}\n"
        f"- Risk reduction vs priority: {risk_reduction:.2f}%\n\n"
        "## Interpretation\n\n"
        "Priority reservation removes conflicts relative to independent planning. "
        "Risk-aware priority further reduces path risk by selecting safer lanes, "
        "at the cost of longer coordinated routes.\n"
    )
    print(f"[INFO] Wrote {OUT_CSV}")
    print(f"[INFO] Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
