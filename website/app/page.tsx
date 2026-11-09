import { ContributionExplorer } from "../components/contribution-explorer";
import { RealDataTrajectory } from "../components/real-data-trajectory";

const evidence = [
  ["C01–C26 smoke suite", "All tracks have registered controlled smoke experiments; this is not a live pass badge.", "registered", "https://github.com/panagiotagrosdouli/DynNav/blob/main/configs/contributions/experiments.yaml"],
  ["Python CI", "Open GitHub Actions for current run results; this static site does not cache a status.", "linked", "https://github.com/panagiotagrosdouli/DynNav/actions/workflows/ci.yml"],
  ["ROS map lab", "The Streamlit app supports ROS YAML + PGM/PNG intake and a static A* baseline.", "available", "https://github.com/panagiotagrosdouli/DynNav/blob/main/app/pages/05_Belief_Mapping_Lab.py"],
  ["LILocBench", "A recorded trajectory has been analyzed; paired DynNav benchmark trials remain open.", "pending", "https://github.com/panagiotagrosdouli/DynNav/blob/main/docs/LILOCBENCH_DYNAMICS_0_ANALYSIS.md"],
  ["Gazebo / physical robot", "Simulation and hardware evidence require their own verified runs and artifacts.", "pending", "https://github.com/panagiotagrosdouli/DynNav/blob/main/docs/GAZEBO_BENCHMARK_PROTOCOL.md"],
] as const;

const pipeline = [
  ["01", "Observe", "Occupancy, uncertainty and route-changing events"],
  ["02", "Estimate", "Traversal risk and preservation of escape options"],
  ["03", "Plan", "Shortest, risk-aware, recoverability-aware and joint objectives"],
  ["04", "Audit", "Metrics, CSV/JSON artifacts, provenance and SHA-256 digests"],
] as const;

const researcherHref = `${process.env.DYNNAV_SITE_BASE_PATH ?? ""}/researcher`;
const mappingLabHref = "https://github.com/panagiotagrosdouli/DynNav/blob/main/app/pages/05_Belief_Mapping_Lab.py";

export default function Home() {
  return (
    <main>
      <nav className="topbar" aria-label="Primary navigation">
        <a className="wordmark" href="#top" aria-label="DynNav home">
          <span className="mark" aria-hidden="true">D</span>
          <span>DynNav</span>
        </a>
        <div className="nav-links">
          <a href="#research-question">Research question</a>
          <a href="#architecture">Architecture</a>
          <a href="#contributions">Contributions</a>
          <a href="#evidence">Evidence</a>
        </div>
        <a className="nav-cta" href={researcherHref}>Open Researcher</a>
      </nav>

      <section className="hero" id="top">
        <div className="hero-copy">
          <p className="eyebrow"><span /> Recoverability-aware autonomous navigation</p>
          <h1>Plan toward the goal. Preserve a way back.</h1>
          <p className="lede">
            DynNav is an executable ROS 2 and Python research programme for studying
            risk, recoverability and online replanning when a changing environment
            invalidates the route ahead.
          </p>
          <div className="hero-actions">
            <a className="button button-primary" href="#contributions">Explore 26 contributions</a>
            <a className="button button-secondary" href="https://github.com/panagiotagrosdouli/DynNav">Inspect the source</a>
          </div>
          <div className="hero-meta" aria-label="Project scope">
            <div><strong>26</strong><span>numbered contribution tracks</span></div>
            <div><strong>4</strong><span>canonical planner objectives</span></div>
            <div><strong>ROS 2</strong><span>Jazzy / Nav2 integration checks in CI</span></div>
          </div>
        </div>

        <div className="route-card" aria-label="Illustrative recoverability-aware route comparison">
          <div className="card-header"><span>Synthetic route vignette</span><em>illustrative</em></div>
          <svg viewBox="0 0 620 390" role="img" aria-label="Illustrative risky short route and recoverability-aware route">
            <defs>
              <pattern id="grid" width="52" height="52" patternUnits="userSpaceOnUse">
                <path d="M 52 0 L 0 0 0 52" fill="none" stroke="#203248" strokeWidth="1" />
              </pattern>
              <filter id="glow"><feGaussianBlur stdDeviation="4" result="blur" /><feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
            </defs>
            <rect width="620" height="390" fill="url(#grid)" />
            <g fill="#30445c">
              <rect x="52" y="52" width="156" height="52" rx="4" />
              <rect x="156" y="104" width="52" height="156" rx="4" />
              <rect x="364" y="52" width="52" height="156" rx="4" />
              <rect x="364" y="260" width="156" height="52" rx="4" />
            </g>
            <path className="route route-risk" d="M78 338 L78 234 L286 234 L286 130 L546 130 L546 52" />
            <path className="route route-safe" d="M78 338 L286 338 L286 286 L546 286 L546 52" />
            <circle className="hazard" cx="286" cy="234" r="18" />
            <circle className="robot" cx="286" cy="338" r="12" filter="url(#glow)" />
            <circle cx="78" cy="338" r="8" fill="#eef6ff" />
            <circle cx="546" cy="52" r="8" fill="#65e6d5" />
          </svg>
          <div className="legend">
            <span><i className="safe" /> recoverability-aware</span>
            <span><i className="risk" /> shortest / brittle</span>
          </div>
        </div>
      </section>

      <section className="briefs" aria-label="Project summary for decision makers and engineers">
        <article>
          <p className="eyebrow"><span /> Executive brief</p>
          <h2>What is being built and what is proven?</h2>
          <p>Research software for navigation decisions in environments that can change after planning. The current verified scope is executable code, registered controlled experiments, and reproducible CI. External-world efficacy is still a validation milestone.</p>
          <a href="https://github.com/panagiotagrosdouli/DynNav/blob/main/CLAIM_EVIDENCE_MATRIX.md">Read the claim-to-evidence matrix →</a>
        </article>
        <article>
          <p className="eyebrow"><span /> Engineering brief</p>
          <h2>ROS maps, planners, evidence artifacts.</h2>
          <p>Import a ROS map-server YAML and its PGM/PNG occupancy image, inspect occupancy semantics, and run a static A* reachability baseline. The interface labels this as map validation; it does not imply live ROS control or physical-robot results.</p>
          <a href={mappingLabHref}>Open the ROS map lab source →</a>
        </article>
      </section>

      <section className="architecture" id="architecture">
        <div className="section-heading">
          <p className="eyebrow"><span /> Executable architecture</p>
          <h2>One research question, traceable from decision to artifact.</h2>
          <p>Every reported result should connect to a configuration, command, metric contract and stored output.</p>
        </div>
        <div className="pipeline">
          {pipeline.map(([number, title, detail]) => (
            <article key={number}>
              <span className="step">{number}</span>
              <h3>{title}</h3>
              <p>{detail}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="history-question" id="research-question">
        <div className="section-heading">
          <p className="eyebrow"><span /> History-conditioned recoverability</p>
          <h2>The same position can represent a different planning state.</h2>
          <p>A traversed action can activate a possible future topology change. If that activation changes which return routes may close, the planner conditions recoverability on the executed history as well as the current position.</p>
        </div>
        <div className="history-grid">
          <figure className="history-card">
            <figcaption><strong>Executed history H₁</strong><span>An action has activated a possible closure.</span></figcaption>
            <svg viewBox="0 0 430 180" role="img" aria-label="Schematic history one: a trigger action activates a possible closure on a return edge before arriving at the same current position">
              <path className="history-route" d="M42 132 L156 132 L270 132 L386 132" />
              <path className="history-return" d="M270 104 L156 104 L42 104" />
              <path className="history-hazard-edge" d="M156 104 L156 48 L270 48 L270 104" />
              <circle className="history-node" cx="42" cy="132" r="12" /><circle className="history-node" cx="156" cy="132" r="12" /><circle className="history-current" cx="270" cy="132" r="15" /><circle className="history-goal" cx="386" cy="132" r="12" />
              <text x="27" y="165">safe</text><text x="141" y="165">trigger</text><text x="250" y="165">current x</text><text x="371" y="165">goal</text><text x="184" y="36">possible closure</text>
            </svg>
            <p className="history-equation">H₁ includes the activated hazard; return risk is conditioned on H₁.</p>
          </figure>
          <figure className="history-card">
            <figcaption><strong>Executed history H₂</strong><span>The triggering action was not taken.</span></figcaption>
            <svg viewBox="0 0 430 180" role="img" aria-label="Schematic history two: a different route reaches the same current position without activating the possible closure">
              <path className="history-route history-route-alt" d="M42 132 L156 132 L270 132 L386 132" />
              <path className="history-return history-return-open" d="M270 104 L156 104 L42 104" />
              <path className="history-hazard-edge history-hazard-inactive" d="M156 104 L156 48 L270 48 L270 104" />
              <circle className="history-node" cx="42" cy="132" r="12" /><circle className="history-node" cx="156" cy="132" r="12" /><circle className="history-current" cx="270" cy="132" r="15" /><circle className="history-goal" cx="386" cy="132" r="12" />
              <text x="27" y="165">safe</text><text x="141" y="165">bypass</text><text x="250" y="165">current x</text><text x="371" y="165">goal</text><text x="186" y="36">not activated</text>
            </svg>
            <p className="history-equation">H₂ differs from H₁, so R(x,H₂) may differ from R(x,H₁).</p>
          </figure>
        </div>
        <p className="history-boundary">Conceptual topology diagram, not a measured map or probability result. Hazard activation is tied to executed transitions; planning a route alone does not activate it. The model's conditional return probability must be supported by the specified hazard distribution and experiment.</p>
      </section>

      <ContributionExplorer />
      <RealDataTrajectory />

      <section className="evidence" id="evidence">
        <div className="section-heading compact">
          <p className="eyebrow"><span /> Scientific boundary</p>
          <h2>Evidence is separated by maturity tier.</h2>
          <p>“Available” means the interface can process supplied map files. It does not mean a dataset benchmark has been run.</p>
        </div>
        <div className="evidence-grid">
          {evidence.map(([name, detail, status, href]) => (
            <div className="evidence-row" key={name}>
              <div><strong>{name}</strong><span>{detail}</span></div>
              <a className={`evidence-status ${status}`} href={href}>{status}</a>
            </div>
          ))}
        </div>
        <p className="boundary-copy">
          C01–C26 smoke suite results are implementation and reproducibility evidence, mostly controlled/synthetic.
          Public-dataset paired trials, Gazebo dynamic-scene evidence and physical-robot evidence remain separate and pending.
        </p>
      </section>

      <section className="interfaces" id="interfaces">
        <div className="section-heading compact">
          <p className="eyebrow"><span /> Research workflow</p>
          <h2>Read the science. Inspect the implementation. Run the protocol.</h2>
        </div>
        <div className="interface-grid">
          <article>
            <span className="surface-label">Research site</span>
            <h3>Full research overview</h3>
            <p>The repository README preserves the detailed model, retained results, negative findings, ROS 2 architecture and scientific limitations.</p>
            <a href="https://github.com/panagiotagrosdouli/DynNav/blob/main/README.md">Open the research guide on GitHub →</a>
          </article>
          <article className="accent-card">
            <span className="surface-label">DynNav Researcher</span>
            <h3>Protocol design and experiment execution</h3>
            <p>Compile a research question into an editable four-planner protocol and expose results only after execution.</p>
            <a href={researcherHref}>Open the Researcher interface →</a>
          </article>
          <article>
            <span className="surface-label">Protocol</span>
            <h3>Reproduce the controlled studies</h3>
            <p>Use the frozen experiment protocol and generated C01–C26 catalog to inspect commands, metrics, dependencies, and claim boundaries.</p>
            <a href="https://github.com/panagiotagrosdouli/DynNav/blob/main/EXPERIMENT_PROTOCOL_V3.md">Open protocol V3 →</a>
          </article>
          <article>
            <span className="surface-label">Publication</span>
            <h3>Manuscript and evidence provenance</h3>
            <p>Inspect the manuscript source, citation metadata, claim-evidence matrix, and paper-facing artifact manifest.</p>
            <a href="https://github.com/panagiotagrosdouli/DynNav/blob/main/paper/dynnav_r/evidence_manifest.json">Open evidence manifest →</a>
          </article>
          <article>
            <span className="surface-label">Robotics stack</span>
            <h3>ROS 2, Nav2, and Gazebo</h3>
            <p>Read the plugin integration guide and frozen action-triggered Gazebo protocol. Integration checks do not establish physical-robot efficacy.</p>
            <a href="https://github.com/panagiotagrosdouli/DynNav/blob/main/docs/ROS2_NAV2_INTEGRATION.md">Open ROS 2 / Nav2 guide →</a>
          </article>
          <article>
            <span className="surface-label">Real data</span>
            <h3>Trajectory analysis and limits</h3>
            <p>Review the LILocBench trajectory measurements and the separate plan for map, bag replay, and matched planner validation.</p>
            <a href="https://github.com/panagiotagrosdouli/DynNav/blob/main/docs/REAL_DATA_VALIDATION.md">Open real-data validation record →</a>
          </article>
        </div>
      </section>

      <footer>
        <span>DynNav · research software with explicit evidence boundaries</span>
        <a href="https://github.com/panagiotagrosdouli/DynNav">GitHub repository</a>
      </footer>
    </main>
  );
}
