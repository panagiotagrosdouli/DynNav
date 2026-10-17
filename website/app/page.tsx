const repo = "https://github.com/panagiotagrosdouli/DynNav";
const source = `${repo}/tree/main`;
const file = `${repo}/blob/main`;
const workspace = `${process.env.DYNNAV_SITE_BASE_PATH ?? ""}/researcher/`;

const projects = [
  { number: "01", category: "CORE RESEARCH", name: "History-aware navigation", detail: "Exact augmented-state A* over position and activated hazard history, with action-triggered topology changes.", tech: "Python · A* · Stochastic modeling", href: `${file}/dynnav/planners/commitment_aware_astar.py` },
  { number: "02", category: "ROBOTICS ENGINEERING", name: "ROS 2 / Nav2 planner", detail: "C++ global planner plugin for ROS 2 Jazzy with persistent hazard history derived from executed motion.", tech: "C++17 · ROS 2 Jazzy · Nav2", href: `${source}/ros2_ws/src/dynnav_nav2_cpp` },
  { number: "03", category: "SIMULATION", name: "Gazebo benchmark system", detail: "Static, dynamic and action-triggered environment scenarios with execution and measurement contracts.", tech: "Gazebo · ROS 2 · Benchmarking", href: `${source}/ros2_ws/src/dynnav_nav2_benchmark` },
  { number: "04", category: "ALGORITHMS", name: "Recoverability & baselines", detail: "Exact safe-return estimates, critical-cut approximation and shortest, state-only and hard-constraint comparisons.", tech: "Probability · Graph search · Ablations", href: `${source}/dynnav/planners` },
  { number: "05", category: "EXPERIMENTS", name: "Evaluation & reproducibility", detail: "Paired stochastic studies, held-out geometries, statistical tests, retained results and explicit negative findings.", tech: "Python · Statistical analysis · Provenance", href: `${file}/CLAIM_EVIDENCE_MATRIX.md` },
  { number: "06", category: "RESEARCH SOFTWARE", name: "Interactive research tools", detail: "Streamlit lab, FastAPI service, Next.js workspace and a research-facing presentation website.", tech: "Streamlit · FastAPI · Next.js", href: `${source}/apps` },
] as const;

const process = [
  ["01", "Model", "Directed robot actions activate stochastic topology hazards."],
  ["02", "Implement", "Build exact and approximate planners plus robust baselines."],
  ["03", "Integrate", "Connect planning to ROS 2 / Nav2 and Gazebo protocols."],
  ["04", "Evaluate", "Retain seeds, artifacts, metrics, counterexamples and limitations."],
] as const;

const visuals = [
  { id: "C01", title: "Learned A* planning", src: "C01_overview.svg" },
  { id: "C04", title: "Returnability & recoverability", src: "C04_overview.svg" },
  { id: "C09", title: "Multi-robot coordination", src: "C09_overview.svg" },
  { id: "C17", title: "Semantic topological maps", src: "C17_overview.svg" },
  { id: "C18", title: "Formal safety shields", src: "C18_overview.svg" },
  { id: "C25", title: "Adversarial navigation testing", src: "C25_overview.svg" },
] as const;

const experimentVisuals = [
 { title:"Path comparison", path:"contributions/04_irreversibility_returnability/results/path_overlay_hard_vs_soft.png", caption:"Historical returnability study · route overlay" },
 { title:"Returnability heatmap", path:"contributions/04_irreversibility_returnability/results/returnability_heatmap.png", caption:"Historical recoverability exploration · visual metric map" },
 { title:"Learned vs classic A*", path:"contributions/01_learned_astar/results/astar_learned_vs_classic.png", caption:"Exploratory learned-search baseline comparison" },
 { title:"Risk–length trade-off", path:"contributions/03_belief_risk_planning/results/lambda_sweep_length_risk_tradeoff.png", caption:"Belief/risk planning parameter sweep" },
 { title:"Multi-robot evaluation", path:"contributions/09_multi_robot/results/memory_failures_over_time.png", caption:"Historical multi-robot experiment plot" },
 { title:"Safe-mode activation", path:"contributions/05_safe_mode_navigation/results/safe_mode_activation_vs_tau0.png", caption:"Historical safety supervisor experiment" },
] as const;

export default function Home() {
  return (
    <main>
      <nav className="topbar" aria-label="Primary navigation">
        <a className="wordmark" href="#top"><span className="mark" aria-hidden="true">D</span> DynNav<span className="portfolio-dot">.</span></a>
        <div className="nav-links"><a href="#about">About</a><a href="#work">My work</a><a href="#gallery">Gallery</a><a href="#plots">Plots</a><a href="#results">Results</a><a href="#explore">Explore</a></div>
        <a className="nav-cta" href={repo} target="_blank" rel="noopener noreferrer">View GitHub ↗</a>
      </nav>

      <section className="hero portfolio-hero" id="top">
        <div className="hero-copy">
          <p className="eyebrow"><span /> A robotics & AI research project by Panagiota Grosdouli</p>
          <h1>Building navigation that thinks <em>beyond the next move.</em></h1>
          <p className="lede">I'm developing <strong>DynNav</strong> — an autonomous navigation research ecosystem spanning intelligent path planning, recoverability modeling, ROS 2 integration, simulation, experimental evaluation and interactive research software.</p>
          <div className="hero-actions">
            <a className="button button-primary" href="#work">Explore my work ↗</a>
            <a className="button button-secondary" href={repo}>View the repository</a>
          </div>
          <div className="hero-meta">
            <div><strong>Python + C++</strong><span>algorithm development</span></div>
            <div><strong>ROS 2 / Nav2</strong><span>robotics integration</span></div>
            <div><strong>Research</strong><span>controlled & reproducible experiments</span></div>
          </div>
        </div>
        <div className="route-card" aria-label="Illustrated robot navigation paths">
          <div className="card-header"><span>DYNNAV / NAVIGATION LAB</span><em>Illustrative route visualization</em></div>
          <svg viewBox="0 0 620 390" role="img" aria-label="Two possible robot navigation routes around a hazard">
            <defs><pattern id="grid" width="52" height="52" patternUnits="userSpaceOnUse"><path d="M52 0 L0 0 0 52" fill="none" stroke="#203248" strokeWidth="1" /></pattern></defs>
            <rect width="620" height="390" fill="url(#grid)" />
            <g fill="#30445c"><rect x="52" y="52" width="156" height="52" rx="4" /><rect x="156" y="104" width="52" height="156" rx="4" /><rect x="364" y="52" width="52" height="156" rx="4" /><rect x="364" y="260" width="156" height="52" rx="4" /></g>
            <path className="route route-risk" d="M78 338 L78 234 L286 234 L286 130 L546 130 L546 52" />
            <path className="route route-safe" d="M78 338 L286 338 L286 286 L546 286 L546 52" />
            <circle className="hazard" cx="286" cy="234" r="18" />
            <circle className="robot" cx="78" cy="338" r="12" />
            <circle cx="546" cy="52" r="9" fill="#65e6d5" />
          </svg>
          <div className="legend"><span><i className="safe" /> alternative route</span><span><i className="risk" /> triggered-hazard route</span></div>
        </div>
      </section>

      <section className="architecture" id="about">
        <div className="section-heading"><p className="eyebrow"><span /> The project</p><h2>From an idea to an end-to-end research system.</h2><p>DynNav grew into a collection of connected implementations: planning algorithms, models of safe return, robot software, simulation protocols, benchmarks and reproducible scientific results. Its current scientific focus is history-conditioned safe-return planning, where the route actually executed can change future connectivity.</p></div>
        <div className="concept-equation"><span>THE CENTRAL IDEA</span><strong>Same location ≠ same planning state.</strong><p>The robot's location and the hazards activated by its previous actions both matter: (x, H).</p></div>
      </section>

      <section className="architecture portfolio-work" id="work">
        <div className="section-heading"><p className="eyebrow"><span /> Selected work</p><h2>What I've built.</h2><p>Explore the main research and engineering areas in the repository. Each project links to its implementation or documentation.</p></div>
        <div className="work-grid">{projects.map((item) => <a className="work-card" href={item.href} key={item.number} target="_blank" rel="noopener noreferrer">
          <div className="work-card-top"><span>{item.number} / {item.category}</span><span>↗</span></div>
          <h3>{item.name}</h3><p>{item.detail}</p><div className="work-tech">{item.tech}</div>
        </a>)}</div>
      </section>


      <section className="architecture gallery-section" id="gallery">
        <div className="section-heading"><p className="eyebrow"><span /> Visual project gallery</p><h2>A closer look at the systems.</h2><p>Original diagrams from the DynNav repository, illustrating selected research modules. These are explanatory architecture visuals, not simulation screenshots or empirical results.</p></div>
        <figure className="map-figure">
          <img src="https://raw.githubusercontent.com/panagiotagrosdouli/DynNav/main/assets/readme/dynnav_living_map.svg" alt="DynNav research illustration showing a grid map, risk area and alternative navigation paths" loading="lazy" />
          <figcaption>DynNav living map · conceptual visualization</figcaption>
        </figure>
        <div className="gallery-grid">
          {visuals.map(v => <a key={v.id} className="gallery-card" href={`${file}/assets/contributions/${v.src}`} target="_blank" rel="noopener noreferrer">
            <div className="gallery-image"><img src={`https://raw.githubusercontent.com/panagiotagrosdouli/DynNav/main/assets/contributions/${v.src}`} alt={`${v.id}: ${v.title} explanatory module diagram`} loading="lazy" /></div>
            <div className="gallery-label"><span>{v.id} / {v.title}</span><span>↗</span></div>
          </a>)}
        </div>
        <a className="gallery-all" href={`${file}/docs/CONTRIBUTION_VISUAL_GALLERY.md`}>Explore all 26 research-module diagrams →</a>
      </section>


      <section className="architecture experiment-gallery" id="plots">
        <div className="section-heading"><p className="eyebrow"><span /> Real research artifacts</p><h2>Plots and experiments from the repository.</h2><p>These are actual stored figures from earlier DynNav research modules. They illustrate the broader engineering and exploration history; they are not direct evidence for the current history-conditioned safe-return paper.</p></div>
        <div className="experiment-grid">{experimentVisuals.map(v => <a className="experiment-card" key={v.path} href={`${file}/${v.path}`} target="_blank" rel="noopener noreferrer">
          <div className="experiment-image"><img src={`https://raw.githubusercontent.com/panagiotagrosdouli/DynNav/main/${v.path}`} alt={v.title} loading="lazy" /></div>
          <div className="experiment-copy"><strong>{v.title} ↗</strong><span>{v.caption}</span></div>
        </a>)}</div>
        <p className="plot-note">Gazebo is represented by its documented benchmark infrastructure and validation protocols, rather than presenting an unverified simulation image as an executed run. For publication-facing numbers, consult the <a href={`${file}/paper/dynnav_r/evidence_manifest.json`}>evidence manifest</a>.</p>
      </section>
      <section className="architecture" id="approach">
        <div className="section-heading"><p className="eyebrow"><span /> How I work</p><h2>Research meets implementation.</h2><p>The project is structured to link mathematical modeling with executable robotic systems and auditable evidence.</p></div>
        <div className="pipeline">{process.map(([n,title,detail]) => <article key={n}><span className="step">{n}</span><h3>{title}</h3><p>{detail}</p></article>)}</div>
      </section>

      <section className="evidence" id="results">
        <div className="section-heading compact"><p className="eyebrow"><span /> Selected outcomes</p><h2>Measured, documented and reproducible.</h2><p>Representative outcomes from controlled research environments, with clear boundaries on interpretation.</p></div>
        <div className="evidence-grid">
          <div className="evidence-row"><div><strong>3-module controlled execution</strong><span>Shortest/state-only: 0.992 failure · history-aware: 0.000</span></div><em className="verified">synthetic</em></div>
          <div className="evidence-row"><div><strong>Held-out 6-module evaluation</strong><span>Shortest/state-only: 0.992 failure · history-aware: 0.000</span></div><em className="verified">synthetic</em></div>
          <div className="evidence-row"><div><strong>Fork / L-room / chamber</strong><span>Evaluation across three frozen, hand-authored topologies</span></div><em className="verified">geometric</em></div>
          <div className="evidence-row"><div><strong>ROS 2 & Gazebo</strong><span>Planner integration and execution/measurement protocol evidence</span></div><em className="verified">prototype</em></div>
        </div>
        <p className="boundary-copy">These findings concern controlled synthetic/geometric cases, not validated physical-robot safety. The research also retains approximation counterexamples and cases where hard safe-return constraints match the history-aware route. <a href={`${file}/CLAIM_EVIDENCE_MATRIX.md`}>Read the evidence and limitations ↗</a></p>
      </section>

      <section className="interfaces" id="explore">
        <div className="section-heading compact"><p className="eyebrow"><span /> Explore the project</p><h2>Go deeper into DynNav.</h2></div>
        <div className="interface-grid">
          <article><span className="surface-label">Open-source repository</span><h3>Source code, experiments and technical documentation</h3><p>Browse planners, ROS 2 packages, simulation infrastructure, tests, results and the research manuscript.</p><a href={repo}>Explore on GitHub →</a><p><a href={`${file}/README_GR.md`}>Ελληνική παρουσίαση →</a></p></article>
          <article className="accent-card"><span className="surface-label">Researcher workspace</span><h3>Explore the research interface</h3><p>The companion Next.js interface presents research workflows. Running real experiments requires the separate FastAPI backend.</p><a href={workspace}>Open workspace →</a><p><a href={`${file}/paper/dynnav_r/main.tex`}>Read the manuscript →</a></p></article>
        </div>
      </section>
      <footer><span>© 2026 Panagiota Grosdouli · DynNav research & engineering portfolio</span><a href={repo}>GitHub ↗</a></footer>
    </main>
  );
}
