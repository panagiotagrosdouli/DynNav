"use client";

import { useMemo, useState } from "react";

type Mode = "obstacle" | "start" | "goal";
type Cell = number;

const size = 12;
const totalCells = size * size;
const defaultStart = 0;
const defaultGoal = totalCells - 1;
const defaultObstacles = new Set<Cell>([15,16,17,18,30,42,54,66,67,68,69,81,93,94,95,107,119,120,121,50,51,52,64,76,88]);

function row(cell: Cell) { return Math.floor(cell / size); }
function col(cell: Cell) { return cell % size; }
function heuristic(a: Cell, b: Cell) { return Math.abs(row(a) - row(b)) + Math.abs(col(a) - col(b)); }
function neighbors(cell: Cell) {
  const r = row(cell), c = col(cell);
  const n: Cell[] = [];
  if (r > 0) n.push(cell - size);
  if (r < size - 1) n.push(cell + size);
  if (c > 0) n.push(cell - 1);
  if (c < size - 1) n.push(cell + 1);
  return n;
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
  const gScore = new Map<Cell, number>([[start, 0]]);
  const fScore = new Map<Cell, number>([[start, heuristic(start, goal)]]);
  const visited: Cell[] = [];
  while (open.size > 0) {
    const current = [...open].reduce((best, cell) => (fScore.get(cell) ?? Infinity) < (fScore.get(best) ?? Infinity) ? cell : best);
    visited.push(current);
    if (current === goal) return { path: reconstruct(cameFrom, current), visited, runtime: performance.now() - startedAt, success: true };
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
  const [log, setLog] = useState<string[]>(["System initialized", "Environment loaded", "A* planner ready"]);

  const result = useMemo(() => astar(start, goal, obstacles), [start, goal, obstacles]);
  const pathSet = new Set(result.path);
  const visitedSet = new Set(result.visited);

  function addLog(text: string) { setLog((v) => [text, ...v].slice(0, 5)); }
  function handleCellClick(cell: Cell) {
    if (mode === "start") { if (cell !== goal && !obstacles.has(cell)) { setStart(cell); addLog(`Start moved to cell ${cell}`); } return; }
    if (mode === "goal") { if (cell !== start && !obstacles.has(cell)) { setGoal(cell); addLog(`Goal moved to cell ${cell}`); } return; }
    if (cell === start || cell === goal) return;
    const next = new Set(obstacles);
    next.has(cell) ? next.delete(cell) : next.add(cell);
    setObstacles(next);
    if (pathSet.has(cell)) { setReplans((v) => v + 1); addLog("Dynamic obstacle detected: rerouting triggered"); }
    else addLog("Map updated");
  }
  function reset() { setStart(defaultStart); setGoal(defaultGoal); setObstacles(defaultObstacles); setReplans(0); setLog(["Scenario reset", "A* planner ready"]); }
  function injectDynamicObstacle() {
    const candidate = result.path.find((cell) => cell !== start && cell !== goal);
    if (!candidate) return addLog("No path cell available for obstacle injection");
    const next = new Set(obstacles); next.add(candidate); setObstacles(next); setReplans((v) => v + 1); addLog(`Obstacle injected at cell ${candidate}`);
  }

  return (
    <main style={{ minHeight: "100vh", background: "#f8fafc", color: "#0f172a", fontFamily: "Arial, sans-serif" }}>
      <div style={{ display: "grid", gridTemplateColumns: "310px 1fr", minHeight: "100vh" }}>
        <aside style={{ background: "white", borderRight: "1px solid #e2e8f0", padding: "2rem", position: "sticky", top: 0, height: "100vh" }}>
          <h2 style={{ margin: 0 }}>DynNav Dashboard</h2>
          <p style={{ color: "#64748b", lineHeight: 1.6 }}>Dynamic Navigation & Re-routing in Unknown Environments</p>
          <div style={{ display: "grid", gap: "0.75rem", marginTop: "1.5rem" }}>
            <button onClick={() => setMode("obstacle")} style={sideButton(mode === "obstacle")}>Obstacle Editor</button>
            <button onClick={() => setMode("start")} style={sideButton(mode === "start")}>Set Start Node</button>
            <button onClick={() => setMode("goal")} style={sideButton(mode === "goal")}>Set Goal Node</button>
            <button onClick={injectDynamicObstacle} style={sideButton(false)}>Run Dynamic Reroute</button>
            <button onClick={reset} style={sideButton(false)}>Reset Scenario</button>
          </div>
          <div style={{ marginTop: "2rem", padding: "1rem", background: "#f1f5f9", borderRadius: 12 }}>
            <strong>Legend</strong>
            <Legend color="#16a34a" text="Start" />
            <Legend color="#dc2626" text="Goal" />
            <Legend color="#2563eb" text="Planned path" />
            <Legend color="#020617" text="Obstacle" />
            <Legend color="#cbd5e1" text="Visited node" />
          </div>
          <a href="/" style={{ display: "block", marginTop: "2rem", color: "#2563eb", textDecoration: "none" }}>← Back to Home</a>
        </aside>

        <section style={{ padding: "2rem 3rem" }}>
          <h1 style={{ fontSize: "2.4rem", marginBottom: "0.3rem" }}>Live Simulation</h1>
          <p style={{ color: "#64748b", maxWidth: 980 }}>Streamlit-style Vercel dashboard for DynNav: A* search, grid environment, obstacle detection, automatic rerouting and performance metrics.</p>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(150px, 1fr))", gap: "1rem", marginTop: "1.5rem" }}>
            <Card label="Status" value={result.success ? "Path Found" : "No Path"} />
            <Card label="Path Length" value={String(result.path.length)} />
            <Card label="Visited Nodes" value={String(result.visited.length)} />
            <Card label="Runtime" value={`${result.runtime.toFixed(2)} ms`} />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 360px", gap: "1.5rem", marginTop: "1.5rem" }}>
            <div style={{ background: "white", padding: "1.5rem", borderRadius: 18, border: "1px solid #e2e8f0", boxShadow: "0 8px 22px rgba(15,23,42,0.06)" }}>
              <h2 style={{ marginTop: 0 }}>Environment Map</h2>
              <div style={{ display: "grid", gridTemplateColumns: `repeat(${size}, 36px)`, gap: 5, overflowX: "auto" }}>
                {Array.from({ length: totalCells }, (_, cell) => {
                  const isStart = cell === start, isGoal = cell === goal, isObstacle = obstacles.has(cell), isPath = pathSet.has(cell), isVisited = visitedSet.has(cell);
                  return <button key={cell} onClick={() => handleCellClick(cell)} style={{ width: 36, height: 36, borderRadius: 7, border: "1px solid #cbd5e1", color: "white", fontWeight: 700, cursor: "pointer", background: isStart ? "#16a34a" : isGoal ? "#dc2626" : isObstacle ? "#020617" : isPath ? "#2563eb" : isVisited ? "#cbd5e1" : "#f8fafc" }}>{isStart ? "S" : isGoal ? "G" : isPath && !isObstacle ? "•" : ""}</button>;
                })}
              </div>
            </div>

            <div style={{ display: "grid", gap: "1rem" }}>
              <Panel title="Planner Configuration">
                <Metric label="Algorithm" value="A* Search" />
                <Metric label="Grid Size" value={`${size} × ${size}`} />
                <Metric label="Obstacles" value={String(obstacles.size)} />
                <Metric label="Replans" value={String(replans)} />
              </Panel>
              <Panel title="Event Log">
                {log.map((item, i) => <p key={i} style={{ margin: "0.5rem 0", color: "#475569" }}>• {item}</p>)}
              </Panel>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

function Card({ label, value }: { label: string; value: string }) { return <div style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 16, padding: "1rem", boxShadow: "0 8px 22px rgba(15,23,42,0.06)" }}><p style={{ color: "#64748b", margin: 0 }}>{label}</p><h3 style={{ margin: "0.5rem 0 0", fontSize: "1.6rem" }}>{value}</h3></div>; }
function Panel({ title, children }: { title: string; children: React.ReactNode }) { return <div style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 16, padding: "1rem" }}><h3 style={{ marginTop: 0 }}>{title}</h3>{children}</div>; }
function Metric({ label, value }: { label: string; value: string }) { return <div style={{ display: "flex", justifyContent: "space-between", padding: "0.5rem 0", borderBottom: "1px solid #e2e8f0" }}><span style={{ color: "#64748b" }}>{label}</span><strong>{value}</strong></div>; }
function Legend({ color, text }: { color: string; text: string }) { return <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 10 }}><span style={{ width: 14, height: 14, borderRadius: 4, background: color, display: "inline-block" }} /> <span>{text}</span></div>; }
function sideButton(active: boolean): React.CSSProperties { return { padding: "0.8rem 1rem", borderRadius: 10, border: "1px solid #cbd5e1", background: active ? "#2563eb" : "#f8fafc", color: active ? "white" : "#0f172a", cursor: "pointer", fontWeight: 700, textAlign: "left" }; }
