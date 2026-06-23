"use client";

import { useMemo, useState } from "react";

type Mode = "obstacle" | "start" | "goal";
type Cell = number;

const size = 12;
const totalCells = size * size;
const defaultStart = 0;
const defaultGoal = totalCells - 1;
const defaultObstacles = new Set<Cell>([
  15, 16, 17, 18, 30, 42, 54, 66, 67, 68, 69, 81, 93, 94, 95, 107, 119, 120,
  121, 50, 51, 52, 64, 76, 88
]);

function row(cell: Cell) {
  return Math.floor(cell / size);
}

function col(cell: Cell) {
  return cell % size;
}

function heuristic(a: Cell, b: Cell) {
  return Math.abs(row(a) - row(b)) + Math.abs(col(a) - col(b));
}

function neighbors(cell: Cell) {
  const r = row(cell);
  const c = col(cell);
  const result: Cell[] = [];
  if (r > 0) result.push(cell - size);
  if (r < size - 1) result.push(cell + size);
  if (c > 0) result.push(cell - 1);
  if (c < size - 1) result.push(cell + 1);
  return result;
}

function reconstruct(cameFrom: Map<Cell, Cell>, current: Cell) {
  const path = [current];
  while (cameFrom.has(current)) {
    current = cameFrom.get(current)!;
    path.unshift(current);
  }
  return path;
}

function astar(start: Cell, goal: Cell, obstacles: Set<Cell>) {
  const startedAt = performance.now();
  const open = new Set<Cell>([start]);
  const cameFrom = new Map<Cell, Cell>();
  const gScore = new Map<Cell, number>();
  const fScore = new Map<Cell, number>();
  const visited: Cell[] = [];

  gScore.set(start, 0);
  fScore.set(start, heuristic(start, goal));

  while (open.size > 0) {
    let current = [...open].reduce((best, cell) =>
      (fScore.get(cell) ?? Infinity) < (fScore.get(best) ?? Infinity) ? cell : best
    );

    visited.push(current);

    if (current === goal) {
      return {
        path: reconstruct(cameFrom, current),
        visited,
        runtime: performance.now() - startedAt,
        success: true
      };
    }

    open.delete(current);

    for (const next of neighbors(current)) {
      if (obstacles.has(next)) continue;
      const tentative = (gScore.get(current) ?? Infinity) + 1;
      if (tentative < (gScore.get(next) ?? Infinity)) {
        cameFrom.set(next, current);
        gScore.set(next, tentative);
        fScore.set(next, tentative + heuristic(next, goal));
        open.add(next);
      }
    }
  }

  return { path: [], visited, runtime: performance.now() - startedAt, success: false };
}

export default function SimulationPage() {
  const [start, setStart] = useState(defaultStart);
  const [goal, setGoal] = useState(defaultGoal);
  const [obstacles, setObstacles] = useState<Set<Cell>>(defaultObstacles);
  const [mode, setMode] = useState<Mode>("obstacle");
  const [replans, setReplans] = useState(0);
  const [message, setMessage] = useState("Ready: run A* to compute the first route.");

  const result = useMemo(() => astar(start, goal, obstacles), [start, goal, obstacles]);
  const pathSet = new Set(result.path);
  const visitedSet = new Set(result.visited);

  function handleCellClick(cell: Cell) {
    if (mode === "start") {
      if (cell !== goal && !obstacles.has(cell)) setStart(cell);
      return;
    }
    if (mode === "goal") {
      if (cell !== start && !obstacles.has(cell)) setGoal(cell);
      return;
    }

    if (cell === start || cell === goal) return;
    const next = new Set(obstacles);
    if (next.has(cell)) next.delete(cell);
    else next.add(cell);
    setObstacles(next);
    if (pathSet.has(cell)) {
      setReplans((value) => value + 1);
      setMessage("Dynamic obstacle detected on active path: route recomputed automatically.");
    } else {
      setMessage("Environment map updated: obstacles changed.");
    }
  }

  function reset() {
    setStart(defaultStart);
    setGoal(defaultGoal);
    setObstacles(defaultObstacles);
    setReplans(0);
    setMessage("Environment reset to the default DynNav scenario.");
  }

  function injectDynamicObstacle() {
    const candidate = result.path.find((cell) => cell !== start && cell !== goal);
    if (!candidate) {
      setMessage("No valid path cell is available for dynamic obstacle injection.");
      return;
    }
    const next = new Set(obstacles);
    next.add(candidate);
    setObstacles(next);
    setReplans((value) => value + 1);
    setMessage("Dynamic obstacle injected on the computed path: DynNav re-routed.");
  }

  return (
    <main style={{ minHeight: "100vh", padding: "3rem", background: "#0f172a", color: "white", fontFamily: "Arial, sans-serif" }}>
      <a href="/" style={{ color: "#93c5fd", textDecoration: "none" }}>← Back to Home</a>
      <h1 style={{ fontSize: "2.8rem", marginTop: "1.5rem" }}>DynNav Interactive Simulation</h1>
      <p style={{ maxWidth: 980, color: "#cbd5e1", lineHeight: 1.8 }}>
        This Vercel demo recreates the core behaviour of the DynNav project in the browser: grid mapping,
        obstacle handling, A* path planning, dynamic obstacle injection, and automatic re-routing metrics.
      </p>

      <section style={{ display: "flex", gap: "1rem", flexWrap: "wrap", marginTop: "2rem" }}>
        <button onClick={() => setMode("obstacle")} style={button(mode === "obstacle")}>Edit Obstacles</button>
        <button onClick={() => setMode("start")} style={button(mode === "start")}>Set Start</button>
        <button onClick={() => setMode("goal")} style={button(mode === "goal")}>Set Goal</button>
        <button onClick={injectDynamicObstacle} style={button(false)}>Inject Dynamic Obstacle</button>
        <button onClick={reset} style={button(false)}>Reset</button>
      </section>

      <section style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: "2rem", alignItems: "start", marginTop: "2rem" }}>
        <div style={{ display: "grid", gridTemplateColumns: `repeat(${size}, 36px)`, gap: "5px", overflowX: "auto" }}>
          {Array.from({ length: totalCells }, (_, cell) => {
            const isStart = cell === start;
            const isGoal = cell === goal;
            const isObstacle = obstacles.has(cell);
            const isPath = pathSet.has(cell);
            const isVisited = visitedSet.has(cell);
            return (
              <button
                key={cell}
                onClick={() => handleCellClick(cell)}
                title={`cell ${cell}`}
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: 8,
                  border: "1px solid #475569",
                  color: "white",
                  fontWeight: 700,
                  cursor: "pointer",
                  background: isStart ? "#16a34a" : isGoal ? "#dc2626" : isObstacle ? "#020617" : isPath ? "#2563eb" : isVisited ? "#475569" : "#1e293b"
                }}
              >
                {isStart ? "S" : isGoal ? "G" : isObstacle ? "" : isPath ? "•" : ""}
              </button>
            );
          })}
        </div>

        <aside style={{ background: "#1e293b", borderRadius: 16, padding: "1.5rem", border: "1px solid #334155" }}>
          <h2 style={{ marginTop: 0 }}>Simulation Metrics</h2>
          <Metric label="Planner" value="A* Search" />
          <Metric label="Status" value={result.success ? "Path Found" : "No Path"} />
          <Metric label="Path Length" value={String(result.path.length)} />
          <Metric label="Visited Nodes" value={String(result.visited.length)} />
          <Metric label="Re-routing Events" value={String(replans)} />
          <Metric label="Runtime" value={`${result.runtime.toFixed(2)} ms`} />
          <p style={{ color: "#cbd5e1", lineHeight: 1.6 }}>{message}</p>
        </aside>
      </section>

      <section style={{ marginTop: "2rem", color: "#cbd5e1", lineHeight: 1.7, maxWidth: 1000 }}>
        <strong style={{ color: "white" }}>How to use:</strong> choose a mode, click cells to change the map,
        then inject a dynamic obstacle. If the new obstacle blocks the active route, the app recomputes a new path.
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", padding: "0.7rem 0", borderBottom: "1px solid #334155" }}>
      <span style={{ color: "#cbd5e1" }}>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function button(active: boolean): React.CSSProperties {
  return {
    padding: "0.8rem 1rem",
    borderRadius: 10,
    border: "1px solid #334155",
    background: active ? "#2563eb" : "#1e293b",
    color: "white",
    cursor: "pointer",
    fontWeight: 700
  };
}
