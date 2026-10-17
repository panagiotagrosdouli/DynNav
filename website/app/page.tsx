const repository = "https://github.com/panagiotagrosdouli/DynNav";
const docs = `${repository}/blob/main`;
const researcherHref = `${process.env.DYNNAV_SITE_BASE_PATH ?? ""}/researcher/`;

const pipeline = [
  ["01", "Execute", "Record the robot's actual directed transitions, not merely proposed paths."],
  ["02", "Update history", "Track action-triggered hazards activated by those executed transitions."],
  ["03", "Evaluate return", "Estimate safe-return probability conditional on position and hazard history."],
  ["04", "Plan & audit", "Search the augmented state and preserve reproducible experiment artifacts."],
] as const;

const evidence = [
  ["Controlled 3-module benchmark", "Shortest/state-only: 0.992 failure; history-aware: 0.000", "synthetic"],
  ["Held-out 6-module benchmark", "Shortest/state-only: 0.992 failure; history-aware: 0.000", "synthetic"],
  ["Fork, L-room, chamber", "Constructed geometric tests; not physical-robot validation", "geometric"],
  ["ROS 2 Jazzy / Nav2", "C++ global planner with persistent executed-history tracking", "prototype"],
  ["Gazebo integration", "Action-triggered execution and measurement protocols", "prototype"],
] as const;

export default function Home() {
  return (
    <main>
      <nav className="topbar" aria-label="Primary navigation">
        <a className="wordmark" href="#top" aria-label="DynNav home"><span className="mark" aria-hidden="true">D</span><span>DynNav</span></a>
        <div className="nav-links"><a href="#idea">Research idea</a><a href="#architecture">Method</a><a href="#evidence">Evidence</a><a href="#interfaces">Explore</a></div>
        <a className="nav-cta" href={repository}>GitHub ↗</a>
      </nav>

      <section className="hero" id="top">
        <div className="hero-copy">
          <p className="eyebrow"><span /> History-conditioned autonomous navigation</p>
          <h1>Same place. Different history. Different way back.</h1>
          <p className="lede">
            DynNav is a research prototype for safe-return planning when actions taken by an autonomous robot can trigger future changes in environmental connectivity.
            Planning considers <strong>where the robot is</strong> and <strong>which hazards its executed path has activated</strong>.
          </p>
          <div className="hero-actions">
            <a className="button button-primary" href="#idea">Understand the research</a>
            <a className="button button-secondary" href={repository}>View source code ↗</a>
            <a className="button button-secondary" href={`${docs}/README_GR.md`}>Ελληνικά ↗</a>
          </div>
          <div className="hero-meta">
            <div><strong>(x, H)</strong><span>history-conditioned planning state</span></div>
            <div><strong>A*</strong><span>exact augmented-state search</span></div>
            <div><strong>ROS 2</strong><span>Jazzy / Nav2 research integration</span></div>
          </div>
        </div>
        <div className="route-card" aria-label="Illustrative comparison of action-triggered navigation histories">
          <div className="card-header"><span>Illustrative research concept</span><em>same position ≠ same state</em></div>
          <svg viewBox="0 0 620 390" role="img" aria-label="Two routes to a shared destination, one crossing an action-triggered hazard">
            <defs><pattern id="grid" width="52" height="52" patternUnits="userSpaceOnUse"><path d="M52 0 L0 0 0 52" fill="none" stroke="#203248" strokeWidth="1" /></pattern></defs>
            <rect width="620" height="390" fill="url(#grid)" />
            <g fill="#30445c"><rect x="52" y="52" width="156" height="52" rx="4" /><rect x="156" y="104" width="52" height="156" rx="4" /><rect x="364" y="52" width="52" height="156" rx="4" /><rect x="364" y="260" width="156" height="52" rx="4" /></g>
            <path className="route route-risk" d="M78 338 L78 234 L286 234 L286 130 L546 130 L546 52" />
            <path className="route route-safe" d="M78 338 L286 338 L286 286 L546 286 L546 52" />
            <circle className="hazard" cx="286" cy="234" r="18" />
            <circle className="robot" cx="78" cy="338" r="12" />
            <circle cx="546" cy="52" r="9" fill="#65e6d5" />
          </svg>
          <div className="legend"><span><i className="safe" /> avoids trigger</span><span><i className="risk" /> activates hazard</span></div>
        </div>
      </section>

      <section className="architecture" id="idea">
        <div className="section-heading">
          <p className="eyebrow"><span /> The research question</p>
          <h2>What if the path you took changes which paths remain possible?</h2>
          <p>Two executions can reach the same geometric position but have different future return connectivity. A position-only planner can miss this distinction. DynNav studies whether retaining the activated-hazard history improves decision-making in precisely this class of problems.</p>
        </div>
        <div className="concept-equation">Planning state: <strong>(position, activated hazard history)</strong> = <strong>(x, H)</strong></div>
      </section>

      <section className="architecture" id="architecture">
        <div className="section-heading"><p className="eyebrow"><span /> Method</p><h2>From executed movement to history-aware planning.</h2><p>The history is updated by real transitions, not by paths that were only considered by the planner.</p></div>
        <div className="pipeline">{pipeline.map(([number,title,detail]) => <article key={number}><span className="step">{number}</span><h3>{title}</h3><p>{detail}</p></article>)}</div>
      </section>

      <section className="evidence" id="evidence">
        <div className="section-heading compact"><p className="eyebrow"><span /> Reproducible evidence</p><h2>Research results, with their boundaries clearly stated.</h2><p>Representative values come from the repository's retained controlled evaluations, not open-world performance claims.</p></div>
        <div className="evidence-grid">{evidence.map(([name,detail,kind]) => <div className="evidence-row" key={name}><div><strong>{name}</strong><span>{detail}</span></div><em className="verified">{kind}</em></div>)}</div>
        <p className="boundary-copy">The reported failure rates are from controlled synthetic or constructed geometric evaluations. This site does not claim universal superiority, safety certification, or demonstrated efficacy on a physical robot. Hard safe-return constraints can match the exact history-aware method in some tested settings. <a href={`${docs}/CLAIM_EVIDENCE_MATRIX.md`}>Read the claim–evidence matrix ↗</a></p>
      </section>

      <section className="interfaces" id="interfaces">
        <div className="section-heading compact"><p className="eyebrow"><span /> Explore DynNav</p><h2>Read the science. Inspect the implementation.</h2></div>
        <div className="interface-grid">
          <article><span className="surface-label">Research documentation</span><h3>Paper, code and experimental provenance</h3><p>Read the technical manuscript, reproducibility guide and documented limitations.</p><a href={`${docs}/paper/dynnav_r/main.tex`}>Read IEEE manuscript source →</a><p><a href={`${docs}/docs/REPOSITORY_GUIDE.md`}>Repository guide →</a></p></article>
          <article className="accent-card"><span className="surface-label">Research workspace</span><h3>Experiment interface</h3><p>Explore the research workspace. Executing experiments requires its separate FastAPI backend; the static website does not run simulations.</p><a href={researcherHref}>Open Researcher →</a><p><a href={repository}>Browse GitHub source →</a></p></article>
        </div>
      </section>
      <footer><span>DynNav · Panagiota Grosdouli · Research prototype</span><a href={repository}>GitHub repository ↗</a></footer>
    </main>
  );
}
