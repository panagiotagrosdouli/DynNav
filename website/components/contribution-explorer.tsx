"use client";

import { useMemo, useState } from "react";

type Contribution = {
  id: string;
  title: string;
  category: string;
  summary: string;
  maturity: string;
  source: string;
  experiment: string;
};

const contributions: Contribution[] = [
  { id: "C01", title: "Learned A* Search", category: "Planning", summary: "Compare classical A* with a learned heuristic bias.", maturity: "Research Prototype", source: "contributions/01_learned_astar", experiment: "contributions/01_learned_astar/experiments/eval_astar_learned.py" },
  { id: "C02", title: "Uncertainty Calibration", category: "Uncertainty", summary: "Explore state-estimation uncertainty and calibration behavior.", maturity: "Research Prototype", source: "contributions/02_uncertainty_calibration", experiment: "contributions/02_uncertainty_calibration/experiments/eval_uncertainty_calibration.py" },
  { id: "C03", title: "Belief and Risk Planning", category: "Risk and safety", summary: "Compare shortest-path and risk-aware route selection.", maturity: "Research Prototype", source: "contributions/03_belief_risk_planning", experiment: "contributions/03_belief_risk_planning/experiments/eval_risk_tradeoff.py" },
  { id: "C04", title: "Irreversibility and Returnability", category: "Risk and safety", summary: "Measure whether future states preserve recovery options.", maturity: "Research Prototype", source: "contributions/04_irreversibility_returnability", experiment: "contributions/04_irreversibility_returnability/experiments/eval_recoverability_metrics.py" },
  { id: "C05", title: "Safe-Mode Navigation", category: "Risk and safety", summary: "Inspect finite-state safety supervision and thresholds.", maturity: "Research Prototype", source: "contributions/05_safe_mode_navigation", experiment: "contributions/05_safe_mode_navigation/experiments/eval_safe_mode_thresholds.py" },
  { id: "C06", title: "Energy and Connectivity", category: "Planning", summary: "Explore mission feasibility under resource constraints.", maturity: "Research Prototype", source: "contributions/06_energy_connectivity", experiment: "contributions/06_energy_connectivity/experiments/eval_resource_feasibility.py" },
  { id: "C07", title: "Next-Best View", category: "Mapping and perception", summary: "Balance information gain, risk, connectivity, and returnability.", maturity: "Research Prototype", source: "contributions/07_next_best_view", experiment: "contributions/07_next_best_view/experiments/eval_returnability_aware_nbv.py" },
  { id: "C08", title: "Security IDS", category: "Security and robustness", summary: "Explore anomaly detection for navigation observations.", maturity: "Experimental", source: "contributions/08_security_ids", experiment: "contributions/08_security_ids/experiments/eval_ids_response_policy.py" },
  { id: "C09", title: "Multi-Robot Navigation", category: "Multi-robot systems", summary: "Study coordination, shared beliefs, and mission conflicts.", maturity: "Experimental", source: "contributions/09_multi_robot", experiment: "contributions/09_multi_robot/experiments/eval_team_coordination.py" },
  { id: "C10", title: "Human, Language, and Ethics", category: "Human interaction", summary: "Explore socially aware navigation costs and behaviors.", maturity: "Experimental", source: "contributions/10_human_language_ethics", experiment: "contributions/10_human_language_ethics/experiments/eval_human_ethics_policy.py" },
  { id: "C11", title: "VLM Navigation Agent", category: "Perception and navigation", summary: "Validate semantic navigation goals before passing them to metric planning.", maturity: "Experimental", source: "contributions/11_vlm_navigation_agent", experiment: "contributions/11_vlm_navigation_agent/experiments/eval_vlm_goal_validation.py" },
  { id: "C12", title: "Diffusion Occupancy", category: "Mapping and perception", summary: "Explore generative occupancy prediction under uncertainty.", maturity: "Experimental", source: "contributions/12_diffusion_occupancy", experiment: "contributions/12_diffusion_occupancy/experiments/eval_risk_map_quality.py" },
  { id: "C13", title: "Latent World Model", category: "Learning", summary: "Inspect compact latent dynamics for future-state prediction.", maturity: "Experimental", source: "contributions/13_latent_world_model", experiment: "contributions/13_latent_world_model/experiments/eval_rollout_audit.py" },
  { id: "C14", title: "Causal Risk Attribution", category: "Risk and safety", summary: "Study structured causes of navigation risk.", maturity: "Experimental", source: "contributions/14_causal_risk_attribution", experiment: "contributions/14_causal_risk_attribution/experiments/eval_root_cause_attribution.py" },
  { id: "C15", title: "Neuromorphic Sensing", category: "Mapping and perception", summary: "Explore event-driven sensing representations.", maturity: "Experimental", source: "contributions/15_neuromorphic_sensing", experiment: "contributions/15_neuromorphic_sensing/experiments/eval_neuromorphic_latency.py" },
  { id: "C16", title: "Federated Navigation Learning", category: "Learning", summary: "Examine decentralized model updates across robots.", maturity: "Experimental", source: "contributions/16_federated_nav_learning", experiment: "contributions/16_federated_nav_learning/experiments/eval_federated_tradeoffs.py" },
  { id: "C17", title: "Topological Semantic Maps", category: "Mapping and perception", summary: "Combine semantic regions with graph-based navigation.", maturity: "Experimental", source: "contributions/17_topological_semantic_maps", experiment: "contributions/17_topological_semantic_maps/experiments/eval_topo_semantic_navigation.py" },
  { id: "C18", title: "Formal Safety Shields", category: "Risk and safety", summary: "Explore barrier-function and temporal-logic interventions.", maturity: "Experimental", source: "contributions/18_formal_safety_shields", experiment: "contributions/18_formal_safety_shields/experiments/eval_shield_stress_test.py" },
  { id: "C19", title: "LLM Mission Planner", category: "Mission reasoning", summary: "Convert natural-language instructions into mission structure.", maturity: "Documentation Concept", source: "contributions/19_llm_mission_planner", experiment: "contributions/19_llm_mission_planner/experiments/eval_mission_plan_quality.py" },
  { id: "C20", title: "Multimodal Failure Explainer", category: "Human interaction", summary: "Generate structured explanations from failure evidence.", maturity: "Experimental", source: "contributions/20_multimodal_failure_explainer", experiment: "contributions/20_multimodal_failure_explainer/experiments/eval_failure_report_quality.py" },
  { id: "C21", title: "PPO Navigation Agent", category: "Learning", summary: "Explore policy optimization for navigation behavior.", maturity: "Experimental", source: "contributions/21_ppo_navigation_agent", experiment: "contributions/21_ppo_navigation_agent/experiments/eval_policy_safety.py" },
  { id: "C22", title: "Curriculum RL", category: "Learning", summary: "Study staged training difficulty and policy progression.", maturity: "Experimental", source: "contributions/22_curriculum_rl", experiment: "contributions/22_curriculum_rl/experiments/eval_curriculum_strategies.py" },
  { id: "C23", title: "Gaussian Splatting Mapper", category: "Scene representation", summary: "Explore dense scene representations for navigation context.", maturity: "Documentation Concept", source: "contributions/23_gaussian_splatting_mapper", experiment: "contributions/23_gaussian_splatting_mapper/experiments/eval_gs_mapping_quality.py" },
  { id: "C24", title: "NeRF Uncertainty", category: "Scene representation", summary: "Examine uncertainty-aware neural scene representations.", maturity: "Documentation Concept", source: "contributions/24_nerf_uncertainty", experiment: "contributions/24_nerf_uncertainty/experiments/eval_nerf_uncertainty.py" },
  { id: "C25", title: "Adversarial Attack Simulator", category: "Security and robustness", summary: "Inject disturbances and inspect navigation robustness.", maturity: "Experimental", source: "contributions/25_adversarial_attack_simulator", experiment: "contributions/25_adversarial_attack_simulator/experiments/eval_attack_impact.py" },
  { id: "C26", title: "Swarm Consensus", category: "Multi-robot systems", summary: "Explore consensus under faulty or untrusted robot reports.", maturity: "Experimental", source: "contributions/26_swarm_consensus", experiment: "contributions/26_swarm_consensus/experiments/eval_swarm_consensus.py" },
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
      {view === "first-eleven" && (
        <article className="core-card">
          <div className="contribution-card-top"><span className="contribution-id">C00 · CORE</span><span className="maturity-pill">Research hypothesis</span></div>
          <p className="contribution-category">Core research question</p>
          <h3>Dynamic navigation with recoverability</h3>
          <p className="contribution-summary">When a route changes or becomes blocked, can online replanning account for risk while preserving a feasible way to recover?</p>
          <a href="https://github.com/panagiotagrosdouli/DynNav/blob/main/README.md">Project hypothesis and protocol ↗</a>
        </article>
      )}
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
              <a href={`https://github.com/panagiotagrosdouli/DynNav/tree/main/${item.source}`}>Source and research note ↗</a>
              <a href={`https://github.com/panagiotagrosdouli/DynNav/blob/main/${item.experiment}`}>Experiment runner ↗</a>
            </div>
          </article>
        ))}
      </div>
      <article className="contribution-card theory-card">
        <div className="contribution-card-top"><span className="contribution-id">C27 · THEORY TRACK</span><span className="maturity-pill">Research proposal</span></div>
        <p className="contribution-category">Recoverability theory</p>
        <h3>Definitions, candidate results, and falsification criteria</h3>
        <p className="contribution-summary">An independent theory proposal covering returnability, viability, history-dependent risk, and the assumptions required for future proofs.</p>
        <div className="contribution-links">
          <a href="https://github.com/panagiotagrosdouli/DynNav/tree/main/contributions/27_Recoverability_Theory">C27 research proposal ↗</a>
          <a href="https://github.com/panagiotagrosdouli/DynNav/tree/main/docs/audits/C27_RECOVERABILITY_THEORY_REVIEW.md">Current evidence review ↗</a>
        </div>
      </article>
      {visible.length === 0 && <p className="empty-state">No contributions match these filters.</p>}
      <p className="explorer-boundary">
        The registry includes controlled smoke experiments; these demonstrate implementation behavior and reproducibility.
        They are not automatically real-world, Gazebo, or hardware evidence. C00 is the core hypothesis and is not a numbered registry track.
      </p>
    </section>
  );
}
