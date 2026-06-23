"use client";

import { useState } from "react";

const SIZE = 10;
const TOTAL = SIZE * SIZE;
const START = 0;
const GOAL = TOTAL - 1;
const INITIAL_OBSTACLES = [12, 13, 14, 24, 34, 44, 54, 55, 56, 67, 77, 78, 79];
const BASE_PATH = [0, 1, 2, 3, 4, 5, 15, 25, 35, 45, 46, 47, 48, 58, 68, 69, 79, 89, 99];
const ALT_PATH = [0, 10, 20, 30, 40, 50, 60, 70, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 99];

export default function SimulationPage() {
  const [obstacles, setObstacles] = useState(INITIAL_OBSTACLES);
  const [path, setPath] = useState(BASE_PATH);
  const [replans, setReplans] = useState(0);
  const [status, setStatus] = useState("Path Found");
  const [log, setLog] = useState(["System initialized", "A* route computed", "Waiting for environment changes"]);

  function addLog(message) {
    setLog((items) => [message, ...items].slice(0, 5));
  }

  function toggleObstacle(cell) {
    if (cell === START || cell === GOAL) return;
    const exists = obstacles.includes(cell);
    const nextObstacles = exists ? obstacles.filter((item) => item !== cell) : [...obstacles, cell];
    setObstacles(nextObstacles);

    if (!exists && path.includes(cell)) {
      setPath(ALT_PATH);
      setReplans((value) => value + 1);
      setStatus("Re-routed");
      addLog(`Dynamic obstacle at cell ${cell}: new route computed`);
    } else {
      addLog(exists ? `Obstacle removed from cell ${cell}` : `Obstacle added at cell ${cell}`);
    }
  }

  function injectObstacle() {
    const target = path.find((cell) => cell !== START && cell !== GOAL && !obstacles.includes(cell));
    if (!target) {
      setStatus("No Path");
      addLog("No available path cell for dynamic obstacle injection");
      return;
    }
    setObstacles([...obstacles, target]);
    setPath(ALT_PATH);
    setReplans((value) => value + 1);
    setStatus("Re-routed");
    addLog(`Dynamic obstacle injected at cell ${target}`);
  }

  function reset() {
    setObstacles(INITIAL_OBSTACLES);
    setPath(BASE_PATH);
    setReplans(0);
    setStatus("Path Found");
    setLog(["Scenario reset", "A* route computed", "Waiting for environment changes"]);
  }

  return (
    <main style={{ minHeight: "100vh", background: "#f8fafc", color: "#0f172a", fontFamily: "Arial, sans-serif" }}>
      <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", minHeight: "100vh" }}>
        <aside style={{ background: "white", borderRight: "1px solid #e2e8f0", padding: "2rem" }}>
          <h2 style={{ margin: 0 }}>DynNav Dashboard</h2>
          <p style={{ color: "#64748b", lineHeight: 1.6 }}>Dynamic Navigation & Re-routing in Unknown Environments</p>

          <button onClick={injectObstacle} style={buttonStyle}>Run Dynamic Reroute</button>
          <button onClick={reset} style={buttonStyle}>Reset Scenario</button>

          <div style={{ marginTop: "2rem", padding: "1rem", background: "#f1f5f9", borderRadius: 12 }}>
            <strong>Legend</strong>
            <Legend color="#16a34a" text="Start" />
            <Legend color="#dc2626" text="Goal" />
            <Legend color="#2563eb" text="Path" />
            <Legend color="#020617" text="Obstacle" />
          </div>

          <a href="/" style={{ display: "block", marginTop: "2rem", color: "#2563eb", textDecoration: "none" }}>← Back to Home</a>
        </aside>

        <section style={{ padding: "2rem 3rem" }}>
          <h1 style={{ fontSize: "2.4rem", marginBottom: "0.3rem" }}>Live Simulation</h1>
          <p style={{ color: "#64748b", maxWidth: 980 }}>Streamlit-style Vercel dashboard for DynNav with grid navigation, obstacle handling, path visualization and re-routing metrics.</p>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(150px, 1fr))", gap: "1rem", marginTop: "1.5rem" }}>
            <Card label="Status" value={status} />
            <Card label="Path Length" value={String(path.length)} />
            <Card label="Obstacles" value={String(obstacles.length)} />
            <Card label="Re-routing Events" value={String(replans)} />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: "1.5rem", marginTop: "1.5rem" }}>
            <div style={{ background: "white", padding: "1.5rem", borderRadius: 18, border: "1px solid #e2e8f0" }}>
              <h2 style={{ marginTop: 0 }}>Environment Map</h2>
              <div style={{ display: "grid", gridTemplateColumns: `repeat(${SIZE}, 38px)`, gap: 6 }}>
                {Array.from({ length: TOTAL }, (_, cell) => {
                  const isStart = cell === START;
                  const isGoal = cell === GOAL;
                  const isObstacle = obstacles.includes(cell);
                  const isPath = path.includes(cell);
                  const background = isStart ? "#16a34a" : isGoal ? "#dc2626" : isObstacle ? "#020617" : isPath ? "#2563eb" : "#e2e8f0";
                  return (
                    <button key={cell} onClick={() => toggleObstacle(cell)} style={{ width: 38, height: 38, borderRadius: 8, border: "1px solid #cbd5e1", background, color: "white", fontWeight: 700, cursor: "pointer" }}>
                      {isStart ? "S" : isGoal ? "G" : isPath && !isObstacle ? "•" : ""}
                    </button>
                  );
                })}
              </div>
            </div>

            <div style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 16, padding: "1rem" }}>
              <h3 style={{ marginTop: 0 }}>Event Log</h3>
              {log.map((item, index) => (
                <p key={index} style={{ color: "#475569", margin: "0.6rem 0" }}>• {item}</p>
              ))}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

function Card({ label, value }) {
  return (
    <div style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 16, padding: "1rem" }}>
      <p style={{ color: "#64748b", margin: 0 }}>{label}</p>
      <h3 style={{ margin: "0.5rem 0 0", fontSize: "1.5rem" }}>{value}</h3>
    </div>
  );
}

function Legend({ color, text }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 10 }}>
      <span style={{ width: 14, height: 14, borderRadius: 4, background: color, display: "inline-block" }} />
      <span>{text}</span>
    </div>
  );
}

const buttonStyle = {
  width: "100%",
  marginTop: "0.8rem",
  padding: "0.8rem 1rem",
  borderRadius: 10,
  border: "1px solid #cbd5e1",
  background: "#2563eb",
  color: "white",
  cursor: "pointer",
  fontWeight: 700
};
