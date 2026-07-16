<div align="center">

# DynNav

## Risk-Aware Dynamic Navigation and Rerouting in Unknown Environments

**A modular research framework and interactive robotics laboratory for autonomous navigation under uncertainty, risk, limited recoverability, dynamic change, and mission-level constraints.**

[![CI](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/ci.yml/badge.svg)](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/ci.yml)
[![Streamlit](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/streamlit-dashboard.yml/badge.svg)](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/streamlit-dashboard.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![License](https://img.shields.io/badge/License-Apache--2.0-4C1.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-research%20prototype-orange)](#verified-status-and-evidence-boundaries)
[![Dashboard](https://img.shields.io/badge/Streamlit-interactive%20robotics%20lab-FF4B4B?logo=streamlit&logoColor=white)](app/dashboard.py)

[**English**](README.md) · [**Ελληνικά**](README_GREEK.md) · [Documentation](docs/README.md) · [Contribution feature catalog](docs/CONTRIBUTION_FEATURE_CATALOG.md) · [Contribution source index](contributions/CONTRIBUTIONS_README.md) · [Dashboard guide](app/README.md) · [Website](website/README.md)

</div>

<p align="center">
  <img src="assets/readme/dynnav_living_map.svg" alt="Conceptual DynNav navigation, uncertainty, planning, rerouting, and supervision pipeline" width="100%" />
</p>

<p align="center"><em>Conceptual DynNav system overview. The figure explains the intended information flow; it is not experimental evidence, a formal safety proof, or a hardware-validation claim.</em></p>

---

## What DynNav is

Autonomous navigation in an unknown or changing environment is not only a shortest-path problem. A robot must make decisions while its map may be incomplete, its state estimate uncertain, its sensors noisy, its communication link degraded, moving obstacles invalidate routes, and its future ability to recover from a decision remains unknown.

DynNav studies this broader decision problem through deterministic baselines, research prototypes, interactive contribution demonstrations, reproducible experiments, and evidence-oriented documentation. The core design principle is that every navigation decision should remain **auditable**: assumptions, parameters, paths, risks, uncertainty, supervisor actions, metrics, and limitations should be visible rather than hidden behind one final result.

> DynNav is research software. Synthetic experiments, passing tests, and dashboard graphics do not establish certified safety, production readiness, physical-robot reliability, or universal guarantees.

---

## Research question

> **How can an autonomous mobile robot dynamically plan and replan in a partially observed environment while explicitly accounting for uncertainty, risk, recoverability, resources, dynamic changes, security, human constraints, and mission-level safety actions?**

The repository decomposes this question into 26 interactive research contributions.

---

## What was built

```text
scenario, map, observation, or mission
        ↓
occupancy and belief representation
        ↓
uncertainty, risk, connectivity, resources, and recoverability
        ↓
geometric, learned, risk-aware, semantic, or resource-aware planning
        ↓
route monitoring, prediction, and online replanning
        ↓
supervisor: continue / caution / replan / recover / stop
        ↓
metrics, event logs, manifests, reports, and evidence audit
```

The repository includes:

- typed navigation and mission primitives;
- deterministic A* and Dijkstra baselines;
- learning-guided and risk-aware planning;
- uncertainty, belief, and calibration experiments;
- returnability, recoverability, and irreversibility metrics;
- finite-state safe-mode supervision;
- energy and connectivity feasibility analysis;
- next-best-view exploration;
- dynamic-obstacle prediction and route invalidation;
- multi-robot coordination and communication experiments;
- security, causal, semantic, learning, formal-method, and swarm extensions;
- an interactive multipage Streamlit robotics laboratory;
- experiment manifests, replay, reports, exports, Docker, tests, and CI validation.

---

## Interactive Robotics Lab

Install and launch:

```bash
python -m pip install -e ".[dashboard]"
streamlit run app/dashboard.py
```

The Streamlit app contains:

| Page | What you can do |
|---|---|
| **Home** | Understand the complete DynNav pipeline and open each laboratory. |
| **Robot Lab** | Play, pause, step, reset, inspect events, observe replanning, and export the rollout. |
| **Scenario Builder** | Configure maps, start/goal cells, obstacles, seeds, and export scenarios. |
| **Planner Arena** | Compare classical and risk-aware planners on the same world and metrics. |
| **Belief & Mapping Lab** | Change sensor noise and inspect prior/posterior occupancy, entropy, and information gain. |
| **Risk & Safety Lab** | Compose risk layers and test `NORMAL`, `CAUTION`, `REPLAN`, and `SAFE STOP` thresholds. |
| **Dynamic Obstacles** | Change motion models, prediction horizons, uncertainty envelopes, and route conflicts. |
| **Multi-Robot Lab** | Change robot count, communication range, packet loss, links, and fleet conflicts. |
| **Contribution Explorer** | Open C01–C26 and interact with each contribution's own controls and graphics. |
| **Experiment Studio** | Run single-seed, multi-seed, baseline-comparison, and sensitivity experiments. |
| **Results & Reports** | Filter, replay, compare, and export manifests, CSV, JSON, Markdown, and ZIP bundles. |
| **Documentation** | Browse curated repository Markdown inside the app. |
| **System Status** | Inspect dependencies, runtime capabilities, pages, and contribution renderers. |

The dashboard is a synthetic explanatory and experimental interface. It does not claim that every module has equal maturity or that all 26 contributions currently form one validated physical-robot stack.

---

# What every contribution does

Every contribution has a Streamlit renderer with its own controls, graphics, metrics, and interpretation. The detailed catalog is available in [`docs/CONTRIBUTION_FEATURE_CATALOG.md`](docs/CONTRIBUTION_FEATURE_CATALOG.md).

## Planning, uncertainty, and runtime safety

| ID | Contribution | What it does | Interactive features | Maturity |
|---|---|---|---|---|
| **C01** | Learned A* Search | Compares classical A* with a learned cost-to-go heuristic. | Grid/obstacle controls, heuristic influence, paths, expanded nodes, cost, runtime. | Research Prototype |
| **C02** | Uncertainty Estimation | Explores state-estimation uncertainty and whether confidence is calibrated against error. | Noise, uncertainty scale, confidence bands, calibration plots, error metrics. | Research Prototype |
| **C03** | Risk-Aware A* | Trades path length against expected, maximum, or tail-risk exposure. | Risk weight, risk field, competing routes, average/max risk, CVaR-style metrics. | Research Prototype |
| **C04** | Returnability and Recoverability | Measures whether entering a state preserves future escape and recovery options. | Bottlenecks, return paths, reachable recovery cells, escape options, irreversibility. | Research Prototype |
| **C05** | Safe-Mode Supervisor | Demonstrates a finite-state supervisor that continues, becomes cautious, replans, or stops. | Thresholds, hysteresis, persistence, cooldown, transition history, supervisor state. | Research Prototype |
| **C06** | Energy and Connectivity | Classifies mission feasibility under battery and communication constraints. | Battery reserve, route energy, link quality, recharge/relay requirements, verdict. | Research Prototype |
| **C07** | Safe Next-Best View | Selects exploration targets using information gain plus risk, connectivity, and returnability. | Candidate viewpoints, scoring weights, information gain, route risk, selected target. | Research Prototype |

## Security, people, coordination, and learning

| ID | Contribution | What it does | Interactive features | Maturity |
|---|---|---|---|---|
| **C08** | Security and Intrusion Detection | Detects anomalous or manipulated navigation observations. | Attack strength, detector threshold, anomaly history, alarms, delay, false positives. | Experimental |
| **C09** | Multi-Robot Coordination | Studies shared beliefs, communication, task allocation, and robot conflicts. | Robot count, range, packet loss, assignments, communication links, fleet metrics. | Experimental |
| **C10** | Human-Aware Navigation | Adds social costs and personal-space reasoning around people. | Human positions, comfort radius, social weight, alternative paths, proximity metrics. | Experimental |
| **C11** | Twin-Critic Reinforcement Learning | Visualizes actor–critic decisions and disagreement between two value estimators. | State/action controls, critic values, policy action, critic gap, reward indicators. | Experimental |
| **C12** | Diffusion Occupancy Prediction | Generates uncertain future occupancy predictions for dynamic scenes. | Forecast horizon, diffusion/noise controls, occupancy samples, uncertainty maps. | Experimental |
| **C13** | Latent World Model | Compresses observations and imagines future state rollouts in latent space. | Latent dimensions, rollout horizon, reconstruction, imagined trajectories, error. | Experimental |
| **C14** | Causal Risk Attribution | Decomposes aggregate navigation risk into structured causes and counterfactuals. | Causal factors, interventions, counterfactual settings, per-cause attribution. | Experimental |
| **C15** | Neuromorphic Sensing | Explores event-driven sensing where scene changes produce sparse events. | Motion, event threshold, temporal window, event map, event rate, sparsity. | Experimental |
| **C16** | Federated Navigation Learning | Simulates decentralized model updates without centralizing local robot data. | Client count, data shift, local rounds, aggregation, convergence, disagreement. | Experimental |
| **C17** | Semantic Topological Maps | Combines semantic regions with graph-based high-level navigation. | Semantic nodes, edges, route preferences, topology, selected semantic path. | Experimental |
| **C18** | Formal Safety Shields | Demonstrates runtime interventions inspired by barrier functions and temporal logic. | Nominal commands, safety boundaries, intervention threshold, constraint status. | Experimental |

## Mission reasoning, explanation, scene representation, and robustness

| ID | Contribution | What it does | Interactive features | Maturity |
|---|---|---|---|---|
| **C19** | Language Mission Planner | Converts natural-language instructions into explicit mission goals and constraints. | Mission text, extracted goals, priorities, forbidden areas, structured plan. | Documentation Concept |
| **C20** | Failure Explanation | Produces structured explanations from navigation events and failure evidence. | Failure type, evidence channels, event sequence, attributed cause, confidence. | Experimental |
| **C21** | PPO Navigation | Demonstrates policy-optimization behavior for navigation. | Reward weights, action probabilities, episode reward, learning curves. | Experimental |
| **C22** | Curriculum Reinforcement Learning | Studies staged task difficulty and policy progression. | Curriculum stage, difficulty, promotion threshold, success history, progression. | Experimental |
| **C23** | Gaussian Splatting Maps | Explores dense Gaussian scene representations for navigation context. | Gaussian count/scale, visibility, rendering, spatial density. | Documentation Concept |
| **C24** | NeRF Uncertainty | Examines uncertainty-aware neural implicit scene representations. | Observation coverage, sampling, field slices, uncertainty and confidence views. | Documentation Concept |
| **C25** | Adversarial Navigation Testing | Injects disturbances and measures navigation robustness degradation. | Attack type, perturbation strength, response, path deviation, failure rate. | Experimental |
| **C26** | Byzantine-Fault-Tolerant Swarm | Explores swarm consensus with faulty or malicious robot reports. | Swarm size, faulty nodes, trust threshold, reports, consensus, consensus error. | Experimental |

### How the contributions connect

```text
C01 learned guidance
       ↓
C02 uncertainty and calibration
       ↓
C03 risk-aware route selection ─────────┐
       ↓                                │
C04 returnability and recovery          │
       ↓                                │
C05 runtime supervision ◄───────────────┘
       ↓
C06 energy and connectivity
       ↓
C07 safe exploration
       ↓
C08–C26 security, people, multi-robot systems,
        prediction, learning, semantics, formal shields,
        explanation, robustness, and swarm consensus
```

This diagram is conceptual. It does not claim that all modules currently execute together as one certified end-to-end system.

---

## Verified status and evidence boundaries

| Capability | Maturity | Current evidence |
|---|---|---|
| Typed grid, pose, trajectory, and mission primitives | Implemented | Source tests and Python CI |
| A* and Dijkstra baselines | Implemented | Deterministic tests |
| Risk-aware grid planning | Implemented | Source and regression tests |
| Risk and uncertainty fields | Implemented / Experimental | Deterministic synthetic tests |
| Multipage Streamlit robotics lab | Implemented / Experimental | Dashboard smoke tests and headless startup CI |
| Scenario editing and planner comparison | Implemented / Experimental | Synthetic interactive workflows |
| Experiment manifests, replay, and exports | Implemented / Experimental | Deterministic session workflows |
| Learned heuristic search | Research Prototype | Controlled grid benchmarks and audits |
| Uncertainty calibration | Research Prototype | Synthetic uncertainty/error studies |
| Recoverability estimation | Research Prototype | Grid reachability heuristics and tests |
| Dynamic rerouting and cooldown | Research Prototype | Regression tests |
| Mission supervisor and safe mode | Research Prototype | Transition and threshold tests |
| Docker dashboard runtime | Implemented | Container entry point and health-check validation |
| ROS 2 / Nav2 integration | Planned / Prototype documentation | No production-ready integration claim |
| Gazebo validation | Planned | Not currently claimed |
| Physical-robot validation | Hardware Validation Required | No hardware evidence claimed |
| End-to-end formal safety | Not claimed | Outside current evidence |

Passing tests establishes consistency with implemented expectations; it does not prove real-world navigation safety, robustness, or generalization.

---

## Installation

```bash
git clone https://github.com/panagiotagrosdouli/DynNav.git
cd DynNav
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,dashboard]"
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,dashboard]"
```

Docker:

```bash
docker build -t dynnav-streamlit .
docker run --rm -p 8501:8501 dynnav-streamlit
```

---

## Main commands

| Purpose | Command |
|---|---|
| Full Python tests | `pytest` |
| Dashboard smoke tests | `pytest tests/test_streamlit_lab_smoke.py` |
| Validate dashboard structure | `python scripts/validate_streamlit_app.py` |
| Launch Streamlit | `streamlit run app/dashboard.py` |
| CI-style smoke run | `python scripts/run_all.py --config configs/default.yaml --smoke --out-dir results/ci_smoke` |
| Benchmark smoke run | `python scripts/run_benchmarks.py --config configs/default.yaml --smoke --out-dir results/ci_benchmarks` |
| Validate documented commands | `python scripts/validate_documented_commands.py --root .` |
| Generate research assets | `python scripts/generate_research_assets.py` |

---

## Evaluation protocol

Reportable runs should preserve:

```text
repository commit
configuration or manifest
random seed
exact command
runtime environment
raw output
aggregated result
figure or report generation step
```

Representative metrics include success rate, path length, expanded nodes, runtime, replans, route switches, average and maximum risk, tail risk, calibration error, recoverability, energy margin, connectivity margin, supervisor transitions, and stop requests.

See [`docs/EVALUATION_PROTOCOL.md`](docs/EVALUATION_PROTOCOL.md) and [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md).

---

## Repository structure

| Directory | Responsibility |
|---|---|
| [`app/`](app/) | Multipage Streamlit robotics laboratory |
| [`src/dynnav_dashboard/`](src/dynnav_dashboard/) | Dashboard simulation engine, registry, and C01–C26 renderers |
| [`contributions/`](contributions/) | Numbered research implementations, experiments, and module documentation |
| [`src/dynnav/`](src/dynnav/) | Installable core navigation package |
| [`configs/`](configs/) | Versioned experiment and benchmark inputs |
| [`scripts/`](scripts/) | Runners, validators, audits, and asset generation |
| [`tests/`](tests/) | Deterministic, regression, and dashboard smoke tests |
| [`docs/`](docs/) | Architecture, formulations, protocols, catalogs, and limitations |
| [`results/`](results/) | Generated metrics, reports, tables, and manifests |
| [`assets/`](assets/) | Figures, diagrams, screenshots, and media |
| [`website/`](website/) | Research landing page |

---

## Limitations

- Current evidence is dominated by deterministic and synthetic experiments.
- The Streamlit app is not ROS 2, Gazebo, or physical-robot execution.
- Contribution maturity ranges from research prototype to documentation concept.
- Calibration can degrade under distribution shift.
- Recoverability metrics are interpretable heuristics rather than universal certificates.
- Supervisor behavior depends on thresholds and scenario design.
- Neural methods can increase runtime even when reducing search effort.
- Dynamic-agent handling is not yet a fully validated probabilistic space-time stack.
- No repository output should be interpreted as a formal end-to-end safety guarantee.

---

## Roadmap

1. Strengthen contribution-level multi-seed evaluation and uncertainty intervals.
2. Expand time-aware dynamic-agent prediction and planning baselines.
3. Improve cross-page scenario sharing and synchronized replay.
4. Add reproducible screenshots, walkthrough GIFs, and public demo deployment.
5. Compile and validate ROS 2 / Nav2 integration.
6. Run traceable Gazebo experiments.
7. Conduct hardware validation with independent fail-safe mechanisms.
8. Generate publication tables and figures exclusively from versioned outputs.

---

## Responsible use

DynNav must not be used as a certified safety controller or as the sole navigation system for safety-critical deployment. Real-world users must provide independent validation, emergency handling, standards compliance, hardware-specific safety mechanisms, and operational supervision.

---

## Citation

Use [`CITATION.cff`](CITATION.cff) and report the exact commit, configuration, seed, contribution mode, checkpoint where applicable, and experiment command.

```bibtex
@software{dynnav,
  author  = {Grosdouli, Panagiota},
  title   = {DynNav: Risk-Aware Dynamic Navigation and Rerouting in Unknown Environments},
  url     = {https://github.com/panagiotagrosdouli/DynNav},
  note    = {Research software; cite the exact repository commit used}
}
```

---

## License

Licensed under the Apache License 2.0. See [`LICENSE`](LICENSE).
