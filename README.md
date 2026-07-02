# DynNav

**Dynamic Navigation and Rerouting in Unknown Environments**  
*An undergraduate independent research project on uncertainty-aware autonomous navigation with ROS 2, TurtleBot3/Nav2, learning-augmented planning, and risk-aware decision making.*

---

## One-sentence summary

DynNav studies how a mobile robot should plan, replan, and explore when the information it receives from perception, localization, mapping, or other agents is uncertain or unreliable.

---

## Why this project exists

Most navigation pipelines assume that the robot's map, pose estimate, sensor readings, and planning inputs are reliable enough to act on. In real environments this assumption often fails: localization can drift, perception can be ambiguous, maps can be incomplete, and other agents may share imperfect information.

DynNav was developed to explore a central research question:

> **How should an autonomous robot change its behaviour when it cannot fully trust the information it is using to plan?**

The project does not claim to solve this problem completely. Instead, it implements and evaluates a set of modular experimental components that investigate different failure modes of autonomous navigation under uncertainty.

---

## Current contribution upgrade log

The repository is being upgraded contribution by contribution. Each contribution is reviewed for scientific clarity, code quality, reproducibility, limitations, and whether it can be understood by a reader who has no prior context about DynNav.

| Contribution | Upgrade status | What was improved | Current evidence / result |
|---|---|---|---|
| C01 — Learned A* Heuristics | Upgraded | Added admissibility/consistency audit and scientific framing separating raw learned heuristics from admissible clipped heuristics. | Existing results show reduced node expansions in easier regimes while preserving path cost; new audit script measures heuristic overestimation and consistency violations. |
| C02 — Uncertainty Estimation and Calibration | Upgraded | Expanded README, added calibration utilities, added benchmark comparing raw uncertainty, global scale calibration, and quantile-bin calibration. | Existing results show uncertainty is informative but not fully calibrated; new code makes calibration measurable and repairable before uncertainty is passed to planners. |
| C03 — Belief-Space and Risk-Aware Planning | Upgraded | Rewrote README, added risk trade-off analyzer, CVaR/expected/max-risk metrics, path-length increase, and Pareto dominance benchmark. | Existing lambda sweep reports 42.75% risk reduction without path-length increase in the evaluated benchmark; new code audits whether risk reductions are meaningful trade-offs. |
| C04 — Irreversibility, Returnability, and Recoverability | Upgraded | Rewrote README, added recoverability metrics, path-level irreversibility summaries, bottleneck/escape-option analysis, and a recoverability benchmark. | Existing results show safe mode recovered feasibility from hard-threshold failures; new code measures how much recovery freedom remains along candidate routes. |
| C05 — Safe-Mode Navigation | Upgraded | Upgraded safe-mode controller with hysteresis, activation/recovery persistence, cooldown, emergency-stop handling, transition logging, and threshold benchmark. | Existing results show 66.7% total-risk reduction and 77.8% max-risk reduction with extra distance/cost; new benchmark audits safe-mode switching under noisy, hazardous, critical, and chattering risk traces. |
| C06 — Energy and Connectivity-Aware Planning | Upgraded | Added resource-feasibility utilities, mission verdicts, recharge/relay classification, feasibility margins, benchmark, and expanded README. | Existing demo compares energy-limited and connectivity-aware routing; new benchmark decides whether a mission is direct-feasible, needs recharge, needs relay, needs both, or is infeasible. |
| C07 — Returnability-Aware Next-Best-View Exploration | Upgraded | Added NBV scoring utilities, safe NBV objective, risk/returnability/connectivity terms, benchmark, scientific note, and expanded README. | New benchmark compares classic IG/cost NBV against safe NBV that avoids high-risk or low-returnability viewpoints even when information gain is high. |
| C08 — Security, Intrusion Detection, and Trust-Aware Response | Upgraded | Added IDS response policy, trust score, alert severity, planner mitigation actions, benchmark, scientific note, and expanded README. | Existing innovation monitor detects anomaly evidence; new response layer converts IDS outputs into WATCH/WARNING/CRITICAL states and navigation mitigations such as safe mode or emergency stop. |
| C09 — Multi-Robot Coordination under Uncertainty | Upgraded | Added team coordination metrics, conflict detection, risk-budget checks, belief-disagreement checks, benchmark, scientific note, and expanded README. | New benchmark evaluates team plans for vertex conflicts, edge-swap conflicts, risk-budget violations, belief disagreement, and overall team feasibility. |
| C10 — Human-Aware and Ethics-Guided Navigation | Upgraded | Added human-ethics policy layer, planner actions, speed/autonomy adaptation, operator-confirmation logic, benchmark, scientific note, and expanded README. | New benchmark maps no-go zones, slow zones, human proximity, low trust, and ambiguous language into auditable planner actions such as block path, slow down, announce, or ask operator. |
| C11 — VLM Navigation Agent with Goal Validation | Upgraded | Added VLM goal validator, accept/reject/ask-human decisions, hallucination checks, pixel/waypoint validation, benchmark, scientific note, and expanded README. | New benchmark validates VLM goals against confidence, allowed regions, forbidden semantics, image bounds, and waypoint plausibility before planner execution. |
| C12 — Diffusion Occupancy Maps and Probabilistic Risk Evaluation | Upgraded | Added risk-map evaluator, Brier/NLL scoring, high-risk precision/recall, CVaR conservatism gap, benchmark, scientific note, and expanded README. | New benchmark compares deterministic and probabilistic risk maps against future occupancy outcomes using proper scoring rules and high-risk detection metrics. |
| C13 — Latent World Model and Imagined Rollout Audit | Upgraded | Added rollout auditor, imagined-return/effort/recoverability metrics, irreversibility flags, benchmark, scientific note, and expanded README. | New benchmark audits imagined action sequences using return, action effort, terminal latent norm, recoverability proxy, and irreversibility-aware final score. |
| C14 — Causal Risk Attribution and Root-Cause Evaluation | Upgraded | Added attribution evaluator, known-cause synthetic failure cases, top-1 attribution accuracy, true-cause rank, counterfactual risk reduction, benchmark, scientific note, and expanded README. | New benchmark evaluates whether SCM root-cause rankings recover injected failure causes and whether counterfactual interventions reduce predicted collision risk. |
| C15 — Neuromorphic Sensing for Low-Latency Obstacle Detection | Upgraded | Added neuromorphic latency benchmark, event-rate metrics, false-negative reporting, frame-baseline comparison, scientific note, and expanded README. | New benchmark compares event/SNN obstacle detection against a frame-based baseline on slow, medium, and fast moving-obstacle sequences. |
| C16 — Federated Navigation Learning | Upgraded | Added federated evaluator, weighted/uniform aggregation comparison, DP/no-DP settings, fairness gap, communication-cost metrics, benchmark, scientific note, and expanded README. | New benchmark evaluates fleet-level trade-offs across generalization error, client fairness, differential privacy, aggregation strategy, and communication cost. |
| C17 — Topological Semantic Maps | Upgraded | Added semantic grounding evaluator, sparse graph planning benchmark, blocked-transition replanning test, scientific note, and expanded README. | New benchmark measures semantic grounding top-1/top-k accuracy and route success/cost before and after a semantic transition is blocked. |
| C18 — Formal Safety Shields | Upgraded | Added shield stress-test evaluator, shielded/unshielded comparison, STL robustness metrics, correction-cost metrics, benchmark, scientific note, and expanded README. | New benchmark evaluates violation count, minimum obstacle distance, intervention rate, correction cost, and goal-efficiency impact under obstacle stress tests. |

Planned direction: continue this process for all contributions, making every module more self-contained, scientifically precise, and reproducible.

---

## What is implemented

The repository contains a ROS 2 / Python research framework with modules for:

- learned heuristics for A* search,
- uncertainty estimation and calibration with EKF/UKF-style state representations,
- belief-space and risk-aware planning,
- irreversibility, returnability, and recoverability-aware planning,
- safe-mode navigation under uncertainty,
- energy and connectivity-aware resource planning,
- returnability-aware next-best-view exploration,
- cyber-physical intrusion detection and trust-aware response,
- multi-robot coordination and disagreement handling,
- human-aware and ethics-guided navigation,
- VLM-based semantic navigation with goal validation,
- diffusion-style future occupancy and probabilistic risk evaluation,
- latent world-model planning with imagined rollout audit,
- causal root-cause attribution for navigation failures,
- neuromorphic low-latency obstacle sensing,
- federated navigation learning across robot fleets,
- topological semantic mapping and grounding,
- formal safety shields using STL/CBF-style constraints,
- visual-odometry-based coverage replanning,
- adversarial and sensor-anomaly detection prototypes,
- interactive simulations and reproducible experiment scripts.

The project is intentionally modular: each module studies one research-oriented question and can be inspected, tested, or extended independently.

---

## Selected results

| Module | Question | Example result |
|---|---|---|
| Learned A* heuristic | Can a learned heuristic reduce search effort without changing the optimal path? | Node expansions reduced in benchmark runs while preserving the same path cost; an added admissibility audit now checks whether learned estimates overestimate true cost-to-go. |
| Uncertainty calibration | Can uncertainty estimates be trusted by a planner? | Existing results show uncertainty is rank-informative but miscalibrated; new calibration utilities evaluate and repair sigma values before planner use. |
| Risk-aware planning | Can a planner reduce risk without blindly increasing path cost? | Existing lambda sweep reports 42.75% risk reduction; new Pareto/CVaR benchmark separates average risk, tail risk, max risk, and distance cost. |
| Recoverability-aware planning | Can a robot avoid decisions that destroy future recovery freedom? | Existing hard-threshold planning succeeded in only 26.7% of cases while safe mode achieved 100%; new metrics quantify recoverability and irreversibility along paths. |
| Safe-mode navigation | When should the robot switch from normal behaviour to conservative behaviour? | Existing safe-mode result reduces total and peak risk; new finite-state controller benchmark measures transitions, replans, emergency stops, and chattering resistance. |
| Resource-aware planning | Can a robot complete the mission with enough battery and communication quality? | New resource-feasibility layer classifies routes as direct-feasible, recharge-needed, relay-needed, both, or infeasible. |
| Next-best-view exploration | Can a robot choose informative viewpoints without sacrificing recoverability? | New returnability-aware NBV score compares classic IG/cost selection against safer viewpoint selection using risk, connectivity, and returnability. |
| Security IDS | Can anomaly detection become a navigation response rather than only a diagnostic flag? | New IDS response policy maps innovation anomalies to trust score, alert severity, and planner mitigation. |
| Multi-robot coordination | Can a team plan remain conflict-free, risk-feasible, and belief-consistent? | New coordination metrics detect path conflicts, budget violations, and belief disagreement across robot plans. |
| Human-aware ethics | Can ethical context become an explicit planner decision? | New policy layer converts human proximity, no-go zones, low trust, and ambiguous commands into path blocking, slowdown, announcement, or operator confirmation. |
| VLM semantic navigation | Can foundation-model goals be used without blindly trusting hallucinated outputs? | New goal validator accepts, rejects, or requests human confirmation for VLM semantic goals before planner execution. |
| Diffusion occupancy | Are probabilistic future-occupancy maps useful as risk estimates? | New evaluator scores predicted risk maps with Brier score, NLL, high-risk precision/recall, and CVaR conservatism gap. |
| Latent world model | Can imagined futures be audited before execution? | New rollout audit scores candidate futures by imagined return, effort, latent familiarity, recoverability, and irreversibility. |
| Causal attribution | Can a failure diagnosis recover the true underlying cause? | New attribution benchmark measures top-1 accuracy, true-cause rank, and counterfactual risk reduction on injected-cause failure cases. |
| Neuromorphic sensing | Can event-based sensing reduce obstacle reaction latency? | New latency benchmark compares event/SNN detection with a frame baseline across moving-obstacle speeds and reports event-rate and false-negative metrics. |
| Federated learning | Can robot fleets learn together without sharing private raw data? | New trade-off benchmark compares aggregation/privacy settings using client MSE, fairness gap, communication cost, and DP metadata. |
| Topological semantic maps | Can semantic place graphs support language grounding and route repair? | New benchmark evaluates semantic grounding accuracy and graph replanning after blocked semantic transitions. |
| Formal safety shields | Can runtime formal filters reduce unsafe commands without excessive efficiency loss? | New shield stress test compares shielded and unshielded execution using violations, STL robustness, correction cost, and goal-distance metrics. |
| VO-based coverage replanning | Can visual-odometry uncertainty guide additional coverage? | Coverage improved after replanning in synthetic/robotics test settings. |
| Swarm consensus | Can robots reject unreliable shared plans? | Byzantine-style disagreement handling improves selected-plan reliability in simulation. |

Detailed numbers, scripts, and CSV logs are documented in the corresponding module folders and extended documentation.

---

## Repository guide for reviewers

If you are reviewing this project quickly, start here:

1. **Scientific overview:** [`docs/Abstract_and_Contributions.md`](docs/Abstract_and_Contributions.md)
2. **Claim-to-evidence map:** [`docs/CLAIMS_EVIDENCE.md`](docs/CLAIMS_EVIDENCE.md)
3. **Full technical README:** [`READMEbig.md`](READMEbig.md)
4. **Greek explanatory README:** [`README_GREEK.md`](README_GREEK.md)
5. **Modules:** [`contributions/`](contributions/)
6. **ROS 2 workspace:** [`ros2_ws/`](ros2_ws/)
7. **Dashboard / interactive simulations:** [`vercel_app/`](vercel_app/) and [`app/`](app/)

Suggested 10-minute reading path:

1. Read this README.
2. Open `docs/CLAIMS_EVIDENCE.md`.
3. Inspect the upgraded core modules from `contributions/01_learned_astar/` through `contributions/18_formal_safety_shields/`, and the safety / replanning modules.
4. Run one experiment script or inspect the logged CSV results.

---

## Quick start

```bash
git clone https://github.com/panagiotagrosdouli/DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments.git
cd DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run the contribution suite in quick mode
python run_all_contributions.py --quick

# Run tests
pytest contributions/tests/ -v
```

For ROS 2 experiments, the project was developed around **ROS 2 Humble**, **TurtleBot3**, **Gazebo**, **Nav2**, and **slam_toolbox**.

---

## Scope and limitations

This repository is a research-oriented framework, not a production navigation system. Some modules are more mature than others:

- core planning and uncertainty modules contain executable experiments,
- ROS 2 navigation components were developed and tested in TurtleBot3 / Gazebo settings,
- several advanced modules are prototypes designed to explore future research directions,
- cross-module integration is partial and should be treated as experimental.

The goal is not to present every module as a finished PhD-level result, but to document and progressively mature an independent research effort investigating how uncertainty, risk, safety, and learning interact in autonomous navigation.

---

## Research relevance

DynNav motivated my current research interest in **trustworthy robot perception** and **decision-making under unreliable information**. The main lesson from the project is that uncertainty should not remain a diagnostic value inside perception or localization modules. It should become actionable information for planning, replanning, and safe behaviour selection.

This connects directly to broader research questions in:

- robot perception,
- active perception,
- uncertainty-aware planning,
- visual-inertial navigation,
- safe autonomy,
- collaborative robotic systems.

---

## Author

**Panagiota Grosdouli**  
Electrical and Computer Engineering, Democritus University of Thrace  
Research interests: robot perception, uncertainty-aware autonomy, visual-inertial navigation, safe decision-making for robots.

---

## License

Licensed under the Apache License 2.0. See [`LICENSE`](LICENSE) for details.
