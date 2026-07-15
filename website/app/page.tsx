const capabilities = [
  "Grid-based A* and Dijkstra baselines",
  "Occupancy-risk-aware planning",
  "Uncertainty and recoverability reasoning",
  "Dynamic rerouting and runtime monitoring",
];

export default function Home() {
  return (
    <main>
      <section className="hero">
        <p className="eyebrow">DynNav research prototype</p>
        <h1>Risk-aware dynamic navigation in unknown environments</h1>
        <p className="lede">
          A reproducible robotics research codebase for studying how occupancy risk,
          uncertainty, recoverability, and runtime supervision affect online replanning.
        </p>
        <a
          className="button"
          href="https://github.com/panagiotagrosdouli/DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments"
        >
          View repository
        </a>
      </section>

      <section aria-labelledby="status-heading">
        <h2 id="status-heading">Current verified scope</h2>
        <ul>
          {capabilities.map((capability) => (
            <li key={capability}>{capability}</li>
          ))}
        </ul>
        <p className="note">
          Current evidence is synthetic and test-based. ROS 2, Nav2, Gazebo, and hardware
          validation are not claimed by this page.
        </p>
      </section>
    </main>
  );
}
