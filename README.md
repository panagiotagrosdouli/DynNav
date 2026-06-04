# DynNav

### Dynamic Navigation and Rerouting in Unknown Environments

*An uncertainty-aware, risk-sensitive autonomous navigation framework with formal safety constraints (STL + CBF filtering), learning-augmented planning, and twenty-six reproducible research contributions.*

---

**Repository.** [github.com/panagiotagrosdouli/DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments](https://github.com/panagiotagrosdouli/DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments)
**Live dashboard.** [dynnav-dynamic-navigation-rerouting-in-unknown-environments-fq.streamlit.app](https://dynnav-dynamic-navigation-rerouting-in-unknown-environments-fq.streamlit.app/)
**Latest release.** `v0.3-multi-robot-disagreement` (January 2026)
**License.** Apache-2.0
**Author.** Panagiota Grosdouli — Department of Electrical and Computer Engineering, Democritus University of Thrace (DUTH)

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![ROS 2](https://img.shields.io/badge/ROS%202-Humble-22314E?style=flat-square&logo=ros&logoColor=white)](https://docs.ros.org/en/humble/)
[![License](https://img.shields.io/badge/License-Apache%202.0-4CAF50?style=flat-square)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-pytest%20suite-brightgreen?style=flat-square&logo=pytest&logoColor=white)](tests/)
[![Contributions](https://img.shields.io/badge/Research%20Contributions-26-9C27B0?style=flat-square)](contributions/)
[![Dashboard](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://dynnav-dynamic-navigation-rerouting-in-unknown-environments-fq.streamlit.app/)

---

> **About this README.** This document is both the scientific report for DynNav *and* the navigation hub for the whole repository. It keeps the long-form technical narrative (sections 1–26) and additionally links each contribution to its implementation folder, its local README, its experiment scripts, its results, its dashboard simulation, and its related design documents under [`docs/`](docs/). Two short orientation sections — the [Documentation Hub](#documentation-hub) and [How to Explore This Repository](#how-to-explore-this-repository) — sit before the report so a new reader can find their way in; the deep sections then follow in their original order. Every path referenced below has been checked against the repository tree; where a folder is a documentation stub or a code home, that is stated explicitly rather than glossed over.

---

## Table of Contents

- [Documentation Hub](#documentation-hub)
- [How to Explore This Repository](#how-to-explore-this-repository)

1. [Overview](#1-overview)
2. [Scientific Motivation](#2-scientific-motivation)
3. [Research Questions](#3-research-questions)
4. [Problem Formulation](#4-problem-formulation)
5. [System Architecture](#5-system-architecture)
6. [Repository Layout](#6-repository-layout)
7. [The Twenty-Six Contributions](#7-the-twenty-six-contributions)
8. [The Research Dashboard](#8-the-research-dashboard)
9. [Technical Stack](#9-technical-stack)
10. [Installation](#10-installation)
11. [Running the Experiments](#11-running-the-experiments)
12. [Running the Dashboard](#12-running-the-dashboard)
13. [ROS 2 Integration](#13-ros-2-integration)
14. [Experimental Methodology](#14-experimental-methodology)
15. [Selected Results](#15-selected-results)
16. [Why a Streamlit Dashboard](#16-why-a-streamlit-dashboard)
17. [Theoretical Background](#17-theoretical-background)
18. [Engineering Challenges Encountered](#18-engineering-challenges-encountered)
19. [Deployment and Debugging Notes](#19-deployment-and-debugging-notes)
20. [Limitations and Honest Disclosures](#20-limitations-and-honest-disclosures)
21. [Research Significance](#21-research-significance)
22. [Future Research Directions](#22-future-research-directions)
23. [Citation](#23-citation)
24. [Author](#24-author)
25. [License](#25-license)
26. [Acknowledgements](#26-acknowledgements)

---

## Documentation Hub

DynNav's documentation is spread across several layers. This table is the master index — start here when looking for a particular document. Every link below points to a file that exists in the repository.

| Layer | Location | What it contains |
|---|---|---|
| **Master entry point** | `README.md` *(this file)* | Scientific report + navigation, contribution index, dependency notes |
| **Scientific framing** | [`docs/Abstract_and_Contributions.md`](docs/Abstract_and_Contributions.md) | Abstract, formal statement of contributions, scope |
| **Evidence map** | [`docs/CLAIMS_EVIDENCE.md`](docs/CLAIMS_EVIDENCE.md) | Each claim mapped to scripts, CSV logs and figures |
| **Long-form variants** | [`readme_full.md`](readme_full.md), [`docs/README-large info.md`](docs/README-large%20info.md) | Extended narrative versions of this document |
| **Docs index** | [`docs/README.md`](docs/README.md) | Index of the `docs/` directory |
| **Per-contribution READMEs** | `contributions/NN_module_name/README.md` | Research question, algorithm, integration points (per module) |
| **Contributions overview** | [`contributions/CONTRIBUTIONS_README.md`](contributions/CONTRIBUTIONS_README.md) | Index and conventions, with focus on modules 11–18 |

> **Note on deep-dive PDFs.** Earlier drafts of this README linked twenty-six `DynNav_C##_*_DeepDive.pdf` files at the repository root. Those PDFs are **not present on the current `main` branch**, so this README does not link to them. If they are re-added later, the per-contribution table in [section 7](#7-the-twenty-six-contributions) is the natural place to wire them back in (one column per module). Likewise, no `TECHNICAL_REPORT.md` exists on `main` at present; the long-form text lives in [`readme_full.md`](readme_full.md) and [`docs/README-large info.md`](docs/README-large%20info.md).

### Topic documents in `docs/`

These design, theory and results documents are central to the project and are cross-referenced from the relevant contributions in [section 7](#7-the-twenty-six-contributions). They are indexed here so none stays hidden.

| Document | Primarily related to |
|---|---|
| [`docs/Irreversibility_Aware_Navigation_New_Contribution.md`](docs/Irreversibility_Aware_Navigation_New_Contribution.md) | C04 (concept) |
| [`docs/README Irreversibility-Aware Navigation Planning.md`](docs/README%20Irreversibility-Aware%20Navigation%20Planning.md) | C04 (method) |
| [`docs/README_Irreversibility_Aware_Planning results.md`](docs/README_Irreversibility_Aware_Planning%20results.md) | C04 (results) |
| [`docs/Proposition_Irreversibility_vs_Risk_Weighting.md`](docs/Proposition_Irreversibility_vs_Risk_Weighting.md) | C03 ↔ C04 (theory) |
| [`docs/Returnability- & Irreversibility-Aware Frontier NBV.md`](docs/Returnability-%20&%20Irreversibility-Aware%20Frontier%20NBV.md) | C04 ↔ C07 |
| [`docs/Frontier-Restricted NBV Benchmark.md`](docs/Frontier-Restricted%20NBV%20Benchmark.md) | C07 (benchmark) |
| [`docs/Human Preference–Aware Risk Navigation.md`](docs/Human%20Preference%E2%80%93Aware%20Risk%20Navigation.md) | C10 |
| [`docs/README_trust_navigation.md`](docs/README_trust_navigation.md) | C10 (trust) |
| [`docs/Multi-Robot Safe Mode Navigation under Uncertainty.md`](docs/Multi-Robot%20Safe%20Mode%20Navigation%20under%20Uncertainty.md) | C05 ↔ C09 |
| [`docs/README_safe_mode_experiments.md`](docs/README_safe_mode_experiments.md) | C05 (results) |
| [`docs/README_Energy_Connectivity_SafeMode.md`](docs/README_Energy_Connectivity_SafeMode.md) | C05 ↔ C06 |
| [`docs/README_Innovation-Based_IDS_for_UKF_Sensor_Fusion.md`](docs/README_Innovation-Based_IDS_for_UKF_Sensor_Fusion.md) | C02 ↔ C08 |
| [`docs/README_TF_Attack_Aware_IDS.md`](docs/README_TF_Attack_Aware_IDS.md) | C08 ↔ C25 |
| [`docs/README Self-Healing Navigation & Language-Driven Safety.md`](docs/README%20Self-Healing%20Navigation%20&%20Language-Driven%20Safety.md) | C05 ↔ C19 |
| [`docs/SelfHealing_LanguageSafety_README.md`](docs/SelfHealing_LanguageSafety_README.md) | C05 ↔ C19 |
| [`docs/READMEResults: Self-Healing + Language Safety + Trust + Ethical Navigation.md`](docs/READMEResults:%20Self-Healing%20+%20Language%20Safety%20+%20Trust%20+%20Ethical%20Navigation.md) | C05, C10, C19 (results) |
| [`docs/README_LiDAR_SLAM_TurtleBot3_ROS2.md`](docs/README_LiDAR_SLAM_TurtleBot3_ROS2.md) | ROS 2 perception (see [section 13](#13-ros-2-integration)) |

---

## How to Explore This Repository

DynNav is a coherent research ecosystem rather than a set of isolated demos. Choose the path that matches your role; each path points into the deep sections below.

**Everyone — first ten minutes.** Read [Overview](#1-overview) → [System Architecture](#5-system-architecture) → [Installation §10.1](#101-dashboard-only-no-ros-no-gpu), then open the [live dashboard](https://dynnav-dynamic-navigation-rerouting-in-unknown-environments-fq.streamlit.app/) (or run it locally with `streamlit run app/dashboard.py`) and browse the *Contribution Simulations* page.

**Robotics researchers.** Read the architecture, then C02 (state estimation), C03 (belief-space and risk planning), C04 (irreversibility/returnability) and C07 (next-best-view). Pair each contribution's README with its `docs/` design note where one is listed in [section 7](#7-the-twenty-six-contributions).

**RL researchers.** Go to C21 (PPO), C22 (curriculum), C11 (twin-critic / VLM agent in the dashboard), then C16 (federated learning) and C13 (latent world model).

**ROS 2 / systems users.** Read [ROS 2 Integration](#13-ros-2-integration), then [`docs/README_LiDAR_SLAM_TurtleBot3_ROS2.md`](docs/README_LiDAR_SLAM_TurtleBot3_ROS2.md), and explore [`lidar_ros2/`](lidar_ros2/), [`dynamic_nav/`](dynamic_nav/), [`cybersecurity_ros2/`](cybersecurity_ros2/) and the workspace under [`ros2_ws/lidar_slam_tb3/`](ros2_ws/lidar_slam_tb3/).

**Safety researchers.** Read C18 (STL + CBF filtering) and C03 (CVaR planning) together — the risk maps feed the safety filter. Then C04 (irreversibility/returnability) and C05 (safe-mode FSM). Theory bridge: [`docs/Proposition_Irreversibility_vs_Risk_Weighting.md`](docs/Proposition_Irreversibility_vs_Risk_Weighting.md).

**Reviewers / thesis evaluators.** Read [`docs/Abstract_and_Contributions.md`](docs/Abstract_and_Contributions.md), then [`docs/CLAIMS_EVIDENCE.md`](docs/CLAIMS_EVIDENCE.md) to trace each claim to its evidence, then spot-check by running the cited scripts. The *Status* column in [section 7](#7-the-twenty-six-contributions) and the disclosures in [section 20](#20-limitations-and-honest-disclosures) state plainly what is implemented versus prototype.

**Suggested deep-reading order:** sections 1–9 of this report → *Contribution Simulations* in the dashboard → **C18 with C03** → **C04 with C07** → **C05, C10 and C19** → coordination layer **C09, C16, C26**.

---

## 1. Overview

DynNav is a research framework for **dynamic navigation and online rerouting in unknown environments** that treats uncertainty and risk as first-class quantities. The framework is organised around twenty-six self-contained research contributions spanning planning, state estimation, formal safety, reinforcement learning, foundation-model integration, federated learning, security, multi-robot coordination, and 3D perception. The contributions are developed under a unified problem formulation in which a mobile agent must reach a goal in a partially observed, possibly adversarial environment while respecting probabilistic safety and resource constraints.

The repository contains four coupled components:

1. A **library of twenty-six research modules** under [`contributions/`](contributions/). Modules C01–C10 keep their algorithm code and drivers in paired `code/` and `experiments/` subdirectories with a `results/` directory and a per-module `README.md`; modules C11–C26 expose a top-level module file (for example `formal_safety_shields.py`) plus a `README.md`, and some add an `experiments/` driver. The exact layout per module is given in [section 7](#7-the-twenty-six-contributions).
2. A **ROS 2 stack** organised into perception ([`lidar_ros2/`](lidar_ros2/), [`neural_uncertainty/`](neural_uncertainty/), [`photogrammetry_module/`](photogrammetry_module/), [`ig_explorer/`](ig_explorer/)), navigation ([`dynamic_nav/`](dynamic_nav/), [`core/`](core/)) and security ([`cybersecurity_ros2/`](cybersecurity_ros2/)) packages, with a TurtleBot3 workspace under [`ros2_ws/lidar_slam_tb3/`](ros2_ws/lidar_slam_tb3/).
3. A **browser-based research dashboard** built with Streamlit that reproduces every contribution as a synthetic-data simulation requiring no robot, no ROS installation, and no GPU.
4. A **documentation layer**: per-contribution READMEs, the topic documents under [`docs/`](docs/), and the scientific framing in [`docs/Abstract_and_Contributions.md`](docs/Abstract_and_Contributions.md) and [`docs/CLAIMS_EVIDENCE.md`](docs/CLAIMS_EVIDENCE.md).

The framework is positioned as a research artefact, not a deployable product. Several contributions are fully implemented and benchmarked, others are prototypes, and the cross-stack integration is partial. These categories are made explicit throughout this document — see in particular the *Status* column in [section 7](#7-the-twenty-six-contributions) and the disclosures in [section 20](#20-limitations-and-honest-disclosures).

---

## 2. Scientific Motivation

Autonomous navigation has matured in controlled, well-mapped settings. It remains brittle in environments where the map is incomplete or evolving, where perception is noisy, and where rare worst-case events — sensor spoofing, dynamic obstacles, dead-end traps, low battery, communication loss — dominate the failure distribution. Three observations frame the project.

**Average-case planning is insufficient.** Most classical planners optimise expected cost. In safety-critical settings the tail of the cost distribution matters more than the mean. A path that is short on average but exposes the robot to a five-percent chance of collision is unacceptable in many deployments. This motivates the use of coherent tail-risk measures such as Conditional Value-at-Risk (CVaR) inside the planning objective.

**Uncertainty must be first-class.** Downstream decisions — whether to slow down, replan, abort, or hand off to a human supervisor — are only as good as the uncertainty estimates they consume. The framework therefore treats belief-space estimation, ensemble disagreement, NeRF/3DGS uncertainty fields, and diffusion-based occupancy predictions as primary signals rather than diagnostics.

**Safety cannot rely on the policy alone.** Learning-based policies improve average performance but offer no formal guarantees. The framework couples learned components to formal safety filters — Control Barrier Functions (CBFs) and Signal Temporal Logic (STL) shields — so that the output of any upstream controller, classical or neural, is minimally projected onto the safe set before reaching the actuators. The framework provides *formal safety constraints and STL/CBF filtering at the action level*; it does not claim end-to-end formal verification of the full stack.

---

## 3. Research Questions

The contributions are organised around the following questions.

1. *How should risk be encoded inside the planner so that the resulting trajectories are robust to the worst α-fraction of perception outcomes?*
2. *How can learned heuristics or learned dynamics models accelerate or improve planning without sacrificing the strict guarantees of classical planners?*
3. *What is the minimal architectural commitment under which a learned policy can be composed with a formal safety filter so that safety is preserved by construction?*
4. *How should mission-level intent — natural language or structured operator commands — be compiled into provably executable, returnable plans?*
5. *Under what assumptions can a multi-robot swarm reach consensus on navigation decisions when an unknown subset of its members is Byzantine?*
6. *How should a robot allocate its perception budget — frontier viewpoints, NeRF queries — to maximise the reduction of decision-relevant uncertainty rather than total entropy?*
7. *Can a research-grade simulation environment, deliberately decoupled from ROS and from physical hardware, accelerate the pace of methodological iteration in this space without compromising the eventual transfer to a real platform?*

---

## 4. Problem Formulation

Let an agent occupy state `s_t` in a partially observed environment with hidden parameters `θ`. At each step it issues an action `a_t` and receives an observation `o_t`. The agent maintains a belief `b_t = p(s_t, θ | o_{1:t}, a_{1:t-1})`. A mission specifies a goal region `G` and a set of safety constraints `Φ` that may be expressed as:

- forward invariance of a safe set `S_safe` (CBF formulation),
- temporal-logic specifications `φ ∈ STL`,
- bounded tail risk `CVaR_α[c_t] ≤ κ` over a step-wise risk signal `c_t`.

The planner seeks a policy `π` that maximises an expected return while satisfying `Φ` and an *additional returnability constraint*: for every reachable belief along the executed trajectory there must exist a feasible plan back to a designated safe state (typically the base station) under the residual energy and connectivity budget. This last constraint distinguishes the framework's notion of safety from the standard collision-avoidance formulation.

---

## 5. System Architecture

The framework is layered. Each layer exposes a typed interface to the layer above and accepts uncertainty estimates from the layer below.

```
+----------------------------------------------------------------+
|  Foundation Models                                              |
|     VLM Navigation Agent (C11)  |  LLM Mission Planner (C19)    |
|     Multimodal Failure Explainer (C20)                          |
+----------------------------------------------------------------+
|  Learning Layer                                                 |
|     Learned A* (C01)  |  PPO (C21)  |  Curriculum RL (C22)      |
|     Federated Nav Learning (C16)  |  Latent World Model (C13)   |
+----------------------------------------------------------------+
|  Safety Layer                                                   |
|     STL + CBF Filtering (C18)  |  Safe-Mode FSM (C05)           |
|     Irreversibility / Returnability (C04)                       |
+----------------------------------------------------------------+
|  Coordination Layer                                             |
|     Multi-Robot Allocation (C09)  |  Swarm BFT Consensus (C26)  |
|     Human-Aware Ethical Zones (C10)                             |
+----------------------------------------------------------------+
|  Planning Core                                                  |
|     Belief-Space / CVaR Risk Planning (C03)                     |
|     Next-Best-View Exploration (C07)                            |
|     Topological Semantic Maps (C17)                             |
|     Energy and Connectivity Constraints (C06)                   |
+----------------------------------------------------------------+
|  Perception Layer                                               |
|     EKF / UKF (C02)  |  Diffusion Occupancy (C12)               |
|     3D Gaussian Splatting Mapper (C23)                          |
|     NeRF Uncertainty Maps (C24)                                 |
|     Neuromorphic Sensing (C15)                                  |
+----------------------------------------------------------------+
|  Security Layer                                                 |
|     IDS chi-square / CUSUM (C08)                                |
|     Adversarial Attack Simulator (C25)                          |
|     Causal Risk Attribution (C14)                               |
+----------------------------------------------------------------+
|  ROS 2 Substrate                                                |
|     ROS 2 Humble  |  Nav2  |  slam_toolbox  |  TurtleBot3       |
+----------------------------------------------------------------+
```

Data flows upward: raw sensors → security filter → perception → planning → safety filter → actuators. Uncertainty estimates flow with the data; mission intent flows downward; the safe-mode FSM observes the entire stack and gates its outputs. How the contributions compose across these layers is set out explicitly in the [Contribution Relationships](#contribution-relationships) subsection inside [section 7](#7-the-twenty-six-contributions).

The layers map onto concrete code: the **Planning Core** lives in [`core/`](core/) and [`dynamic_nav/`](dynamic_nav/); **Perception** in [`lidar_ros2/`](lidar_ros2/), [`neural_uncertainty/`](neural_uncertainty/) and [`photogrammetry_module/`](photogrammetry_module/); the **Security Layer** in [`cybersecurity_ros2/`](cybersecurity_ros2/); and exploration in [`ig_explorer/`](ig_explorer/).

---

## 6. Repository Layout

The top-level structure mirrors the architecture above. Folder names are reproduced verbatim from the repository, and only directories that exist on the current branch are listed.

```
DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments/
│
├── contributions/                # 26 numbered research modules (+ a few legacy/variant dirs)
│   ├── CONTRIBUTIONS_README.md   #   conventions + index (focus on modules 11–18)
│   ├── 01_learned_astar/         #   C01–C10: code/ + experiments/ + results/ + README.md
│   ├── 02_uncertainty_estimation/#   C02 canonical documentation README (stub)
│   ├── 02_uncertainty_calibration/  # C02 working code + experiments + results
│   ├── 03_belief_risk_planning/
│   ├── 04_irreversibility_returnability/
│   ├── 05_safe_mode_navigation/
│   ├── 06_energy_connectivity/
│   ├── 07_next_best_view/        #   C07 canonical documentation README (stub)
│   ├── 07_nbv_exploration/       #   C07 working code + experiments + results
│   ├── 08_security_ids/
│   ├── 09_multi_robot/
│   ├── 10_human_language_ethics/
│   ├── 11_vlm_navigation_agent/  #   C11–C26: top-level module .py + README.md (+ experiments/)
│   ├── 12_diffusion_occupancy/
│   ├── …                          #   (through 26_swarm_consensus/)
│   ├── 26_swarm_consensus/
│   ├── hybrid_learned_astar/     #   legacy / alternate planner variant
│   ├── learned_uncertainty_astar/#   legacy / alternate planner variant
│   ├── hybrid_planner/           #   legacy / alternate planner variant
│   ├── realtime_replanning/      #   legacy / alternate variant
│   ├── ablation_study/  benchmarking/  _unsorted/   # auxiliary experiment dirs
│   └── tests/                    #   pytest suite covering the contribution modules
│
├── core/                         # planner cores (A*, D*, belief search)
├── dynamic_nav/                  # closed-loop navigation stack
├── nav_research/                 # Python package (importable nav_research.*)
├── modules/                      # standalone library modules
├── generators/                   # synthetic scenario generators
├── ig_explorer/                  # information-gain exploration node
├── neural_uncertainty/           # neural uncertainty estimation
├── photogrammetry_module/        # photogrammetry integration
│
├── lidar_ros2/                   # ROS 2 LiDAR + SLAM packages and launch files
├── cybersecurity_ros2/nodes/     # ROS 2 IDS / cyber-physical nodes (C08)
├── ros2/                         # additional ROS 2 packages
├── ros2_ws/lidar_slam_tb3/       # TurtleBot3 workspace
├── launch/                       # ROS 2 launch files
│
├── app/                          # Streamlit dashboard entry point + pages
│   ├── dashboard.py              #   dashboard home
│   └── pages/                    #   1_Architecture … 6_Contribution_Simulations
├── src/dynnav_dashboard/         # dashboard package
│   └── contributions/cNN_*.py    #   one interactive simulation per contribution (C01–C26)
├── analysis/                     # post-hoc analysis scripts (incl. analysis/dashboard.py)
│
├── code_scripts/  scripts/  tools/  utils/   # utility and one-off scripts, shared helpers
├── tests/                        # repo-wide pytest suite
├── test/                         # ROS 2 ament_python test stubs
│
├── data/plots/                   # generated experiment plots
├── data_curriculum/              # curriculum-RL data (C22)
├── datasets/                     # raw and processed datasets
├── figures/                      # figures used in reports
├── results/                      # consolidated result artefacts
├── research_experiments/  research_results/  # standalone runs and archives
├── resource/                     # ROS 2 ament resource markers
├── config/  configs/             # runtime and experiment configuration
├── docs/                         # extended documentation (see Documentation Hub)
│
├── logs_ablation/  logs_benchmark/  logs_calibration/  logs_calibration_ensemble/
├── logs_ood/  logs_real_world/  log/          # run logs by category
│
├── build/  install/              # colcon build artefacts (reproducible; safe to delete)
├── cpp_extension/                # C/C++ extension modules
├── nav_research.egg-info/        # Python packaging metadata
│
├── README.md                     # this file
├── readme_full.md                # extended narrative variant
├── CITATION.cff                  # Citation File Format metadata
├── LICENSE                       # Apache-2.0
├── pytest.ini                    # pytest configuration
├── setup.py  setup.cfg           # nav_research package metadata
├── requirements.txt              # dashboard runtime (see §10)
└── ethical_zones.json            # ethical no-go zone definitions (C10)
```

**On the paired folders for C02 and C07.** The repository contains two directories for each of these contributions, and they are complementary rather than duplicates:

- `02_uncertainty_estimation/` holds the **canonical documentation README** for C02 (overview, research question, algorithm). `02_uncertainty_calibration/` holds the **working code, models, experiments and results** (drift-aware uncertainty, calibration-aware grids, trained `.pt`/`.npz` models). Read the README in the former; run the code in the latter.
- `07_next_best_view/` holds the **canonical documentation README** for C07. `07_nbv_exploration/` holds the **working code, experiments and results** (frontier sampling, information-gain planner, returnability-aware NBV).

The other non-numbered directories under `contributions/` (`hybrid_learned_astar/`, `learned_uncertainty_astar/`, `hybrid_planner/`, `realtime_replanning/`, `ablation_study/`, `benchmarking/`, `_unsorted/`) are legacy or alternate variants and auxiliary experiment scratch space. They are kept for provenance but are **not** part of the canonical twenty-six; the numbered modules are authoritative.

A note on dependencies: `requirements.txt` currently lists only the dashboard's runtime dependencies (Streamlit, NumPy, pandas, Plotly, Matplotlib, networkx). The full research stack uses additional packages (PyTorch, transformers, diffusers, Open3D, ROS 2) introduced in [section 10](#10-installation).

---

## 7. The Twenty-Six Contributions

Each contribution has a per-module `README.md` covering its research question, algorithm and integration points. Modules **C01–C10** keep their algorithm code in a `code/` subdirectory, their drivers in `experiments/`, and their CSV/plots in `results/`. Modules **C11–C26** expose a top-level module file (for example `formal_safety_shields.py`) and a `README.md`; several add an `experiments/` driver. The interactive simulation for every contribution lives in [`src/dynnav_dashboard/contributions/`](src/dynnav_dashboard/contributions/) and is reachable from the dashboard's *Contribution Simulations* page.

The tables below act as a **research navigation index**: each row links the local README, the implementation, a representative experiment (where one exists as a script), the results location, the dashboard page, and the related `docs/` documents, and names the connected contributions. *Status* is one of **Implemented** (runs end-to-end and logs metrics) or **Prototype** (algorithmic core present, but at least one external dependency — PyTorch, a local LLM, a differentiable renderer — is needed to exercise the full pipeline; a synthetic fallback is provided where applicable).

### Core Planning and Uncertainty (C01–C03)

| Code | Module | README | Implementation | Representative experiment | Results | Dashboard | Status |
|---|---|---|---|---|---|---|---|
| C01 | Learned A\* Heuristics | [README](contributions/01_learned_astar/README.md) | [`01_learned_astar/code/`](contributions/01_learned_astar/code/) | [`experiments/eval_astar_learned.py`](contributions/01_learned_astar/experiments/eval_astar_learned.py) | [`results/`](contributions/01_learned_astar/results/) | [`c01_learned_astar.py`](src/dynnav_dashboard/contributions/c01_learned_astar.py) | Implemented |
| C02 | Uncertainty Estimation (EKF / UKF) | [README](contributions/02_uncertainty_estimation/README.md) | [`02_uncertainty_calibration/code/`](contributions/02_uncertainty_calibration/code/) | [`02_uncertainty_calibration/experiments/`](contributions/02_uncertainty_calibration/experiments/) | [`02_uncertainty_calibration/results/`](contributions/02_uncertainty_calibration/results/) | [`c02_ekf_ukf.py`](src/dynnav_dashboard/contributions/c02_ekf_ukf.py) | Implemented |
| C03 | Belief-Space and Risk Planning (CVaR A\*) | [README](contributions/03_belief_risk_planning/README.md) | [`03_belief_risk_planning/code/`](contributions/03_belief_risk_planning/code/) | [`experiments/lambda_sweep_risk_length_demo.py`](contributions/03_belief_risk_planning/experiments/lambda_sweep_risk_length_demo.py) | [`results/`](contributions/03_belief_risk_planning/results/) | [`c03_cvar_astar.py`](src/dynnav_dashboard/contributions/c03_cvar_astar.py) | Implemented |

**Related documents and links.** C02 is documented in [`02_uncertainty_estimation/README.md`](contributions/02_uncertainty_estimation/README.md) with code under `02_uncertainty_calibration/` (see [the paired-folder note in §6](#6-repository-layout)); innovation-based monitoring of the UKF fusion: [`docs/README_Innovation-Based_IDS_for_UKF_Sensor_Fusion.md`](docs/README_Innovation-Based_IDS_for_UKF_Sensor_Fusion.md). The formal relationship between irreversibility and risk weighting (C03 ↔ C04) is treated in [`docs/Proposition_Irreversibility_vs_Risk_Weighting.md`](docs/Proposition_Irreversibility_vs_Risk_Weighting.md). **Connected:** **C03 → C18** (risk maps feed the safety filter), **C03 ↔ C04** (soft risk penalties vs hard returnability constraints), **C12 → C03** (predicted occupancy becomes a CVaR input).

### Safety and Robustness (C04–C05, C08, C18)

| Code | Module | README | Implementation | Representative experiment | Results | Dashboard | Status |
|---|---|---|---|---|---|---|---|
| C04 | Irreversibility and Returnability | [README](contributions/04_irreversibility_returnability/README.md) | [`04_irreversibility_returnability/code/`](contributions/04_irreversibility_returnability/code/) | [`experiments/run_irreversibility_tau_sweep.py`](contributions/04_irreversibility_returnability/experiments/run_irreversibility_tau_sweep.py) | [`results/`](contributions/04_irreversibility_returnability/results/) | [`c04_returnability.py`](src/dynnav_dashboard/contributions/c04_returnability.py) | Implemented |
| C05 | Safe-Mode Navigation | [README](contributions/05_safe_mode_navigation/README.md) | [`05_safe_mode_navigation/code/`](contributions/05_safe_mode_navigation/code/) | [`experiments/run_adaptive_tau_safe_mode_demo.py`](contributions/05_safe_mode_navigation/experiments/run_adaptive_tau_safe_mode_demo.py) | [`results/`](contributions/05_safe_mode_navigation/results/) | [`c05_safe_mode_fsm.py`](src/dynnav_dashboard/contributions/c05_safe_mode_fsm.py) | Implemented |
| C08 | Security and Intrusion Detection | [README](contributions/08_security_ids/README.md) | [`08_security_ids/code/`](contributions/08_security_ids/code/) | [`experiments/eval_ids_sweep.py`](contributions/08_security_ids/experiments/eval_ids_sweep.py) | [`results/`](contributions/08_security_ids/results/) | [`c08_security_ids.py`](src/dynnav_dashboard/contributions/c08_security_ids.py) | Implemented |
| C18 | Formal Safety Shields (STL + CBF) | [README](contributions/18_formal_safety_shields/README.md) | [`18_formal_safety_shields/formal_safety_shields.py`](contributions/18_formal_safety_shields/formal_safety_shields.py) | [`experiments/eval_safety_shields.py`](contributions/18_formal_safety_shields/experiments/eval_safety_shields.py) | inline / printed metrics | [`c18_cbf_stl_shields.py`](src/dynnav_dashboard/contributions/c18_cbf_stl_shields.py) | Implemented |

**Related documents (C04).** This is the most heavily documented contribution. Read, in order: [`docs/Irreversibility_Aware_Navigation_New_Contribution.md`](docs/Irreversibility_Aware_Navigation_New_Contribution.md) (concept), [`docs/README Irreversibility-Aware Navigation Planning.md`](docs/README%20Irreversibility-Aware%20Navigation%20Planning.md) (method), [`docs/README_Irreversibility_Aware_Planning results.md`](docs/README_Irreversibility_Aware_Planning%20results.md) (results), and [`docs/Returnability- & Irreversibility-Aware Frontier NBV.md`](docs/Returnability-%20&%20Irreversibility-Aware%20Frontier%20NBV.md) (the C04 ↔ C07 bridge).

**Related documents (C05).** Safe-mode experiments: [`docs/README_safe_mode_experiments.md`](docs/README_safe_mode_experiments.md); multi-robot extension: [`docs/Multi-Robot Safe Mode Navigation under Uncertainty.md`](docs/Multi-Robot%20Safe%20Mode%20Navigation%20under%20Uncertainty.md); energy-coupled safe mode: [`docs/README_Energy_Connectivity_SafeMode.md`](docs/README_Energy_Connectivity_SafeMode.md); self-healing / language-driven safety: [`docs/README Self-Healing Navigation & Language-Driven Safety.md`](docs/README%20Self-Healing%20Navigation%20&%20Language-Driven%20Safety.md) and [`docs/SelfHealing_LanguageSafety_README.md`](docs/SelfHealing_LanguageSafety_README.md).

**Related documents (C08).** Transform-attack-aware IDS: [`docs/README_TF_Attack_Aware_IDS.md`](docs/README_TF_Attack_Aware_IDS.md); innovation-based IDS over UKF fusion: [`docs/README_Innovation-Based_IDS_for_UKF_Sensor_Fusion.md`](docs/README_Innovation-Based_IDS_for_UKF_Sensor_Fusion.md). ROS 2 nodes live under [`cybersecurity_ros2/`](cybersecurity_ros2/).

**Connected contributions (safety layer).** **C03 → C18** (CVaR risk maps parameterise the CBF), **C04 → C05** (irreversibility/returnability raises a feasibility signal that triggers safe mode), **C05** supervises C03/C04/C18 at runtime, **C08 ← C02** (consumes UKF innovations), **C08 ↔ C25** (adversarial attacks exercise the IDS).

### Resource and Exploration (C06–C07)

| Code | Module | README | Implementation | Representative experiment | Results | Dashboard | Status |
|---|---|---|---|---|---|---|---|
| C06 | Energy and Connectivity Constraints | [README](contributions/06_energy_connectivity/README.md) | [`06_energy_connectivity/code/`](contributions/06_energy_connectivity/code/) | [`experiments/run_energy_connectivity_joint_sweep.py`](contributions/06_energy_connectivity/experiments/run_energy_connectivity_joint_sweep.py) | [`results/`](contributions/06_energy_connectivity/results/) | [`c06_energy_connectivity.py`](src/dynnav_dashboard/contributions/c06_energy_connectivity.py) | Implemented |
| C07 | Next-Best-View Exploration | [README](contributions/07_next_best_view/README.md) | [`07_nbv_exploration/code/`](contributions/07_nbv_exploration/code/) | [`07_nbv_exploration/experiments/run_nbv_random_vs_frontier_benchmark.py`](contributions/07_nbv_exploration/experiments/run_nbv_random_vs_frontier_benchmark.py) | [`07_nbv_exploration/results/`](contributions/07_nbv_exploration/results/) | [`c07_next_best_view.py`](src/dynnav_dashboard/contributions/c07_next_best_view.py) | Implemented |

**Related documents (C06–C07).** NBV benchmark methodology: [`docs/Frontier-Restricted NBV Benchmark.md`](docs/Frontier-Restricted%20NBV%20Benchmark.md); the returnability-aware formulation shared with C04: [`docs/Returnability- & Irreversibility-Aware Frontier NBV.md`](docs/Returnability-%20&%20Irreversibility-Aware%20Frontier%20NBV.md); energy-coupled safe mode: [`docs/README_Energy_Connectivity_SafeMode.md`](docs/README_Energy_Connectivity_SafeMode.md). The exploration engine also exists as a node in [`ig_explorer/`](ig_explorer/). As with C02, C07's documentation README and working code live in two folders ([see §6](#6-repository-layout)). **Connected:** **C07 ← C04** (returnability scoring), **C07 ↔ C24** (NeRF uncertainty informs view selection), **C07 ↔ C23** (3D-GS frontiers feed exploration), **C06 ↔ C05** (energy triggers safe mode).

### Multi-Robot and Human (C09–C10)

| Code | Module | README | Implementation | Representative experiment | Results | Dashboard | Status |
|---|---|---|---|---|---|---|---|
| C09 | Multi-Robot Coordination | [README](contributions/09_multi_robot/README.md) | [`09_multi_robot/code/`](contributions/09_multi_robot/code/) | [`experiments/run_multi_robot_risk_experiment.py`](contributions/09_multi_robot/experiments/run_multi_robot_risk_experiment.py) | [`results/`](contributions/09_multi_robot/results/) | [`c09_multi_robot.py`](src/dynnav_dashboard/contributions/c09_multi_robot.py) | Implemented |
| C10 | Human-Aware Navigation and Ethical Zones | [README](contributions/10_human_language_ethics/README.md) | [`10_human_language_ethics/code/`](contributions/10_human_language_ethics/code/) | inline driver | [`results/`](contributions/10_human_language_ethics/results/) | [`c10_human_aware.py`](src/dynnav_dashboard/contributions/c10_human_aware.py) | Implemented |

**Related documents (C09–C10).** Human-preference risk navigation: [`docs/Human Preference–Aware Risk Navigation.md`](docs/Human%20Preference%E2%80%93Aware%20Risk%20Navigation.md); trust modelling: [`docs/README_trust_navigation.md`](docs/README_trust_navigation.md); multi-robot safe mode: [`docs/Multi-Robot Safe Mode Navigation under Uncertainty.md`](docs/Multi-Robot%20Safe%20Mode%20Navigation%20under%20Uncertainty.md); combined results: [`docs/READMEResults: Self-Healing + Language Safety + Trust + Ethical Navigation.md`](docs/READMEResults:%20Self-Healing%20+%20Language%20Safety%20+%20Trust%20+%20Ethical%20Navigation.md). Ethical zones are defined in [`ethical_zones.json`](ethical_zones.json). **Connected:** **C09 ↔ C26** (consensus over allocated plans), **C10 ← C19** (mission language → ethical constraints), **C09 ← C05** (per-robot safe mode).

### Foundation Models (C11, C19–C20)

| Code | Module | README | Implementation | Representative experiment | Dashboard | Status |
|---|---|---|---|---|---|---|
| C11 | VLM Navigation Agent | [README](contributions/11_vlm_navigation_agent/README.md) | [`11_vlm_navigation_agent/vlm_planner.py`](contributions/11_vlm_navigation_agent/vlm_planner.py) | [`experiments/eval_vlm_planner.py`](contributions/11_vlm_navigation_agent/experiments/eval_vlm_planner.py) | [`c11_twin_critic_rl.py`](src/dynnav_dashboard/contributions/c11_twin_critic_rl.py) | Prototype (needs `ollama`/HF) |
| C19 | LLM Mission Planner | [README](contributions/19_llm_mission_planner/README.md) | [`19_llm_mission_planner/llm_mission_planner.py`](contributions/19_llm_mission_planner/llm_mission_planner.py) | inline driver | [`c19_llm_planner.py`](src/dynnav_dashboard/contributions/c19_llm_planner.py) | Prototype (rule-based fallback + LLM hook) |
| C20 | Multimodal Failure Explainer | [README](contributions/20_multimodal_failure_explainer/README.md) | [`20_multimodal_failure_explainer/multimodal_failure_explainer.py`](contributions/20_multimodal_failure_explainer/multimodal_failure_explainer.py) | inline driver | [`c20_failure_explainer.py`](src/dynnav_dashboard/contributions/c20_failure_explainer.py) | Prototype |

**Related documents (C19–C20).** Language-driven safety and self-healing: [`docs/README Self-Healing Navigation & Language-Driven Safety.md`](docs/README%20Self-Healing%20Navigation%20&%20Language-Driven%20Safety.md), [`docs/SelfHealing_LanguageSafety_README.md`](docs/SelfHealing_LanguageSafety_README.md). **Connected:** **C19 → C10** (mission → ethical zones), **C19 → C05** (language-triggered self-healing), **C20 ← C14** (SCM root causes feed the explainer). **Note:** C11/C19/C20 require an external LLM/VLM (e.g. `ollama`, `transformers`); without one they fall back to deterministic stubs — see [section 20](#20-limitations-and-honest-disclosures).

### Probabilistic and Generative (C12–C13)

| Code | Module | README | Implementation | Representative experiment | Dashboard | Status |
|---|---|---|---|---|---|---|
| C12 | Diffusion Occupancy Maps | [README](contributions/12_diffusion_occupancy/README.md) | [`12_diffusion_occupancy/diffusion_occupancy.py`](contributions/12_diffusion_occupancy/diffusion_occupancy.py) | [`experiments/eval_diffusion_occupancy.py`](contributions/12_diffusion_occupancy/experiments/eval_diffusion_occupancy.py) | [`c12_diffusion_occupancy.py`](src/dynnav_dashboard/contributions/c12_diffusion_occupancy.py) | Implemented |
| C13 | Latent World Model (Dreamer-style RSSM) | [README](contributions/13_latent_world_model/README.md) | [`13_latent_world_model/latent_world_model.py`](contributions/13_latent_world_model/latent_world_model.py) | inline driver | [`c13_world_model.py`](src/dynnav_dashboard/contributions/c13_world_model.py) | Prototype |

**Connected.** **C12 → C03** (predicted occupancy becomes a CVaR risk input), **C13 → C21/C22** (world-model rollouts can accelerate RL training).

### Causal and Adversarial (C14, C25)

| Code | Module | README | Implementation | Representative experiment | Dashboard | Status |
|---|---|---|---|---|---|---|
| C14 | Causal Risk Attribution (SCM) | [README](contributions/14_causal_risk_attribution/README.md) | [`14_causal_risk_attribution/causal_risk.py`](contributions/14_causal_risk_attribution/causal_risk.py) | inline driver | [`c14_causal_scm.py`](src/dynnav_dashboard/contributions/c14_causal_scm.py) | Implemented |
| C25 | Adversarial Attack Simulator | [README](contributions/25_adversarial_attack_simulator/README.md) | [`25_adversarial_attack_simulator/adversarial_attacks.py`](contributions/25_adversarial_attack_simulator/adversarial_attacks.py) | inline driver | [`c25_adversarial.py`](src/dynnav_dashboard/contributions/c25_adversarial.py) | Implemented |

**Related documents.** Attack-aware IDS: [`docs/README_TF_Attack_Aware_IDS.md`](docs/README_TF_Attack_Aware_IDS.md). **Connected:** **C25 → C08** (attacks exercise the IDS), **C14 → C20** (causes feed the failure explainer).

### Neuromorphic and 3D Perception (C15, C23–C24)

| Code | Module | README | Implementation | Dashboard | Status |
|---|---|---|---|---|---|
| C15 | Neuromorphic Sensing (DVS + SNN) | [README](contributions/15_neuromorphic_sensing/README.md) | [`15_neuromorphic_sensing/neuromorphic_sensing.py`](contributions/15_neuromorphic_sensing/neuromorphic_sensing.py) | [`c15_neuromorphic.py`](src/dynnav_dashboard/contributions/c15_neuromorphic.py) | Prototype (synthetic event streams) |
| C23 | Gaussian Splatting Mapper | [README](contributions/23_gaussian_splatting_mapper/README.md) | [`23_gaussian_splatting_mapper/gaussian_splatting_map.py`](contributions/23_gaussian_splatting_mapper/gaussian_splatting_map.py) | [`c23_gaussian_splatting.py`](src/dynnav_dashboard/contributions/c23_gaussian_splatting.py) | Prototype (no differentiable renderer in repo) |
| C24 | NeRF Uncertainty Maps | [README](contributions/24_nerf_uncertainty/README.md) | [`24_nerf_uncertainty/nerf_uncertainty.py`](contributions/24_nerf_uncertainty/nerf_uncertainty.py) | [`c24_nerf_uncertainty.py`](src/dynnav_dashboard/contributions/c24_nerf_uncertainty.py) | Prototype (MC-dropout proxy) |

**Connected.** **C24 → C07** (uncertainty maps drive next-best-view), **C23 → C07** (3D-GS frontiers feed exploration). Photogrammetry integration: [`photogrammetry_module/`](photogrammetry_module/).

### Distributed Learning and Consensus (C16, C26)

| Code | Module | README | Implementation | Dashboard | Status |
|---|---|---|---|---|---|
| C16 | Federated Navigation Learning | [README](contributions/16_federated_nav_learning/README.md) | [`16_federated_nav_learning/federated_nav.py`](contributions/16_federated_nav_learning/federated_nav.py) | [`c16_federated_learning.py`](src/dynnav_dashboard/contributions/c16_federated_learning.py) | Implemented |
| C26 | Swarm Consensus (BFT) | [README](contributions/26_swarm_consensus/README.md) | [`26_swarm_consensus/swarm_consensus.py`](contributions/26_swarm_consensus/swarm_consensus.py) | [`c26_bft_swarm.py`](src/dynnav_dashboard/contributions/c26_bft_swarm.py) | Implemented |

**Connected.** **C16 → C01/C02/C24** (federated training of heuristic and perception models without centralising raw data), **C26 ↔ C09** (BFT consensus over multi-robot allocations).

### Reinforcement Learning (C21–C22)

| Code | Module | README | Implementation | Dashboard | Status |
|---|---|---|---|---|---|
| C21 | PPO Navigation Agent | [README](contributions/21_ppo_navigation_agent/README.md) | [`21_ppo_navigation_agent/ppo_nav_agent.py`](contributions/21_ppo_navigation_agent/ppo_nav_agent.py) | [`c21_ppo.py`](src/dynnav_dashboard/contributions/c21_ppo.py) | Implemented |
| C22 | Curriculum RL | [README](contributions/22_curriculum_rl/README.md) | [`22_curriculum_rl/curriculum_rl.py`](contributions/22_curriculum_rl/curriculum_rl.py) | [`c22_curriculum_rl.py`](src/dynnav_dashboard/contributions/c22_curriculum_rl.py) | Implemented |

**Connected.** **C22 → C21** (curriculum schedules PPO training), **C21 ← C03** (risk shaping reuses the CVaR cost), **C13 → C21** (world-model rollouts). Curriculum data: [`data_curriculum/`](data_curriculum/).

### Semantic Mapping (C17)

| Code | Module | README | Implementation | Dashboard | Status |
|---|---|---|---|---|---|
| C17 | Topological Semantic Maps | [README](contributions/17_topological_semantic_maps/README.md) | [`17_topological_semantic_maps/topo_semantic_map.py`](contributions/17_topological_semantic_maps/topo_semantic_map.py) | [`c17_topological_maps.py`](src/dynnav_dashboard/contributions/c17_topological_maps.py) | Implemented |

**Connected.** **C17 → C19** (semantic zones ground mission language), **C17 → C10** (zones map to ethical constraints).

## Research Monograph Series

DynNav is accompanied by a complete collection of technical monographs that provide a detailed scientific treatment of each contribution.

While this README focuses on the overall architecture and implementation, the monographs contain the full research-level discussion, including:

- Motivation and problem formulation
- Mathematical foundations
- Algorithm design
- Theoretical analysis
- Complexity analysis
- Experimental methodology
- Failure modes and limitations
- Literature positioning
- Reviewer-oriented critique
- Publication strategy
- Open research questions

These documents are intended for researchers, graduate students, reviewers, and engineers seeking a deeper understanding of the underlying methods.

### Core Planning and Uncertainty

| Contribution | Monograph |
|-------------|------------|
| C01 — Learned A* Heuristics | [DynNav_C01_Learned_Astar_DeepDive.pdf](DynNav_C01_Learned_Astar_DeepDive.pdf) |
| C02 — EKF / UKF Uncertainty Estimation | [DynNav_C02_EKF_UKF_DeepDive.pdf](DynNav_C02_EKF_UKF_DeepDive.pdf) |
| C03 — CVaR Belief-Space Planning | [DynNav_C03_CVaR_AStar_DeepDive.pdf](DynNav_C03_CVaR_AStar_DeepDive.pdf) |
| C04 — Returnability-Aware Navigation | [DynNav_C04_Returnability_DeepDive.pdf](DynNav_C04_Returnability_DeepDive.pdf) |

### Safety, Security and Exploration

| Contribution | Monograph |
|-------------|------------|
| C05 — Safe Mode Navigation | [DynNav_C05_Safe_Mode_FSM_DeepDive.pdf](DynNav_C05_Safe_Mode_FSM_DeepDive.pdf) |
| C06 — Energy and Connectivity-Aware Planning | [DynNav_C06_Energy_Connectivity_DeepDive.pdf](DynNav_C06_Energy_Connectivity_DeepDive.pdf) |
| C07 — Next-Best-View Exploration | [DynNav_C07_NextBestView_DeepDive.pdf](DynNav_C07_NextBestView_DeepDive.pdf) |
| C08 — Security and Intrusion Detection | [DynNav_C08_Security_IDS_DeepDive.pdf](DynNav_C08_Security_IDS_DeepDive.pdf) |

### Multi-Robot Systems and Human-Aware Navigation

| Contribution | Monograph |
|-------------|------------|
| C09 — Multi-Robot Coordination | [DynNav_C09_MultiRobot_DeepDive.pdf](DynNav_C09_MultiRobot_DeepDive.pdf) |
| C10 — Human-Aware Navigation | [DynNav_C10_HumanAware_DeepDive.pdf](DynNav_C10_HumanAware_DeepDive.pdf) |

### Learning, Reasoning and Foundation Models

| Contribution | Monograph |
|-------------|------------|
| C11 — Twin-Critic Reinforcement Learning | [DynNav_C11_TwinCritic_RL_DeepDive.pdf](DynNav_C11_TwinCritic_RL_DeepDive.pdf) |
| C12 — Diffusion-Based Planning | [DynNav_C12_Diffusion_DeepDive.pdf](DynNav_C12_Diffusion_DeepDive.pdf) |
| C13 — World Models | [DynNav_C13_WorldModel_DeepDive.pdf](DynNav_C13_WorldModel_DeepDive.pdf) |
| C14 — Structural Causal Models | [DynNav_C14_CausalSCM_DeepDive.pdf](DynNav_C14_CausalSCM_DeepDive.pdf) |
| C19 — LLM Mission Planning | [DynNav_C19_LLMPlanner_DeepDive.pdf](DynNav_C19_LLMPlanner_DeepDive.pdf) |
| C20 — Failure Explanation Engine | [DynNav_C20_FailureExplainer_DeepDive.pdf](DynNav_C20_FailureExplainer_DeepDive.pdf) |
| C21 — PPO Navigation Policies | [DynNav_C21_PPO_DeepDive.pdf](DynNav_C21_PPO_DeepDive.pdf) |
| C22 — Curriculum Learning | [DynNav_C22_Curriculum_DeepDive.pdf](DynNav_C22_Curriculum_DeepDive.pdf) |

### Mapping, Perception and Formal Methods

| Contribution | Monograph |
|-------------|------------|
| C15 — Neuromorphic Perception | [DynNav_C15_Neuromorphic_DeepDive.pdf](DynNav_C15_Neuromorphic_DeepDive.pdf) |
| C17 — Topological Semantic Maps | [DynNav_C17_TopologicalMaps_DeepDive.pdf](DynNav_C17_TopologicalMaps_DeepDive.pdf) |
| C18 — Signal Temporal Logic and Control Barrier Functions | [DynNav_C18_CBF_STL_DeepDive.pdf](DynNav_C18_CBF_STL_DeepDive.pdf) |
| C23 — Gaussian Splatting | [DynNav_C23_GaussianSplatting_DeepDive.pdf](DynNav_C23_GaussianSplatting_DeepDive.pdf) |
| C24 — Neural Radiance Fields (NeRF) | [DynNav_C24_NeRF_DeepDive.pdf](DynNav_C24_NeRF_DeepDive.pdf) |

### Distributed Systems and Robustness

| Contribution | Monograph |
|-------------|------------|
| C16 — Federated Learning | [DynNav_C16_Federated_DeepDive.pdf](DynNav_C16_Federated_DeepDive.pdf) |
| C25 — Adversarial Robustness | [DynNav_C25_Adversarial_DeepDive.pdf](DynNav_C25_Adversarial_DeepDive.pdf) |
| C26 — Byzantine Fault-Tolerant Swarm Consensus | [DynNav_C26_BFT_DeepDive.pdf](DynNav_C26_BFT_DeepDive.pdf) |

### Comprehensive Analyses

| Document | Description |
|-----------|-------------|
| [DynNav_Mega_Ellinika.pdf.pdf](DynNav_Mega_Ellinika.pdf.pdf) | Extended Greek-language technical analysis of the complete DynNav framework |
| [DynNav_UltraDeep_Analysis.pdf](DynNav_UltraDeep_Analysis.pdf) | System-wide research analysis covering architecture, theory, evaluation, and future research directions |

### Suggested Reading Path

Researchers primarily interested in navigation, uncertainty, and formal safety are encouraged to begin with:

1. C01 — Learned A* Heuristics
2. C02 — EKF / UKF Uncertainty Estimation
3. C03 — CVaR Belief-Space Planning
4. C04 — Returnability-Aware Navigation
5. C18 — STL + CBF Safety Shields

These five contributions form the core scientific foundation of the DynNav framework.



### Contribution Relationships

DynNav's contributions are designed to compose. The diagram summarises the principal data and control dependencies; arrows read "feeds / supervises / informs".

```
            +---------- C02 EKF/UKF ----------+
            | (state belief + innovations)    |
            v                                  v
        C03 Belief / CVaR Risk          C08 IDS <-- C25 Adversarial
            |                                  |
   +--------+----------+                       +--> C14 Causal SCM --> C20 Explainer
   v        v          v
C18 STL+CBF  C04 Irrev./Return.   C12 Diffusion Occupancy --> (risk input to C03)
   ^            |        |
   |            v        v
   +- C05 Safe-Mode FSM  C07 NBV <-- C24 NeRF / C23 3D-GS
        |  (supervisor)
        +--> C06 Energy / Connectivity
        +--> C09 Multi-Robot <--> C26 Swarm BFT
        +--> C19 LLM Mission --> C10 Human / Ethics <-- C17 Semantic Maps

   C13 World Model --> C21 PPO <-- C22 Curriculum
   C16 Federated Learning --> (trains C01 heuristics, C02 / C24 models)
```

Key relationships, stated explicitly:

- **C03 → C18.** CVaR risk maps from belief-space planning parameterise the CBF in the safety filter; the two should be read together. Theory bridge: [`docs/Proposition_Irreversibility_vs_Risk_Weighting.md`](docs/Proposition_Irreversibility_vs_Risk_Weighting.md).
- **C04 → C05 → C{03,18}.** Irreversibility/returnability raises a feasibility signal that the safe-mode FSM uses to supervise the risk planner and the safety filter.
- **C07 ↔ C24 / C23.** Next-best-view exploration consumes NeRF MC-dropout uncertainty (C24) and Gaussian-splatting frontiers (C23). Shared returnability scoring with C04: [`docs/Returnability- & Irreversibility-Aware Frontier NBV.md`](docs/Returnability-%20&%20Irreversibility-Aware%20Frontier%20NBV.md).
- **C16 → C01 / C02 / C24.** Federated learning can train heuristic and perception models without centralising raw data.
- **C26 ↔ C09.** Byzantine fault-tolerant consensus selects an agreed plan over the multi-robot allocator's candidates.
- **C19 → C10 / C17.** Mission language is grounded via semantic maps (C17) and converted into ethical constraints (C10).
- **C25 → C08 → C14 → C20.** Adversarial attacks exercise the IDS; detected anomalies are attributed by the causal SCM; the explainer renders human-readable failure reports.

---

## 8. The Research Dashboard

The Streamlit dashboard at [dynnav-dynamic-navigation-rerouting-in-unknown-environments-fq.streamlit.app](https://dynnav-dynamic-navigation-rerouting-in-unknown-environments-fq.streamlit.app/) reproduces every contribution as a self-contained, browser-based interactive simulation. The dashboard requires no robot, no ROS installation, and no GPU.

The home page is [`app/dashboard.py`](app/dashboard.py) and the sidebar pages live under [`app/pages/`](app/pages/):

| # | Page | Purpose |
|---|---|---|
| 0 | [`app/dashboard.py`](app/dashboard.py) (home) | Project overview, headline metrics, quick navigation |
| 1 | [`1_Architecture.py`](app/pages/1_Architecture.py) | Layered diagram of the DynNav stack |
| 2 | [`2_Navigation_Demo.py`](app/pages/2_Navigation_Demo.py) | Closed-loop episode with online replanning |
| 3 | [`3_Risk_Map.py`](app/pages/3_Risk_Map.py) | Uncertainty and risk heatmaps, CVaR threshold visualisation |
| 4 | [`4_Planner_Comparison.py`](app/pages/4_Planner_Comparison.py) | A\* versus risk-aware A\*, Monte-Carlo sweep across seeds |
| 5 | [`5_Research_Modules.py`](app/pages/5_Research_Modules.py) | Searchable catalogue of all twenty-six contributions |
| 6 | [`6_Contribution_Simulations.py`](app/pages/6_Contribution_Simulations.py) | One interactive mini-simulation per contribution (C01–C26) |

The Contribution Simulations page is the technical centrepiece. A dropdown over `C01`–`C26` dispatches to a self-contained `render(st)` function defined in [`src/dynnav_dashboard/contributions/`](src/dynnav_dashboard/contributions/) (one `cNN_*.py` file per contribution); each renderer presents:

1. a short research explanation,
2. interactive controls (seed and topic-specific parameters),
3. one or more output plots,
4. quantitative metrics,
5. an interpretation block that comments on the current parameter regime.

The dashboard is **explicit about what is real and what is illustrative**. Each interpretation block names the synthetic proxy in use (for example, a Chebyshev-distance heuristic stands in for a learned cost-to-go network in C01) and the parameter regime in which the proxy behaves like the production version.

---

## 9. Technical Stack

| Layer | Component | Implementation |
|---|---|---|
| **Planning** | A\* core, learned heuristic, risk-aware variant | Pure NumPy; 8-connected; optional heuristic field and risk weight |
| | Topological routing | networkx weighted graph |
| | Next-best-view exploration | Frontier extraction + information-gain scoring |
| **Safety** | CBF filter | Iterative half-space projection on quadratic safety set |
| | STL monitor | Bounded-time predicate checking |
| | Safe-mode FSM | Four-state automaton with hysteresis |
| | Returnability check | Bidirectional A\* under risk threshold |
| **Learning** | PPO | Risk-shaped actor-critic |
| | Twin-critic (TD3-style) | min of two Q estimates |
| | Curriculum | Five-stage adaptive difficulty scheduler |
| | World model | Ensemble rollouts with growing process noise |
| | Federated learning | FedAvg with heterogeneity and dropout |
| **Security** | IDS | Sliding-window chi-square and CUSUM |
| | Adversarial defence | Median + MAD outlier suppression on LiDAR scans |
| **Multi-robot** | Assignment | Hungarian (exact); brute permutation for n ≤ 6 |
| | Consensus | Coordinate-wise median, α-trimmed mean, BFT weighted median |
| **Foundation models** | LLM mission planner | LLM call (via Ollama / HF) with deterministic rule-based fallback |
| | VLM agent | LLaVA / GPT-4V hook with stub fallback |
| **Perception** | EKF / UKF | Linear-Gaussian Kalman with sigma-point inflation |
| | Diffusion occupancy | DDPM-style spread of occupancy probability over horizon |
| | NeRF uncertainty | MC-dropout proxy field |
| | 3D Gaussian Splatting | Visual reconstruction; no differentiable renderer in this repo |
| | Neuromorphic | DVS event stream + SNN classifier |
| **Visualisation** | Plotly + Matplotlib | All figures |
| | Streamlit | Multi-page dashboard |
| **Substrate** | ROS 2 Humble | Nav2, slam_toolbox, TurtleBot3 |

---

## 10. Installation

The project supports three installation profiles, depending on what the user wants to run.

### 10.1 Dashboard only (no ROS, no GPU)

Sufficient to reproduce every contribution in the browser and to exercise the synthetic experiments.

```bash
git clone https://github.com/panagiotagrosdouli/DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments.git
cd DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments

python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate

pip install -r requirements.txt     # streamlit, numpy, pandas, plotly, matplotlib, networkx
pip install pytest                  # for the test suite
```

### 10.2 Full research stack (Python, no ROS)

Required to exercise the learning, generative and foundation-model contributions in non-stub mode.

```bash
pip install -r requirements.txt
pip install \
    torch>=2.0 \
    transformers>=4.40 \
    diffusers>=0.27 \
    open3d>=0.17 \
    scipy>=1.10
# For C11 and C19 in non-stub mode:
#   install Ollama from https://ollama.ai/download
#   pull a small local model, e.g.:  ollama pull llama3
```

### 10.3 ROS 2 stack (Ubuntu 22.04, ROS 2 Humble)

Required for closed-loop experiments on TurtleBot3 (real or Gazebo).

```bash
sudo apt install \
    ros-humble-desktop \
    ros-humble-nav2-bringup \
    ros-humble-slam-toolbox \
    ros-humble-turtlebot3*

mkdir -p ~/dynnav_ws/src && cd ~/dynnav_ws/src
ln -s /path/to/DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments ./dynnav
cd .. && rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

---

## 11. Running the Experiments

There is no single batch driver on the current branch; each contribution is run via its own scripts. Contributions C01–C10 expose runnable drivers under `contributions/NN_*/experiments/`; several of C11–C26 run their module file directly or via an `experiments/` script. Examples below use scripts that exist in the repository.

```bash
# Formal safety shields (STL + CBF) — Contribution 18
python contributions/18_formal_safety_shields/experiments/eval_safety_shields.py

# Diffusion occupancy risk maps — Contribution 12
python contributions/12_diffusion_occupancy/experiments/eval_diffusion_occupancy.py

# Learned A* node-expansion benchmark — Contribution 01
python contributions/01_learned_astar/experiments/eval_astar_learned.py

# CVaR / risk-budget path selection — Contribution 03
python contributions/03_belief_risk_planning/experiments/lambda_sweep_risk_length_demo.py

# Irreversibility τ phase-transition sweep — Contribution 04
python contributions/04_irreversibility_returnability/experiments/run_irreversibility_tau_sweep.py

# Frontier-vs-random NBV benchmark — Contribution 07
python contributions/07_nbv_exploration/experiments/run_nbv_random_vs_frontier_benchmark.py

# Intrusion-detection sweep — Contribution 08
python contributions/08_security_ids/experiments/eval_ids_sweep.py
```

A self-contained example for the swarm-consensus module (Contribution 26):

```bash
python -c "
import numpy as np, sys
sys.path.insert(0, 'contributions/26_swarm_consensus')
from swarm_consensus import SwarmCoordinator
coord = SwarmCoordinator(n_robots=6, n_byzantine=1)
grid = np.zeros((20, 20)); grid[8:12, 8:12] = 1.0
result = coord.plan(grid, (0, 0), (18, 18))
print(f'Cost: {result.agreed_cost:.2f} | Byzantine detected: {result.n_byzantine_detected}')
"
```

To run the test suites:

```bash
pytest contributions/tests/ -v
pytest tests/ -v
```

Scripts for C01–C10 write CSV logs into the contribution's `results/` directory and plots into `data/plots/`. Repository-wide ablation, benchmark, calibration, OOD and real-world logs are stored in the corresponding `logs_*` folders. The canonical claim → evidence mapping is [`docs/CLAIMS_EVIDENCE.md`](docs/CLAIMS_EVIDENCE.md).

---

## 12. Running the Dashboard

### 12.1 Locally

```bash
streamlit run app/dashboard.py
```

The application opens at `http://localhost:8501`. The **Contribution Simulations** page ([`app/pages/6_Contribution_Simulations.py`](app/pages/6_Contribution_Simulations.py)) exposes all twenty-six demos in a single dropdown.

### 12.2 Cloud-hosted

A deployed instance runs on Streamlit Community Cloud:

> [dynnav-dynamic-navigation-rerouting-in-unknown-environments-fq.streamlit.app](https://dynnav-dynamic-navigation-rerouting-in-unknown-environments-fq.streamlit.app/)

---

## 13. ROS 2 Integration

The ROS 2 packages live in several directories:

- [`lidar_ros2/`](lidar_ros2/) — LiDAR drivers, scan-matching, slam_toolbox integration, and the bulk of the launch files. Setup and bring-up are documented in [`docs/README_LiDAR_SLAM_TurtleBot3_ROS2.md`](docs/README_LiDAR_SLAM_TurtleBot3_ROS2.md).
- [`cybersecurity_ros2/nodes/`](cybersecurity_ros2/) — intrusion-detection nodes wrapping C08's chi-square / CUSUM detectors.
- [`ros2_ws/lidar_slam_tb3/`](ros2_ws/lidar_slam_tb3/) — a TurtleBot3-specific workspace combining LiDAR SLAM and the DynNav planning stack.
- [`dynamic_nav/`](dynamic_nav/), [`core/`](core/) — the navigation stack and planner cores.

The system has been tested on a TurtleBot3 Burger (hardware) and a TurtleBot3 Waffle (Gazebo). Launch files are under [`lidar_ros2/`](lidar_ros2/) and [`launch/`](launch/); for example:

```bash
# SLAM bring-up
ros2 launch lidar_ros2 bringup_slam.launch.py

# TurtleBot3 dynamic-navigation stack
ros2 launch lidar_ros2 dynamic_nav_tb3.launch.py

# Gazebo simulation
ros2 launch lidar_ros2 simulation.launch.py
```

The integration is partial. Several launch files orchestrate the perception and planning nodes, but the formal-safety filter (C18) and the swarm-consensus logic (C26) are currently exercised via their Python evaluators rather than as live ROS 2 nodes. Wiring these into the ROS 2 graph is on the future-work list ([section 22](#22-future-research-directions)).

---

## 14. Experimental Methodology

The experiments reported in section 15 and in the per-module documentation follow a consistent protocol.

**Determinism.** Every contribution accepts an explicit seed. All randomness — obstacle placement, sensor noise, attack injection, federated client samples — derives from `numpy.random.default_rng(seed)`. Two runs with the same seed produce bit-identical plots and metrics.

**Seed sweeps.** Where a single seed could mislead, contributions report a Monte-Carlo sweep over seeds `{1, 7, 13, 21, 42}`. Inter-seed variance is reported alongside the mean.

**Baselines.** Each learning-augmented contribution is compared against a clearly identified classical baseline: learned A\* versus vanilla A\*, CVaR A\* versus shortest-path A\*, twin-critic versus optimistic-max, curriculum versus flat training, robust estimators versus naive mean, BFT-weighted median versus naive majority.

**Logging.** Numerical results for C01–C10 land in CSV files under `contributions/NN_module_name/results/`; plots are written to `data/plots/`. Five additional repository-wide log folders capture ablation (`logs_ablation/`), benchmarks (`logs_benchmark/`), calibration (`logs_calibration/`, `logs_calibration_ensemble/`), out-of-distribution evaluation (`logs_ood/`) and real-world runs (`logs_real_world/`).

---

## 15. Selected Results

The numbers below summarise representative outcomes. They are illustrative rather than headline claims; the claim → evidence mapping is [`docs/CLAIMS_EVIDENCE.md`](docs/CLAIMS_EVIDENCE.md), and the per-contribution documentation gives full tables and ablations.

### 15.1 Formal safety shields (C18)

| Metric | Without filter | With STL + CBF filter |
|---|---|---|
| Constraint violations per episode (mean) | 4.2 | 0.3 |
| Path-length overhead | — | < 8 % |
| Average command correction | — | 0.026 m/s |

### 15.2 Swarm consensus (C26)

| Metric | Naive majority | BFT weighted median |
|---|---|---|
| Byzantine detection rate | 60 % | 91 % |
| Correct plan selected | 71 % | 96 % |
| Byzantine tolerance | f < N/2 | f < N/3 |

### 15.3 Federated learning (C16)

| Round | Centralised val MSE | Federated val MSE (6 robots) |
|---|---|---|
| 1 | 0.41 | 0.37 |
| 10 | 0.18 | 0.21 |
| 20 | 0.12 | 0.14 |

### 15.4 Curriculum reinforcement learning (C22)

| Training regime | Episodes to reach "hard" stage | Final success rate |
|---|---|---|
| Flat | n/a | 23 % |
| Adaptive five-stage curriculum | ~200 | 61 % |

### 15.5 Learned A\* (C01)

On a 35×35 grid with 18 obstacles, the learned-heuristic variant typically reduces node expansions by 25–45 % at a path-cost penalty under 5 %. The reduction grows with clutter density and vanishes in open space. Reproduce with [`contributions/01_learned_astar/experiments/eval_astar_learned.py`](contributions/01_learned_astar/experiments/eval_astar_learned.py).

### 15.6 CVaR A\* (C03)

Setting α = 0.95 with a risk weight of 3.0 reduces the worst 5 % of per-step risks by 30–60 % at a 5–15 % path-length penalty. Reproduce with [`contributions/03_belief_risk_planning/experiments/lambda_sweep_risk_length_demo.py`](contributions/03_belief_risk_planning/experiments/lambda_sweep_risk_length_demo.py).

### 15.7 Irreversibility / returnability (C04)

The irreversibility threshold τ exhibits a sharp feasibility phase transition; see [`contributions/04_irreversibility_returnability/experiments/run_irreversibility_tau_sweep.py`](contributions/04_irreversibility_returnability/experiments/run_irreversibility_tau_sweep.py) and detailed results in [`docs/README_Irreversibility_Aware_Planning results.md`](docs/README_Irreversibility_Aware_Planning%20results.md).

All values are reproducible from the corresponding seeds, either via the cited scripts or via the Streamlit dashboard.

---

## 16. Why a Streamlit Dashboard

A non-trivial engineering decision was to build a browser-based research dashboard as a first-class artefact rather than as an afterthought. The rationale is threefold.

**Reproducibility.** A robotics repository that ships only a ROS package and no installation script is difficult to verify. The dashboard exposes every contribution as a deterministic synthetic experiment — given a seed, the figures, metrics and verdicts are bit-for-bit reproducible. A reviewer can confirm an effect in seconds.

**Accessibility.** Reviewers and collaborators do not need to install ROS 2, build a Gazebo world, or own a TurtleBot3 to inspect the framework's claims. The dashboard turns the research portfolio into a self-contained read-only experiment that opens in a browser.

**Methodological velocity.** Decoupling algorithmic ideas from the friction of robotic integration shortens the iteration cycle. A risk-aware planner can be specified, tested across seeds, and visually inspected in minutes rather than days. ROS 2 integration follows after the algorithm has stabilised.

The synthetic-simulation philosophy also has a practical justification. A graduate research project should not depend on continuous access to physical robots. By making the framework runnable on a laptop with five Python packages, the work survives the loss of a particular piece of hardware and can be extended by anyone with a browser.

---

## 17. Theoretical Background

This section briefly anchors the framework in its relevant prior art. Per-contribution references are in each module's documentation.

**Uncertainty-aware navigation.** The framework draws on belief-space planning (Platt, Kaelbling, Lozano-Pérez) and on partially observable MDP formulations. Recent work — notably DYNUS (Kondo et al., 2025) and Map-Predictive Motion Planning (Katyal et al.) — frames the same challenge: trajectories planned under nominal assumptions can become unsafe at any moment because the agent cannot predict ground-truth futures. DynNav's response is to make every layer's uncertainty explicit and consumable by the layer above.

**CVaR-style planning.** Conditional Value-at-Risk is a coherent risk measure standard in finance (Rockafellar and Uryasev). In safe robotics it has been used to replace expected cost with expected cost in the worst α-fraction of outcomes (Chow, Tamar et al.). C03 implements a risk-weighted A\* variant that augments edge cost with a CVaR penalty.

**Formal safety constraints, CBFs and STL.** Control Barrier Functions (Ames, Xu, Tabuada) certify forward invariance of a safe set via affine constraints on the control input. Signal Temporal Logic (Maler, Nickovic) allows time-bounded specifications. C18 composes both: the STL monitor produces a Boolean safety signal, and the CBF layer minimally edits the commanded action to maintain forward invariance. The guarantee is at the level of the action filter, not the whole stack.

**Reinforcement learning trade-offs.** On-policy PPO (Schulman et al.) is preferred for its trust-region stability; twin-critic estimators (TD3, Fujimoto et al.) mitigate the over-estimation bias of max-over-noisy-Q targets. Curriculum learning (Bengio et al.) trades early-stage performance for late-stage capability on tasks that are otherwise unreachable from a cold start.

**Adversarial robustness.** Sensor spoofing on LiDAR and GPS has been documented in the cyber-physical-systems literature (Cao et al., Shoukry et al.). C25's median + MAD filter is a robust-statistics standard; the chi-square and CUSUM detectors in C08 are textbook tools from change-point detection.

**Swarm coordination.** Byzantine fault tolerance dates back to Lamport, Shostak and Pease. In the continuous-aggregation setting, coordinate-wise median and α-trimmed mean tolerate up to f Byzantine agents when n > 2f (or n > 3f for stronger guarantees in adversarial models). C26 uses both.

**Federated learning.** FedAvg (McMahan et al.) is the de-facto baseline. C16 demonstrates the convergence-versus-heterogeneity trade-off and the effect of client dropout.

**World models.** The Dreamer line of work (Hafner et al.) shows that ensemble rollouts under a learned latent dynamics model can substitute for environment interaction. C13 adopts the same architectural shape.

**Diffusion-based occupancy prediction.** Generative models for occupancy / risk forecasting (Toyungyernsub et al., Bharilya and Kumar) extend single-step prediction to a distribution over futures. C12 uses a Gaussian-spread proxy to keep the simulation lightweight; the production version uses a DDPM.

**Neuromorphic perception.** Event cameras (DVS) emit asynchronous, microsecond-latency, high-dynamic-range pixel-change events. Combined with spiking neural networks (Tavanaei et al.) they offer fast obstacle detection at low power. C15 demonstrates the principle on synthetic event streams.

---

## 18. Engineering Challenges Encountered

The list below records the non-trivial engineering issues that surfaced during development. They are reported here because they are the kind of detail typically omitted from research write-ups, yet they consumed substantial time and shaped the architecture.

**Streamlit caching versus stateful environments.** The original navigation episode runner mutated the environment in place. Streamlit's `@st.cache_data` aggressively serialised the cached instance, and subsequent runs poisoned each other's state, producing non-deterministic plots across reruns. The fix was to deep-copy the environment at the boundary of every cached call and to make the episode runner pure with respect to its inputs.

**Replanning that never reached the goal.** An early version of the closed-loop demo replanned on every step against the same dilated obstacle map and oscillated between two corridors, never converging. The fix was to introduce a hysteresis window on the replanning trigger and to require a strict improvement in the planner's f-score before committing to a new path.

**`scipy` removed from the dashboard runtime.** An early implementation of C01 used `scipy.ndimage.distance_transform_edt` for the learned-heuristic proxy. To keep the dashboard's dependency surface at five packages, the distance transform was reimplemented in pure NumPy using iterative Chebyshev dilation. The result is slower for very large grids but indistinguishable in the dashboard's operating range. SciPy remains a dependency of the full research stack.

**Hungarian assignment for n > 6.** The brute-permutation Hungarian variant in [`contributions/09_multi_robot/`](contributions/09_multi_robot/) is exact but exponential. For larger swarms an O(n³) Munkres implementation is required; the slot is deliberately marked in the module.

**ROS 2 packaging.** The ROS 2 stack was originally interleaved with the Python library, which broke `colcon build` when Python imports leaked into the workspace's site-packages search path. The fix was the strict separation between `ros2/`, `lidar_ros2/`, `cybersecurity_ros2/` and the pure-Python `nav_research/` package.

**Streamlit Community Cloud build pinning.** Streamlit Community Cloud pins Python and Streamlit versions independently from the local development image. A Plotly API used locally silently produced an empty figure in the cloud build. The dashboard now uses only documented stable APIs and pins minimum versions in `requirements.txt`.

**Colour-key drift in the dashboard.** Design tokens were initially defined under one set of keys (`muted`) while contribution modules used another (`text_muted`). The mismatch surfaced only at render time. A single source of truth — `nav_research.config.COLORS` — and a linting pass resolved the issue. The lesson is to keep design tokens behind a typed accessor rather than a free-form dictionary.

**Deterministic randomness across NumPy versions.** Newer NumPy `default_rng` byte-layouts differ across versions; legacy `numpy.random.seed` fixtures stopped matching. The framework standardised on `np.random.default_rng(seed)` everywhere and removed all calls to the legacy API.

**LLM-planner determinism.** The LLM mission planner (C19) ships with a deterministic rule-based fallback. This is deliberate: an actual LLM call would make the dashboard non-reproducible and would require network credentials at build time. The downstream contract — a typed list of (action, location) tuples — is identical to what an LLM call emits, so the parser can be swapped out without changing any consumer.

**Two `requirements.txt` files in spirit.** The repository's `requirements.txt` is currently the dashboard runtime. The fuller research stack (PyTorch, transformers, diffusers, Open3D) is not pinned in a single file. This is an outstanding issue; section 10 documents the actual dependency layers.

---

## 19. Deployment and Debugging Notes

**Cold-start latency on the dashboard.** The Contribution Simulations page imports many modules on first render. On a cold Streamlit Community Cloud container this is roughly four to six seconds. Subsequent renders are instantaneous. If cold-start becomes a problem, the dispatcher can be rewritten to import lazily on dropdown selection.

**Headless smoke test.** The CI pipeline runs `streamlit.testing.v1.AppTest` over every contribution renderer and verifies the page renders without exception. This catches the colour-key class of bugs and the random-seed-API-drift class of bugs before deployment.

**TurtleBot3 hardware testing.** Real-robot runs (TurtleBot3 Burger) used a quiet office environment, a Hokuyo URG-04LX scanner and an off-board ROS 2 controller. Logs from these sessions are archived under `logs_real_world/`.

**WSL2 support.** The framework runs on Windows under WSL2 (Ubuntu 22.04). Graphics-heavy ROS 2 visualisation (RViz) requires WSLg or an X server. The dashboard works natively on Windows without WSL.

**Python environment isolation.** Use of `python -m venv` is strongly recommended. The repository's `nav_research.egg-info/` is regenerated by `pip install -e .`; do not commit it manually.

**`build/` and `install/` directories.** These are colcon artefacts. Although they appear in the repository tree, they are reproducible and can be deleted before rebuilding.

---

## 20. Limitations and Honest Disclosures

- The framework provides **formal safety constraints and STL/CBF action filtering**, not end-to-end formal verification of the whole stack. The guarantee is that the filtered action is projected onto the safe set; upstream perception and planning are not themselves verified.
- The ROS 2 stack is **partially integrated**: not every safety contribution is wired as a runtime node. Several launch files orchestrate perception and base planning but rely on Python evaluators for the safety filter and the swarm consensus.
- 3D Gaussian Splatting (C23) is **visualised**, not optimised. No differentiable renderer ships in this repository.
- The LLM mission planner (C19) and the VLM navigation agent (C11) ship with **deterministic stubs**. Real LLM / VLM use requires an external Ollama instance or a Hugging Face account.
- The federated-learning module (C16) uses a **scalar regression** problem to make the FedAvg dynamics legible. Real perception models are not federated in this build.
- The neuromorphic module (C15) uses **synthetic event streams** rather than a calibrated DVS device.
- The adversarial module (C25) covers **LiDAR spoofing**, FGSM and PGD on perception inputs. No camera-domain physical attacks (e.g. adversarial patches under real illumination) are implemented.
- The reinforcement-learning curves (C21, C22) report results from a **synthetic environment**. Transfer to ROS 2 Gazebo is documented as future work.
- `requirements.txt` is currently the **dashboard runtime**; the full research stack requires additional packages, listed in section 10.
- The repository keeps several **legacy / alternate** contribution directories (`hybrid_learned_astar/`, `learned_uncertainty_astar/`, `hybrid_planner/`, `realtime_replanning/`) alongside the canonical numbered modules; only the numbered modules C01–C26 are authoritative.

---

## 21. Research Significance

The framework's contribution is methodological rather than the addition of a single novel component. It assembles a coherent uncertainty-aware navigation pipeline in which each layer's interface is designed to consume the layer below's uncertainty estimates and to expose its own to the layer above. The same A\* core supports learned-heuristic, risk-aware and CVaR-aware variants; the same safety layer can wrap a classical controller, a PPO policy or an LLM-driven plan; the same federated-learning loop can host any of the perception modules.

This *interface discipline* is the practical thesis of the project. It makes the difference between a collection of independent demos and a stack in which an improvement in one layer immediately benefits the others.

The Streamlit dashboard is the second methodological contribution. By making the entire research portfolio reproducible in a browser, it lowers the barrier to inspection and critique. The framework is designed to be argued with rather than admired.

---

## 22. Future Research Directions

- A differentiable 3D Gaussian Splatting pipeline for C23 with calibrated uncertainty exported to C24.
- Integration of C18's CBF filter as a ROS 2 node sitting between Nav2 and `cmd_vel`.
- Replacement of the rule-based parser in C19 with a small local LLM under a constrained-decoding wrapper that emits only typed plans.
- A real federated-learning experiment on a learned perception model, replacing the scalar regression in C16.
- Sim-to-real transfer experiments for the PPO policy (C21) using the world-model surrogate (C13) as a domain-randomisation engine.
- Joint optimisation of NBV (C07) and NeRF uncertainty (C24) so the next viewpoint reduces the field's variance rather than a frontier proxy.
- A consolidated `pyproject.toml` replacing the current `setup.py` / `setup.cfg` / `requirements.txt` triple, with optional dependency groups (`[dashboard]`, `[learning]`, `[ros2]`).
- A single batch driver (`run_all_contributions.py`) that dispatches every module's evaluation from one entry point.

---

## 23. Citation

If this framework supports your work, please cite the repository:

```bibtex
@software{grosdouli_dynnav_2025,
  author    = {Grosdouli, Panagiota},
  title     = {{DynNav}: Dynamic Navigation and Rerouting in Unknown Environments},
  year      = {2025},
  publisher = {GitHub},
  url       = {https://github.com/panagiotagrosdouli/DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments},
  license   = {Apache-2.0},
  version   = {v0.3-multi-robot-disagreement},
  note      = {26 research contributions: uncertainty-aware, risk-sensitive, learning-augmented navigation.}
}
```

A [`CITATION.cff`](CITATION.cff) file is provided in the repository root for tools that consume the Citation File Format.

---

## 24. Author

**Panagiota Grosdouli**
Department of Electrical and Computer Engineering
Democritus University of Thrace (DUTH)
[ee.duth.gr](https://ee.duth.gr)

The work is carried out as an independent research portfolio in autonomous systems and uncertainty-aware navigation, consolidating twenty-six methodological contributions into a single reproducible artefact.

---

## 25. License

Copyright © 2025 Panagiota Grosdouli.

Released under the **Apache License, Version 2.0**. See [`LICENSE`](LICENSE) for the full text.

The Apache-2.0 licence is chosen because it explicitly grants a patent licence alongside the copyright licence — relevant for downstream use of the safety-filter and adversarial-defence components — and because it imposes no copyleft on derived works.

---

## 26. Acknowledgements

This project was developed as an independent research effort built upon the broader open-source robotics and machine learning ecosystem. The framework integrates and extends technologies including ROS 2 Humble, Nav2, slam_toolbox, TurtleBot3, NumPy, SciPy, PyTorch, Plotly, Streamlit, networkx, Open3D, and components from the Hugging Face ecosystem.

A number of implemented techniques are based on established methods from the scientific literature, including Hungarian assignment optimization, median–MAD outlier filtering, Federated Averaging (FedAvg), TD3-style twin critics, PPO, Dreamer-inspired world models, and adversarial attack methods such as FGSM and PGD. The canonical references for these approaches are provided within the corresponding module documentation.

The author also acknowledges the wider open-source and research communities whose publicly available tools, publications, and educational resources contributed to the realization of this work.

---
