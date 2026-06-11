import csv
import heapq
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
RESULTS = BASE / "results"
OUT_CSV = RESULTS / "c06_energy_connectivity_summary.csv"
OUT_MD = RESULTS / "c06_energy_connectivity_summary.md"


def make_world():
    """
    Synthetic benchmark with two feasible corridors:

    1. Short central corridor with poor connectivity.
    2. Longer outer corridor with good connectivity.

    This lets the connectivity-aware planner trade extra distance/energy
    for improved communication quality.
    """
    grid = [[1 for _ in range(12)] for _ in range(8)]

    # Short low-connectivity corridor: y=3
    for x in range(12):
        grid[3][x] = 0

    # Longer high-connectivity outer route: down, across, up
    for y in range(0, 8):
        grid[y][0] = 0
        grid[y][11] = 0
    for x in range(12):
        grid[7][x] = 0

    start = (0, 3)
    goal = (11, 3)

    link = [[0.9 for _ in range(12)] for _ in range(8)]

    # Central shortcut has poor connectivity.
    for x in range(3, 9):
        link[3][x] = 0.2

    # Outer corridor remains high connectivity.
    return grid, link, start, goal


def plan(grid, link, start, goal, budget, use_link_penalty):
    h, w = len(grid), len(grid[0])
    pq = [(0, 0, start)]
    parent = {start: None}
    cost = {start: 0.0}
    energy = {start: 0.0}
    min_link = {start: link[start[1]][start[0]]}

    def free(x, y):
        return 0 <= x < w and 0 <= y < h and grid[y][x] == 0

    def manhattan(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    expansions = 0

    while pq:
        _, g, cur = heapq.heappop(pq)
        expansions += 1

        if cur == goal:
            path = []
            node = cur
            while node is not None:
                path.append(node)
                node = parent[node]
            path.reverse()
            return True, path, cost[cur], energy[cur], min_link[cur], expansions

        x, y = cur
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = x + dx, y + dy
            if not free(nx, ny):
                continue

            new_energy = energy[cur] + 1.0
            if new_energy > budget:
                continue

            step_cost = 1.0

            if use_link_penalty:
                # Communication-aware objective:
                # high connectivity -> small penalty
                # low connectivity  -> large penalty
                connectivity_cost = 10.0 * (1.0 - link[ny][nx])
            else:
                connectivity_cost = 0.0

            new_cost = g + step_cost + connectivity_cost
            nxt = (nx, ny)

            if nxt not in cost or new_cost < cost[nxt]:
                cost[nxt] = new_cost
                energy[nxt] = new_energy
                min_link[nxt] = min(min_link[cur], link[ny][nx])
                parent[nxt] = cur
                heapq.heappush(pq, (new_cost + manhattan(nxt, goal), new_cost, nxt))

    return False, [], float("inf"), float("inf"), 0.0, expansions


def main():
    grid, link, start, goal = make_world()

    configs = [
        ("baseline", 30, False),
        ("energy_limited", 14, False),
        ("energy_connectivity", 30, True),
    ]

    rows = []
    for name, budget, use_link in configs:
        ok, path, cost, used, minq, exp = plan(grid, link, start, goal, budget, use_link)
        rows.append({
            "planner": name,
            "success": int(ok),
            "path_len": len(path),
            "cost": cost,
            "energy_used": used,
            "budget": budget,
            "energy_margin": budget - used if ok else "",
            "min_connectivity": minq,
            "expansions": exp,
        })

    RESULTS.mkdir(parents=True, exist_ok=True)

    with OUT_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    base = rows[0]
    limited = rows[1]
    conn = rows[2]

    OUT_MD.write_text(
        "# C06 Energy and Connectivity Summary\n\n"
        f"- Baseline success: {base['success']}\n"
        f"- Energy-limited success: {limited['success']}\n"
        f"- Connectivity-aware success: {conn['success']}\n"
        f"- Baseline min connectivity: {float(base['min_connectivity']):.3f}\n"
        f"- Connectivity-aware min connectivity: {float(conn['min_connectivity']):.3f}\n"
        f"- Baseline energy used: {float(base['energy_used']):.3f}\n"
        f"- Connectivity-aware energy used: {float(conn['energy_used']):.3f}\n\n"
        "## Interpretation\n\n"
        "The energy-limited setting rejects plans that exceed the available budget. "
        "The connectivity-aware setting penalizes low-link regions and exposes the trade-off "
        "between resource feasibility and communication-aware routing.\n"
    )

    print(f"[INFO] Wrote {OUT_CSV}")
    print(f"[INFO] Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
