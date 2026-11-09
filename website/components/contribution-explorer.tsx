"use client";

import { useMemo, useState } from "react";

type Contribution = {
  id: string;
  title: string;
  category: string;
  summary: string;
  maturity: string;
};

const contributions: Contribution[] = [
  { id: "C01", title: "Learned A* Search", category: "Planning", summary: "Compare classical A* with a learned heuristic bias.", maturity: "Research Prototype" },
  { id: "C02", title: "Uncertainty Estimation", category: "Uncertainty", summary: "Explore state-estimation uncertainty and calibration behavior.", maturity: "Research Prototype" },
  { id: "C03", title: "Risk-Aware A*", category: "Risk and safety", summary: "Compare shortest-path and risk-aware route selection.", maturity: "Research Prototype" },
  { id: "C04", title: "Returnability and Recoverability", category: "Risk and safety", summary: "Measure whether future states preserve recovery options.", maturity: "Research Prototype" },
  { id: "C05", title: "Safe-Mode Supervisor", category: "Risk and safety", summary: "Inspect finite-state safety supervision and thresholds.", maturity: "Research Prototype" },
  { id: "C06", title: "Energy and Connectivity", category: "Planning", summary: "Explore mission feasibility under resource constraints.", maturity: "Research Prototype" },
  { id: "C07", title: "Safe Next-Best View", category: "Mapping and perception", summary: "Balance information gain, risk, connectivity, and returnability.", maturity: "Research Prototype" },
  { id: "C08", title: "Security and Intrusion Detection", category: "Security and robustness", summary: "Explore anomaly detection for navigation observations.", maturity: "Experimental" },
  { id: "C09", title: "Multi-Robot Coordination", category: "Multi-robot systems", summary: "Study coordination, shared beliefs, and mission conflicts.", maturity: "Experimental" },
  { id: "C10", title: "Human-Aware Navigation", category: "Human interaction", summary: "Explore socially aware navigation costs and behaviors.", maturity: "Experimental" },
  { id: "C11", title: "VLM Navigation Agent", category: "Perception and navigation", summary: "Validate semantic navigation goals before passing them to metric planning.", maturity: "Experimental" },
  { id: "C12", title: "Diffusion Occupancy Prediction", category: "Mapping and perception", summary: "Explore generative occupancy prediction under uncertainty.", maturity: "Experimental" },
  { id: "C13", title: "Latent World Model", category: "Learning", summary: "Inspect compact latent dynamics for future-state prediction.", maturity: "Experimental" },
  { id: "C14", title: "Causal Risk Attribution", category: "Risk and safety", summary: "Study structured causes of navigation risk.", maturity: "Experimental" },
  { id: "C15", title: "Neuromorphic Sensing", category: "Mapping and perception", summary: "Explore event-driven sensing representations.", maturity: "Experimental" },
  { id: "C16", title: "Federated Navigation Learning", category: "Learning", summary: "Examine decentralized model updates across robots.", maturity: "Experimental" },
  { id: "C17", title: "Semantic Topological Maps", category: "Mapping and perception", summary: "Combine semantic regions with graph-based navigation.", maturity: "Experimental" },
  { id: "C18", title: "Formal Safety Shields", category: "Risk and safety", summary: "Explore barrier-function and temporal-logic interventions.", maturity: "Experimental" },
  { id: "C19", title: "Language Mission Planner", category: "Mission reasoning", summary: "Convert natural-language instructions into mission structure.", maturity: "Documentation Concept" },
  { id: "C20", title: "Failure Explanation", category: "Human interaction", summary: "Generate structured explanations from failure evidence.", maturity: "Experimental" },
  { id: "C21", title: "PPO Navigation", category: "Learning", summary: "Explore policy optimization for navigation behavior.", maturity: "Experimental" },
  { id: "C22", title: "Curriculum Reinforcement Learning", category: "Learning", summary: "Study staged training difficulty and policy progression.", maturity: "Experimental" },
  { id: "C23", title: "Gaussian Splatting Maps", category: "Scene representation", summary: "Explore dense scene representations for navigation context.", maturity: "Documentation Concept" },
  { id: "C24", title: "NeRF Uncertainty", category: "Scene representation", summary: "Examine uncertainty-aware neural scene representations.", maturity: "Documentation Concept" },
  { id: "C25", title: "Adversarial Navigation Testing", category: "Security and robustness", summary: "Inject disturbances and inspect navigation robustness.", maturity: "Experimental" },
  { id: "C26", title: "Byzantine-Fault-Tolerant Swarm", category: "Multi-robot systems", summary: "Explore consensus under faulty or untrusted robot reports.", maturity: "Experimental" },
];

const views = [
  { id: "first-eleven", label: "C00 + C01–C11", matches: (id: string) => Number(id.slice(1)) <= 11 },
  { id: "all", label: "All C01–C26", matches: () => true },
  { id: "c26", label: "C26 only", matches: (id: string) => id === "C26" },
] as const;

export function ContributionExplorer() {
  const [view, setView] = useState<(typeof views)[number]["id"]>("first-eleven");
  const [maturity, setMaturity] = useState("All maturity levels");
  const [query, setQuery] = useState("");

  const selectedView = views.find((item) => item.id === view) ?? views[0];
  const visible = useMemo(() => contributions.filter((item) => {
    const matchesView = selectedView.matches(item.id);
    const matchesMaturity = maturity === "All maturity levels" || item.maturity === maturity;
    const needle = query.trim().toLowerCase();
    const matchesQuery = !needle || [item.id, item.title, item.category, item.summary].join(" ").toLowerCase().includes(needle);
    return matchesView && matchesMaturity && matchesQuery;
  }), [maturity, query, selectedView]);

  return (
    <section className="contributions" id="contributions">
      <div className="section-heading">
        <p className="eyebrow"><span /> Contribution registry</p>
        <h2>From the core idea to all 26 research tracks.</h2>
        <p>Browse the canonical contribution set. Each entry links to its registry record and the reproducible experiment contract.</p>
      </div>
      <div className="explorer-controls" aria-label="Contribution filters">
        <div className="view-tabs" role="group" aria-label="Contribution range">
          {views.map((item) => (
            <button key={item.id} type="button" aria-pressed={view === item.id} onClick={() => setView(item.id)}>
              {item.label}
            </button>
          ))}
        </div>
        <label className="search-label">
          <span>Search</span>
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Title, category, or ID" />
        </label>
        <label className="maturity-label">
          <span>Maturity</span>
          <select value={maturity} onChange={(event) => setMaturity(event.target.value)}>
            <option>All maturity levels</option>
            <option>Research Prototype</option>
            <option>Experimental</option>
            <option>Documentation Concept</option>
          </select>
        </label>
      </div>
      <div className="explorer-summary" aria-live="polite">
        <strong>{visible.length} of 26</strong>
        <span>registered tracks shown · filter updates immediately</span>
      </div>
      <div className="contribution-grid">
        {visible.map((item) => (
          <article className="contribution-card" key={item.id}>
            <div className="contribution-card-top">
              <span className="contribution-id">{item.id}</span>
              <span className="maturity-pill">{item.maturity}</span>
            </div>
            <p className="contribution-category">{item.category}</p>
            <h3>{item.title}</h3>
            <p className="contribution-summary">{item.summary}</p>
            <div className="contribution-links">
              <a href={`https://github.com/panagiotagrosdouli/DynNav/blob/main/docs/CONTRIBUTION_INDEX.md#${item.id.toLowerCase()}`}>Registry details ↗</a>
              <a href="https://github.com/panagiotagrosdouli/DynNav/blob/main/configs/contributions/experiments.yaml">Experiment contract ↗</a>
            </div>
          </article>
        ))}
      </div>
      {visible.length === 0 && <p className="empty-state">No contributions match these filters.</p>}
      <p className="explorer-boundary">
        The registry includes controlled smoke experiments; these demonstrate implementation behavior and reproducibility.
        They are not automatically real-world, Gazebo, or hardware evidence. C00 is the core hypothesis and is not a numbered registry track.
      </p>
    </section>
  );
}
