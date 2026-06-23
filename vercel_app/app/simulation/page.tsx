export default function SimulationPage() {
  const grid = Array.from({ length: 49 }, (_, index) => {
    const obstacles = [9, 10, 17, 24, 25, 32, 39];
    const path = [0, 1, 2, 3, 4, 11, 18, 19, 20, 27, 34, 41, 48];
    const isStart = index === 0;
    const isGoal = index === 48;
    const isObstacle = obstacles.includes(index);
    const isPath = path.includes(index);

    return { index, isStart, isGoal, isObstacle, isPath };
  });

  return (
    <main
      style={{
        minHeight: "100vh",
        padding: "4rem",
        fontFamily: "Arial, sans-serif",
        background: "#0f172a",
        color: "white"
      }}
    >
      <a href="/" style={{ color: "#93c5fd", textDecoration: "none" }}>
        ← Back to Home
      </a>

      <h1 style={{ fontSize: "2.8rem", marginTop: "2rem", marginBottom: "1rem" }}>
        DynNav Live Demo
      </h1>

      <p style={{ maxWidth: "850px", lineHeight: "1.8", color: "#cbd5e1", fontSize: "1.1rem" }}>
        This browser-based demo illustrates dynamic navigation and re-routing in an unknown grid environment.
        The green cell is the start, the red cell is the goal, dark cells are obstacles, and blue cells show
        the computed navigation path.
      </p>

      <section
        style={{
          marginTop: "3rem",
          display: "grid",
          gridTemplateColumns: "repeat(7, 54px)",
          gap: "8px"
        }}
      >
        {grid.map((cell) => (
          <div
            key={cell.index}
            title={`Cell ${cell.index}`}
            style={{
              width: "54px",
              height: "54px",
              borderRadius: "10px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 700,
              background: cell.isStart
                ? "#16a34a"
                : cell.isGoal
                  ? "#dc2626"
                  : cell.isObstacle
                    ? "#020617"
                    : cell.isPath
                      ? "#2563eb"
                      : "#334155",
              border: "1px solid #475569"
            }}
          >
            {cell.isStart ? "S" : cell.isGoal ? "G" : cell.isObstacle ? "" : cell.isPath ? "•" : ""}
          </div>
        ))}
      </section>

      <section style={{ marginTop: "3rem", display: "flex", gap: "1rem", flexWrap: "wrap" }}>
        <div style={{ padding: "1rem", background: "#1e293b", borderRadius: "12px" }}>
          Path Length: 13 cells
        </div>
        <div style={{ padding: "1rem", background: "#1e293b", borderRadius: "12px" }}>
          Re-routing Events: 2
        </div>
        <div style={{ padding: "1rem", background: "#1e293b", borderRadius: "12px" }}>
          Status: Path Found
        </div>
      </section>
    </main>
  );
}
