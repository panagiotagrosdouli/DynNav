export default function HomePage() {
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
      <h1
        style={{
          fontSize: "3rem",
          fontWeight: "bold",
          marginBottom: "1rem"
        }}
      >
        DynNav
      </h1>

      <h2
        style={{
          fontSize: "1.5rem",
          marginBottom: "2rem",
          color: "#cbd5e1"
        }}
      >
        Dynamic Navigation & Re-routing in Unknown Environments
      </h2>

      <p
        style={{
          maxWidth: "800px",
          lineHeight: "1.8",
          fontSize: "1.1rem"
        }}
      >
        DynNav is an intelligent path-planning and navigation framework
        designed for dynamic and unknown environments. The system combines
        graph-based planning, obstacle detection and real-time route
        reconfiguration to improve autonomous navigation performance.
      </p>

      <div
        style={{
          marginTop: "3rem",
          display: "flex",
          gap: "1rem"
        }}
      >
        <a
          href="https://github.com/panagiotagrosdouli/DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments"
          target="_blank"
          style={{
            padding: "12px 24px",
            background: "#2563eb",
            color: "white",
            textDecoration: "none",
            borderRadius: "8px"
          }}
        >
          GitHub Repository
        </a>

        <a
          href="/simulation"
          style={{
            padding: "12px 24px",
            background: "#16a34a",
            color: "white",
            textDecoration: "none",
            borderRadius: "8px"
          }}
        >
          Live Demo
        </a>
      </div>
    </main>
  );
}
