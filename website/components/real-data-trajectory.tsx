const basePath = process.env.DYNNAV_SITE_BASE_PATH ?? "";

const metrics = [
  ["3,194", "ground-truth poses · LILocBench dynamics_0"],
  ["53.97 m", "recorded XY path length · ground truth"],
  ["11.20 m", "static 4-neighbour A* route · 225 cells"],
  ["30,577", "ROS1 bag messages decoded offline"],
] as const;

export function RealDataTrajectory() {
  return (
    <section className="real-data" id="real-data">
      <div className="section-heading">
        <p className="eyebrow"><span /> Recorded robotics data</p>
        <h2>Map ingestion and recorded motion, with evidence boundaries.</h2>
        <p>
          LILocBench Clearpath Dingo sequence <code>dynamics_0</code>. The pink line is
          recorded ground truth; cyan is DynNav four-neighbour A* on the official static
          occupancy map between the first and last ground-truth poses. This is not a
          dynamic-planner or robot-control trial.
        </p>
      </div>
      <div className="real-data-layout">
        <div className="real-data-visuals">
          <figure className="trajectory-figure">
            <img
              src={`${basePath}/lilocbench-dynamics-0-verified-overlay.svg`}
              alt="Official LILocBench occupancy map with pink recorded ground-truth trajectory and cyan DynNav static A-star path"
              width="1200"
              height="1360"
            />
            <figcaption>
              Dataset: LILocBench <code>dynamics_0</code>. Metric: 53.97 m recorded path;
              11.20 m static A* route. Evidence: source-documented global frame plus
              3,194 of 3,194 poses in known-free cells. Source hashes, attribution and
              evidence status are embedded in the SVG and retained in the provenance artifact.
            </figcaption>
          </figure>
        </div>
        <div className="real-data-side">
          <div className="real-metrics">
            {metrics.map(([value, label]) => (
              <div className="real-metric" key={label}>
                <strong>{value}</strong>
                <span>{label}</span>
              </div>
            ))}
          </div>
          <p className="real-method">
            Static A*: 6,891 expanded nodes, 0.05 m map resolution, unknown cells blocked.
            Ground-truth mean speed: 0.337 m/s. Bag: 17 connections across seven
            topic names; front/rear scan skew median 7.09 ms (p95 7.98 ms).
          </p>
          <p className="real-boundary">
            The ROS1 TF tree has <code>odom</code> as its root and no <code>map → odom</code>
            transform. The diagnostic odometry fit is not used as a map transform. The bag
            was decoded and audited offline; no live ROS/Nav2 replay, dynamic counterfactual,
            closed-loop control, or physical-robot run is claimed.
          </p>
          <div className="real-links">
            <a href="https://github.com/panagiotagrosdouli/DynNav/blob/real-data-validation/docs/LILOCBENCH_REAL_DATA_REPORT.md">Full methods and limitations ↗</a>
            <a href={`${basePath}/results/real_data/lilocbench_map_and_trajectory_provenance.json`}>Map, trajectory, and A* provenance JSON ↗</a>
            <a href={`${basePath}/results/real_data/lilocbench_dynamics_0_static_astar_config.json`}>Static A* run configuration ↗</a>
            <a href={`${basePath}/results/real_data/lilocbench_dynamics_0_ros1_bag_audit.json`}>ROS1 bag audit JSON ↗</a>
            <a href={`${basePath}/results/real_data/LICENSE.md`}>Dataset-derived artifact attribution ↗</a>
            <a href="https://www.ipb.uni-bonn.de/html/projects/localization_benchmark/">Official dataset and license ↗</a>
          </div>
          <p className="real-license">
            Dataset: CC BY-NC-SA 4.0 · Trekel et al., IROS 2025. Derived artifacts carry
            attribution and license details in <code>results/real_data/LICENSE.md</code>.
          </p>
        </div>
      </div>
    </section>
  );
}
