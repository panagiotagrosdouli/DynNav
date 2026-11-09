import { ContributionExplorer } from "../components/contribution-explorer";
import { RealDataTrajectory } from "../components/real-data-trajectory";

const evidence = [
  ["Contribution suite", "Controlled smoke experiment registered for each C01–C26 track", "CI"],
  ["Python research core", "Unit and integration checks run in GitHub Actions", "CI"],
  ["ROS map intake", "ROS map-server YAML + PGM/PNG upload and static A* route viewer", "available"],
  ["Public dataset trial", "LILocBench map/sequence analysis with recorded provenance", "pending"],
  ["Gazebo / physical robot", "Paired dynamic-scene and hardware trials with traceable logs", "pending"],
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
          <a href="https://github.com/panagiotagrosdouli/DynNav/blob/main/docs/CLAIM_EVIDENCE_MATRIX.md">Read the claim-to-evidence matrix →</a>
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
          <p>
            <a href="https://github.com/panagiotagrosdouli/DynNav/blob/main/docs/FULL_REPOSITORY_TOPOLOGY_2026-11-09.md">
              Inspect the complete 381-folder repository topology and architecture boundaries →
            </a>
          </p>
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

      <ContributionExplorer />
      <RealDataTrajectory />

      <section className="evidence" id="evidence">
        <div className="section-heading compact">
          <p className="eyebrow"><span /> Scientific boundary</p>
          <h2>Evidence is separated by maturity tier.</h2>
          <p>“Available” means the interface can process supplied map files. It does not mean a dataset benchmark has been run.</p>
        </div>
        <div className="evidence-grid">
          {evidence.map(([name, detail, status]) => (
            <div className="evidence-row" key={name}>
              <div><strong>{name}</strong><span>{detail}</span></div>
              <em className={status === "pending" ? "pending" : status === "available" ? "available" : "verified"}>{status}</em>
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
            <h3>Project narrative and evidence map</h3>
            <p>Research question, architecture, contribution registry and evidence boundaries in one public overview.</p>
            <a href="https://github.com/panagiotagrosdouli/DynNav/blob/main/docs/README.md">Open technical documentation →</a>
          </article>
          <article className="accent-card">
            <span className="surface-label">DynNav Researcher</span>
            <h3>Protocol design and experiment execution</h3>
            <p>Compile a research question into an editable four-planner protocol and expose results only after execution.</p>
            <a href={researcherHref}>Open the Researcher interface →</a>
            <p>
              Experiments require the separate Python API service; GitHub Pages hosts the frontend only.
              <a href="https://github.com/panagiotagrosdouli/DynNav/blob/main/dynnav/researcher/api.py">
                {" "}Inspect the actual FastAPI endpoints →
              </a>
            </p>
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
