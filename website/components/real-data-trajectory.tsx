const basePath = process.env.DYNNAV_SITE_BASE_PATH ?? "";

const metrics = [
  ["3,194", "ground-truth poses"],
  ["159.95 s", "recorded sequence"],
  ["53.97 m", "XY path length"],
  ["0.337 m/s", "mean XY speed"],
] as const;

export function RealDataTrajectory() {
  return (
    <section className="real-data" id="real-data">
      <div className="section-heading">
        <p className="eyebrow"><span /> Recorded robot data</p>
        <h2>A real trajectory, with the source and limits visible.</h2>
        <p>
          LILocBench Clearpath Dingo sequence <code>dynamics_0</code>. The plotted
          line is the public ground-truth XY trajectory during a sequence with
          moving people; it is not a DynNav planner trial.
        </p>
      </div>
      <div className="real-data-layout">
        <div className="real-data-visuals">
          <figure className="trajectory-figure">
            <img
              src={`${basePath}/lilocbench-dynamics-0-ground-truth.svg`}
              alt="XY plot of the LILocBench dynamics_0 ground-truth robot trajectory, without an occupancy-map background"
              width="960"
              height="620"
            />
            <figcaption>
              Recorded XY positions in the LILocBench global frame. No occupancy grid or planned route is overlaid.
            </figcaption>
          </figure>
          <figure className="trajectory-figure map-preview">
            <img
              src="https://www.ipb.uni-bonn.de/html/projects/localization_benchmark/static/images/map_office.png"
              alt="Official LILocBench office occupancy-map preview"
              loading="lazy"
            />
            <figcaption>
              Official occupancy-map preview from LILocBench. The pose plot above has not been transformed or overlaid on this map.
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
            Mean sample rate: 19.962 Hz. Median speed: 0.378 m/s; 95th percentile:
            0.440 m/s. Five timestamp gaps exceed the nominal 0.05 s: four are about
            0.10 s and one is about 0.15 s. Path length sums consecutive XY displacements.
          </p>
          <p className="real-boundary">
            These measurements describe one recorded trajectory. They do not measure
            localization error, route success, replanning quality, or causal response
            to a changing obstacle.
          </p>
          <div className="real-links">
            <a href="https://github.com/panagiotagrosdouli/DynNav/blob/main/docs/LILOCBENCH_DYNAMICS_0_ANALYSIS.md">Methods, numbers, and reproduction steps ↗</a>
            <a href="https://www.ipb.uni-bonn.de/html/projects/localization_benchmark/data/gt_poses_public/dynamics_0/gt_poses.txt">Official ground-truth pose file ↗</a>\n            <a href="https://www.ipb.uni-bonn.de/html/projects/localization_benchmark/data/map_office.zip">Official occupancy-map ZIP ↗</a>
          </div>
          <p className="real-license">
            Dataset: CC BY-NC-SA 4.0 · Trekel et al., IROS 2025. See attribution and terms in the analysis notes.
          </p>
        </div>
      </div>
    </section>
  );
}
