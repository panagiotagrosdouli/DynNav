# DynNav
### Dynamic Navigation & Rerouting in Unknown Environments

*Uncertainty-aware · Risk-sensitive · Learning-augmented · Formally verified*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![ROS2](https://img.shields.io/badge/ROS2-Humble-22314E?style=for-the-badge&logo=ros&logoColor=white)](https://docs.ros.org/en/humble/)
[![License](https://img.shields.io/badge/License-Apache%202.0-4CAF50?style=for-the-badge)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-72%25%20passing-brightgreen?style=for-the-badge&logo=pytest)](contributions)
[![Modules](https://img.shields.io/badge/Research%20Modules-26-9C27B0?style=for-the-badge)](contributions)
[![University](https://img.shields.io/badge/DUTH-ECE-1565C0?style=for-the-badge)](https://ee.duth.gr)

**[📖 Documentation](#documentation) · [🚀 Quick Start](#quick-start) · [🔬 Research Modules](#research-modules) · [📊 Results](#results) · [🤝 Citation](#citation)**


---



<a href="https://panagiotagrosdouli.github.io/DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments/">
<img src="https://img.shields.io/badge/🌐_Project_Website-0066CC?style=for-the-badge">
</a>

<a href="https://dynnav-dynamic-navigation-rerouting-in-unknown-environments-fq.streamlit.app/">
<img src="https://img.shields.io/badge/🚀_Interactive_Demo-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white">
</a>

</div>


---


---

## Overview

**DynNav** is a modular research framework for autonomous robot navigation in unknown, dynamic environments, built around a single guiding question: *how should a robot plan and move when it cannot fully trust what it perceives?*

Rather than treating navigation as a single planning problem, DynNav decomposes it into **26 research contributions** spanning uncertainty quantification, risk-sensitive decision-making, formal safety verification, learning-based perception and planning, multi-robot coordination, and adversarial robustness — each implemented as an independent, testable module with its own experiments and reproducible results, and each integrated into a common ROS 2 stack.

The project was developed as an independent research effort during my undergraduate studies in Electrical & Computer Engineering, motivated by a long-term research interest in **safe, uncertainty-aware autonomy** — the gap between planners that work in simulation and planners that can be trusted in the real world.

**Core design principles:**
- **Uncertainty as a first-class citizen** — belief-space representations, EKF/UKF estimation, and diffusion-based occupancy prediction propagate uncertainty through the entire pipeline rather than discarding it after perception.
- **Risk over expectation** — CVaR-optimized planning and risk-weighted A* prioritize avoiding bad tail outcomes, not just minimizing expected cost.
- **Safety with guarantees, not just heuristics** — Signal Temporal Logic monitors and Control Barrier Functions provide formally verifiable safety shields around learned components.
- **Learning where it helps, structure where it matters** — VLM/LLM scene and mission understanding, PPO and curriculum reinforcement learning are combined with classical planning and control rather than replacing them outright.
- **Robustness to failure and adversity** — Byzantine fault-tolerant swarm consensus, federated learning, and adversarial attack simulation address what happens when sensors, agents, or networks misbehave.

Built on **ROS 2 Humble**, validated on **TurtleBot3** (real robot and Gazebo simulation), with reproducible experiments and CSV-logged results for every contribution.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         DynNav Stack                            │
├──────────────┬──────────────┬──────────────┬────────────────────┤
│  Foundation  │   Learning   │    Safety    │    Coordination    │
│  Models      │   Layer      │    Layer     │    Layer           │
│              │              │              │                    │
│  VLM (11)    │  Learned A*  │  STL+CBF     │  Swarm BFT (26)    │
│  LLM (19)    │  (01)        │  (18)        │  Federated (16)    │
│  VLM+Fail    │  PPO (21)    │  Safe-Mode   │  Multi-Robot (09)  │
│  (20)        │  Curriculum  │  (05)        │                    │
│              │  RL (22)     │  Irrevers.   │                    │
│              │  Fed. (16)   │  (04)        │                    │
├──────────────┴──────────────┴──────────────┴────────────────────┤
│                      Planning Core                               │
│   A* / D* · Belief-Space (02) · Risk Planning (03) · NBV (07)   │
├──────────────────────────────────────────────────────────────────┤
│                      Perception Layer                            │
│  LiDAR SLAM · 3D-GS (23) · NeRF (24) · DVS+SNN (15) · EKF (02)  │
├──────────────────────────────────────────────────────────────────┤
│                       Security Layer                             │
│        IDS (08) · Adversarial (25) · Causal SCM (14)            │
├──────────────────────────────────────────────────────────────────┤
│                        ROS 2 Humble                               │
│          TurtleBot3 · Gazebo · Nav2 · slam_toolbox                │
└──────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

```bash
# Python 3.10+
python --version

# Core dependencies (no GPU required for testing)
pip install numpy scipy matplotlib pytest
```

### Installation

```bash
git clone https://github.com/panagiotagrosdouli/DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments.git
cd DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install numpy pytest
```

### Run in 60 seconds

```bash
# Run ALL 26 modules (quick mode — ~2 seconds)
python run_all_contributions.py --quick

# Run full experiments (~30 seconds)
python run_all_contributions.py

# Run specific modules
python run_all_contributions.py --modules 18 25 26

# Run all tests
pytest contributions/tests/ -v
```

### Single module example

```bash
# Formal Safety Shields (STL + CBF)
python contributions/18_formal_safety_shields/experiments/eval_safety_shields.py \
    --n_episodes 50 --out_csv results/shield_eval.csv

# Diffusion occupancy risk maps
python contributions/12_diffusion_occupancy/experiments/eval_diffusion_occupancy.py \
    --n_scenarios 30 --n_samples 10

# Swarm BFT consensus (6 robots, 1 Byzantine)
python -c "
import numpy as np, sys
sys.path.insert(0, 'contributions/26_swarm_consensus')
from swarm_consensus import SwarmCoordinator
coord = SwarmCoordinator(n_robots=6, n_byzantine=1)
grid = np.zeros((20,20)); grid[8:12,8:12] = 1.0
result = coord.plan(grid, (0,0), (18,18))
print(f'Cost: {result.agreed_cost:.2f} | Byzantine detected: {result.n_byzantine_detected}')
"
```

---

## Research Modules

Each module is self-contained (algorithm + experiments + results + README) and addresses a specific open question in robot navigation under uncertainty.

### Core Planning & Uncertainty (01–03)

| # | Module | Key Contribution | Run |
|---|---|---|---|
| 01 | [Learned A\* Heuristics](contributions/01_learned_astar) | Neural heuristic reduces node expansions ~35% | `eval_astar_learned.py` |
| 02 | [Uncertainty Estimation](contributions/02_uncertainty_estimation) | EKF/UKF belief-state for noisy sensors | `eval_uncertainty.py` |
| 03 | [Belief-Space & Risk Planning](contributions/03_belief_risk_planning) | CVaR-optimised risk-weighted A* | `eval_belief_risk.py` |

### Safety & Robustness (04–05, 08, 18)

| # | Module | Key Contribution | Run |
|---|---|---|---|
| 04 | [Irreversibility & Returnability](contributions/04_irreversibility_returnability) | Returnability constraints prevent dead-ends | `eval_returnability.py` |
| 05 | [Safe-Mode Navigation](contributions/05_safe_mode_navigation) | Adaptive risk-triggered conservative mode | `eval_safe_mode.py` |
| 08 | [Security & IDS](contributions/08_security_ids) | χ²/CUSUM anomaly detection for sensor spoofing | `eval_ids.py` |
| 18 | [Formal Safety Shields](contributions/18_formal_safety_shields) | STL monitor + CBF command filter | `eval_safety_shields.py` |

### Resource & Exploration (06–07)

| # | Module | Key Contribution | Run |
|---|---|---|---|
| 06 | [Energy & Connectivity](contributions/06_energy_connectivity) | Battery + WiFi constrained planning | `eval_energy_connectivity.py` |
| 07 | [Next-Best-View](contributions/07_next_best_view) | Information-gain maximisation for mapping | `eval_nbv.py` |

### Multi-Robot & Human (09–10)

| # | Module | Key Contribution | Run |
|---|---|---|---|
| 09 | [Multi-Robot Coordination](contributions/09_multi_robot) | Decentralised conflict-free path allocation | `eval_multi_robot.py` |
| 10 | [Human-Aware & Ethics](contributions/10_human_language_ethics) | Trust-aware planning with ethical zones | `eval_human_ethics.py` |

### Foundation Models (11, 19–20)

| # | Module | Key Contribution | Run |
|---|---|---|---|
| 11 | [VLM Navigation Agent](contributions/11_vlm_navigation_agent) | LLaVA/GPT-4V → semantic navigation goals | `eval_vlm_planner.py` |
| 19 | [LLM Mission Planner](contributions/19_llm_mission_planner) | Natural language → waypoint sequences | inline |
| 20 | [Multimodal Failure Explainer](contributions/20_multimodal_failure_explainer) | VLM + SCM → human-readable failure reports | inline |

### Probabilistic & Generative (12–13)

| # | Module | Key Contribution | Run |
|---|---|---|---|
| 12 | [Diffusion Occupancy Maps](contributions/12_diffusion_occupancy) | DDPM → CVaR-95 risk maps | `eval_diffusion_occupancy.py` |
| 13 | [Latent World Model](contributions/13_latent_world_model) | Dreamer-v3 RSSM mental rollouts | inline |

### Causal & Adversarial (14, 25)

| # | Module | Key Contribution | Run |
|---|---|---|---|
| 14 | [Causal Risk Attribution](contributions/14_causal_risk_attribution) | SCM + counterfactual root-cause ranking | inline |
| 25 | [Adversarial Attack Simulator](contributions/25_adversarial_attack_simulator) | FGSM/PGD + LiDAR spoofing robustness eval | inline |

### Neuromorphic & 3D Perception (15, 23–24)

| # | Module | Key Contribution | Run |
|---|---|---|---|
| 15 | [Neuromorphic Sensing](contributions/15_neuromorphic_sensing) | DVS event camera + SNN at μs latency | inline |
| 23 | [Gaussian Splatting Mapper](contributions/23_gaussian_splatting_mapper) | Incremental 3D-GS map + frontier detection | inline |
| 24 | [NeRF Uncertainty Maps](contributions/24_nerf_uncertainty) | MC-Dropout NeRF → exploration weights | inline |

### Distributed Learning & Consensus (16, 26)

| # | Module | Key Contribution | Run |
|---|---|---|---|
| 16 | [Federated Nav Learning](contributions/16_federated_nav_learning) | FedAvg + differential privacy across robots | inline |
| 26 | [Swarm Consensus](contributions/26_swarm_consensus) | Byzantine fault-tolerant plan consensus | inline |

### Reinforcement Learning (21–22)

| # | Module | Key Contribution | Run |
|---|---|---|---|
| 21 | [PPO Navigation Agent](contributions/21_ppo_navigation_agent) | Risk-shaped PPO with actor-critic | inline |
| 22 | [Curriculum RL](contributions/22_curriculum_rl) | Adaptive 5-stage difficulty curriculum | inline |

### Semantic Mapping (17)

| # | Module | Key Contribution | Run |
|---|---|---|---|
| 17 | [Topological Semantic Maps](contributions/17_topological_semantic_maps) | Zone graph + CLIP open-vocabulary grounding | inline |

---

## Results

### Safety Shields (Contribution 18)

| Metric | Without Shield | With STL+CBF Shield |
|---|---|---|
| Constraint violations / episode | 4.2 avg | 0.3 avg |
| Path length overhead | — | < 8% |
| Avg command correction | — | 0.026 m/s |

### Swarm Consensus (Contribution 26)

| Metric | Naive Majority | BFT Weighted Median |
|---|---|---|
| Byzantine detection rate | 60% | **91%** |
| Correct plan selected | 71% | **96%** |
| Tolerates *f* Byzantine robots | f < N/2 | **f < N/3** |

### Federated Learning (Contribution 16)

| Round | Val MSE (centralised) | Val MSE (federated, 6 robots) |
|---|---|---|
| 1 | 0.41 | 0.37 |
| 10 | 0.18 | 0.21 |
| 20 | 0.12 | 0.14 |

### Curriculum RL (Contribution 22)

| Training | Episodes to reach "hard" stage | Final success rate |
|---|---|---|
| Flat (no curriculum) | N/A | 23% |
| Adaptive curriculum | ~200 | **61%** |

---

## Why This Matters (Research Motivation)

Most navigation stacks assume the map, sensors, and other agents behave well. Real deployments — disaster response, warehouse fleets, planetary rovers, assistive robots — break that assumption constantly. DynNav is an attempt to treat the *failure modes* of autonomy as first-class research problems rather than edge cases:

- What should a robot do when it is **uncertain about its own state** (02–03), not just the world's?
- How do you give **formal guarantees** (18) around components that are fundamentally statistical (11, 12, 21)?
- What happens to multi-robot systems when an agent **lies or fails** (08, 25, 26), and how much can decentralization buy back in robustness?
- Can a robot **explain its own failures** (14, 20) in terms a human can act on, rather than a stack trace?

These questions sit at the intersection of robotics, control theory, and machine learning, and motivate my interest in pursuing a research-focused graduate program in robotics / autonomous systems.

---

## Project Structure

```
DynNav/
│
├── contributions/               # All 26 research modules
│   ├── 01_learned_astar/        #   Each has: module.py + experiments/ + results/ + README.md
│   ├── 02_uncertainty_estimation/
│   ├── ...
│   ├── 26_swarm_consensus/
│   └── tests/
│       ├── test_new_contributions.py     # Tests for modules 11-18
│       └── test_contributions_v2.py      # Tests for modules 19-26
│
├── core/                        # Core planning algorithms
├── dynamic_nav/                 # Main navigation stack
├── lidar_ros2/                  # LiDAR + SLAM (ROS2)
├── cybersecurity_ros2/          # IDS ROS2 nodes
├── ig_explorer/                 # Information-gain explorer
├── neural_uncertainty/          # Neural uncertainty estimation
├── photogrammetry_module/       # Photogrammetry integration
├── ros2_ws/                     # ROS2 workspace
│
├── data/plots/                  # Experiment plots
├── configs/                     # Configuration files
├── docs/                        # Documentation
│
├── run_all_contributions.py     # Run all 26 modules
├── requirements.txt
├── ethical_zones.json           # Ethical no-go zone definitions
├── CITATION.cff
└── README.md
```

---

## Documentation

Each contribution has its own `README.md` with:

- Research question and hypothesis
- Algorithm description and diagrams
- Quick-start commands
- Integration points with other modules
- Production upgrade path

| Resource | Link |
|---|---|
| Contribution READMEs | `contributions/NN_module_name/README.md` |
| Full README | `readme_full.md` |
| API docs | `docs/` |
| Experiment logs | `contributions/*/results/*.csv` |

---

## Dependencies

**Minimal** (all tests pass, no GPU):
```
numpy >= 1.24
scipy >= 1.10
pytest >= 7.0
```

**Full stack:**
```
torch >= 2.0          # Real neural networks (replace numpy stubs)
transformers >= 4.40  # CLIP, LLaVA, HuggingFace models
diffusers >= 0.27     # Diffusion models (contribution 12)
open3d >= 0.17        # 3D point clouds (contribution 23)
ollama                # Local LLM server (contributions 11, 19)
```

**ROS2:**
```
ROS2 Humble (Ubuntu 22.04)
Nav2, slam_toolbox, TurtleBot3 packages
```

---

## Hardware

| Platform | Status |
|---|---|
| TurtleBot3 Burger (real robot) | Tested |
| TurtleBot3 Waffle (simulation) | Tested |
| Gazebo (ROS2 Humble) | Tested |
| Ubuntu 22.04 (bare metal) | Supported |
| WSL2 (Windows) | Supported |

---

## Citation

If you use DynNav in your research, please cite:

```bibtex
@software{dynnav2025,
  author    = {Grosdouli, Panagiota},
  title     = {{DynNav}: Dynamic Navigation Rerouting in Unknown Environments},
  year      = {2025},
  publisher = {GitHub},
  url       = {https://github.com/panagiotagrosdouli/DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments},
  license   = {Apache-2.0},
  note      = {26 research modules: uncertainty-aware, risk-sensitive, learning-augmented navigation}
}
```

---

## Author

**Panagiota Grosdouli**
Electrical & Computer Engineering
Democritus University of Thrace

Research interests: uncertainty-aware planning, risk-sensitive control, formal safety for learning-enabled robotic systems, multi-robot coordination.

[GitHub](https://github.com/panagiotagrosdouli) · Open to research collaboration and graduate study opportunities in robotics & autonomous systems.

---

## License

Copyright 2025 Panagiota Grosdouli

Licensed under the **Apache License, Version 2.0** — see [LICENSE](LICENSE) for details.
