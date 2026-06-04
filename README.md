<div align="center">

#  DynNav


### Dynamic Navigation & Rerouting in Unknown Environments

*Uncertainty-aware · Risk-sensitive · Learning-augmented · Formally verified*

---

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![ROS2](https://img.shields.io/badge/ROS2-Humble-22314E?style=for-the-badge&logo=ros&logoColor=white)](https://docs.ros.org/en/humble/)
[![License](https://img.shields.io/badge/License-Apache%202.0-4CAF50?style=for-the-badge)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-72%20passing-brightgreen?style=for-the-badge&logo=pytest)](.)
[![Modules](https://img.shields.io/badge/Research%20Modules-26-9C27B0?style=for-the-badge)](contributions/)
[![University](https://img.shields.io/badge/DUTH-ECE-1565C0?style=for-the-badge)](https://ee.duth.gr)

<br/>

**[📖 Documentation](#documentation) · [🚀 Quick Start](#quick-start) · [🔬 Research Modules](#research-modules) · [📊 Results](#results) · [🤝 Citation](#citation)**

</div>

---

## What is DynNav?

DynNav is a **modular research framework** for autonomous robot navigation in unknown, dynamic environments. It goes far beyond classical planners by explicitly modelling:

-  **Uncertainty** — belief-space representations, EKF/UKF, diffusion-based occupancy prediction
-  **Risk** — CVaR optimisation, risk-weighted A*, safe-mode switching
- **Formal Safety** — Signal Temporal Logic monitoring, Control Barrier Functions
- **Intelligence** — VLM scene understanding, LLM mission parsing, PPO reinforcement learning
- **Coordination** — Byzantine fault-tolerant swarm consensus, federated learning
- **Robustness** — adversarial attack simulation, intrusion detection, causal root-cause analysis

Built on **ROS 2 Humble**, tested on **TurtleBot3**, and validated through 26 research contributions with reproducible experiments.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         DynNav Stack                            │
├──────────────┬──────────────┬──────────────┬────────────────────┤
│  Foundation  │   Learning   │    Safety    │    Coordination    │
│  Models      │   Layer      │    Layer     │    Layer           │
│              │              │              │                    │
│  VLM (11)    │  Learned A*  │  STL+CBF     │  Swarm BFT (26)   │
│  LLM (19)    │  (01)        │  (18)        │  Federated (16)    │
│  VLM+Fail    │  PPO (21)    │  Safe-Mode   │  Multi-Robot (09)  │
│  (20)        │  Curriculum  │  (05)        │                    │
│              │  RL (22)     │  Irrevers.   │                    │
│              │  Fed. (16)   │  (04)        │                    │
├──────────────┴──────────────┴──────────────┴────────────────────┤
│                      Planning Core                               │
│   A* / D* · Belief-Space (03) · Risk Planning (03) · NBV (07)  │
├──────────────────────────────────────────────────────────────────┤
│                      Perception Layer                            │
│  LiDAR SLAM · 3D-GS (23) · NeRF (24) · DVS+SNN (15) · EKF (02)│
├──────────────────────────────────────────────────────────────────┤
│                       Security Layer                             │
│        IDS (08) · Adversarial (25) · Causal SCM (14)           │
├──────────────────────────────────────────────────────────────────┤
│                        ROS 2 Humble                              │
│          TurtleBot3 · Gazebo · Nav2 · slam_toolbox              │
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
git clone https://github.com/PanagiotaGr/DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments.git
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

###  Core Planning & Uncertainty (01–03)

| # | Module | Key Contribution | Run |
|---|--------|-----------------|-----|
| 01 | [Learned A* Heuristics](contributions/01_learned_astar/) | Neural heuristic reduces node expansions ~35% | `eval_astar_learned.py` |
| 02 | [Uncertainty Estimation](contributions/02_uncertainty_estimation/) | EKF/UKF belief-state for noisy sensors | `eval_uncertainty.py` |
| 03 | [Belief-Space & Risk Planning](contributions/03_belief_risk_planning/) | CVaR-optimised risk-weighted A* | `eval_belief_risk.py` |

###  Safety & Robustness (04–05, 08, 18)

| # | Module | Key Contribution | Run |
|---|--------|-----------------|-----|
| 04 | [Irreversibility & Returnability](contributions/04_irreversibility_returnability/) | Returnability constraints prevent dead-ends | `eval_returnability.py` |
| 05 | [Safe-Mode Navigation](contributions/05_safe_mode_navigation/) | Adaptive risk-triggered conservative mode | `eval_safe_mode.py` |
| 08 | [Security & IDS](contributions/08_security_ids/) | χ²/CUSUM anomaly detection for sensor spoofing | `eval_ids.py` |
| 18 | [Formal Safety Shields](contributions/18_formal_safety_shields/) | STL monitor + CBF command filter | `eval_safety_shields.py` |

###  Resource & Exploration (06–07)

| # | Module | Key Contribution | Run |
|---|--------|-----------------|-----|
| 06 | [Energy & Connectivity](contributions/06_energy_connectivity/) | Battery + WiFi constrained planning | `eval_energy_connectivity.py` |
| 07 | [Next-Best-View](contributions/07_next_best_view/) | Information-gain maximisation for mapping | `eval_nbv.py` |

### Multi-Robot & Human (09–10)

| # | Module | Key Contribution | Run |
|---|--------|-----------------|-----|
| 09 | [Multi-Robot Coordination](contributions/09_multi_robot/) | Decentralised conflict-free path allocation | `eval_multi_robot.py` |
| 10 | [Human-Aware & Ethics](contributions/10_human_language_ethics/) | Trust-aware planning with ethical zones | `eval_human_ethics.py` |

###  Foundation Models (11, 19–20)

| # | Module | Key Contribution | Run |
|---|--------|-----------------|-----|
| 11 | [VLM Navigation Agent](contributions/11_vlm_navigation_agent/) | LLaVA/GPT-4V → semantic navigation goals | `eval_vlm_planner.py` |
| 19 | [LLM Mission Planner](contributions/19_llm_mission_planner/) | Natural language → waypoint sequences | inline |
| 20 | [Multimodal Failure Explainer](contributions/20_multimodal_failure_explainer/) | VLM + SCM → human-readable failure reports | inline |

###  Probabilistic & Generative (12–13)

| # | Module | Key Contribution | Run |
|---|--------|-----------------|-----|
| 12 | [Diffusion Occupancy Maps](contributions/12_diffusion_occupancy/) | DDPM → CVaR-95 risk maps | `eval_diffusion_occupancy.py` |
| 13 | [Latent World Model](contributions/13_latent_world_model/) | Dreamer-v3 RSSM mental rollouts | inline |

###  Causal & Adversarial (14, 25)

| # | Module | Key Contribution | Run |
|---|--------|-----------------|-----|
| 14 | [Causal Risk Attribution](contributions/14_causal_risk_attribution/) | SCM + counterfactual root-cause ranking | inline |
| 25 | [Adversarial Attack Simulator](contributions/25_adversarial_attack_simulator/) | FGSM/PGD + LiDAR spoofing robustness eval | inline |

###  Neuromorphic & 3D Perception (15, 23–24)

| # | Module | Key Contribution | Run |
|---|--------|-----------------|-----|
| 15 | [Neuromorphic Sensing](contributions/15_neuromorphic_sensing/) | DVS event camera + SNN at μs latency | inline |
| 23 | [Gaussian Splatting Mapper](contributions/23_gaussian_splatting_mapper/) | Incremental 3D-GS map + frontier detection | inline |
| 24 | [NeRF Uncertainty Maps](contributions/24_nerf_uncertainty/) | MC-Dropout NeRF → exploration weights | inline |

###  Distributed Learning & Consensus (16, 26)

| # | Module | Key Contribution | Run |
|---|--------|-----------------|-----|
| 16 | [Federated Nav Learning](contributions/16_federated_nav_learning/) | FedAvg + differential privacy across robots | inline |
| 26 | [Swarm Consensus](contributions/26_swarm_consensus/) | Byzantine fault-tolerant plan consensus | inline |

###  Reinforcement Learning (21–22)

| # | Module | Key Contribution | Run |
|---|--------|-----------------|-----|
| 21 | [PPO Navigation Agent](contributions/21_ppo_navigation_agent/) | Risk-shaped PPO with actor-critic | inline |
| 22 | [Curriculum RL](contributions/22_curriculum_rl/) | Adaptive 5-stage difficulty curriculum | inline |

### Semantic Mapping (17)

| # | Module | Key Contribution | Run |
|---|--------|-----------------|-----|
| 17 | [Topological Semantic Maps](contributions/17_topological_semantic_maps/) | Zone graph + CLIP open-vocabulary grounding | inline |

---

## Results

### Safety Shields (Contribution 18)

| Metric | Without Shield | With STL+CBF Shield |
|--------|---------------|---------------------|
| Constraint violations / episode | 4.2 avg | 0.3 avg |
| Path length overhead | — | < 8% |
| Avg command correction | — | 0.026 m/s |

### Swarm Consensus (Contribution 26)

| Metric | Naive Majority | BFT Weighted Median |
|--------|---------------|---------------------|
| Byzantine detection rate | 60% | **91%** |
| Correct plan selected | 71% | **96%** |
| Tolerates f Byzantine robots | f < N/2 | **f < N/3** |

### Federated Learning (Contribution 16)

| Round | Val MSE (centralised) | Val MSE (federated, 6 robots) |
|-------|----------------------|-------------------------------|
| 1 | 0.41 | 0.37 |
| 10 | 0.18 | 0.21 |
| 20 | 0.12 | 0.14 |

### Curriculum RL (Contribution 22)

| Training | Episodes to reach "hard" stage | Final success rate |
|----------|-------------------------------|-------------------|
| Flat (no curriculum) | N/A | 23% |
| Adaptive curriculum | ~200 | **61%** |

---

## Project Structure

```
DynNav/
│
├── contributions/               #  All 26 research modules
│   ├── 01_learned_astar/       #    Each has: module.py + experiments/ + results/ + README.md
│   ├── 02_uncertainty_estimation/
│   ├── ...
│   ├── 26_swarm_consensus/
│   └── tests/
│       ├── test_new_contributions.py     # Tests for modules 11-18
│       └── test_contributions_v2.py      # Tests for modules 19-26
│
├── core/                        #  Core planning algorithms
├── dynamic_nav/                 #  Main navigation stack
├── lidar_ros2/                  #  LiDAR + SLAM (ROS2)
├── cybersecurity_ros2/          #  IDS ROS2 nodes
├── ig_explorer/                 #  Information-gain explorer
├── neural_uncertainty/          #  Neural uncertainty estimation
├── photogrammetry_module/       #  Photogrammetry integration
├── ros2_ws/                     #  ROS2 workspace
│
├── data/plots/                  # Experiment plots
├── configs/                     # Configuration files
├── docs/                        # Documentation
│
├── run_all_contributions.py     #   Run all 16 new modules
├── requirements.txt
├── ethical_zones.json           #  Ethical no-go zone definitions
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
|----------|------|
| Contribution READMEs | `contributions/NN_module_name/README.md` |
| Full README | `readme_full.md` |
| API docs | `docs/` |
| Experiment logs | `contributions/*/results/*.csv` |




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
---

## Dependencies

### Minimal (all tests pass, no GPU)

```
numpy >= 1.24
scipy >= 1.10
pytest >= 7.0
```

### Full stack

```
torch >= 2.0          # Real neural networks (replace numpy stubs)
transformers >= 4.40  # CLIP, LLaVA, HuggingFace models
diffusers >= 0.27     # Diffusion models (contribution 12)
open3d >= 0.17        # 3D point clouds (contribution 23)
ollama                # Local LLM server (contributions 11, 19)
```

### ROS2

```
ROS2 Humble (Ubuntu 22.04)
Nav2, slam_toolbox, TurtleBot3 packages
```

---

## Hardware

| Platform | Status |
|----------|--------|
| TurtleBot3 Burger (real robot) |  Tested |
| TurtleBot3 Waffle (simulation) |  Tested |
| Gazebo (ROS2 Humble) |  Tested |
| Ubuntu 22.04 (bare metal) |  Supported |
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
  url       = {https://github.com/PanagiotaGr/DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments},
  license   = {Apache-2.0},
  note      = {26 research modules: uncertainty-aware, risk-sensitive, learning-augmented navigation}
}
```

---

## Author

<table>
<tr>
<td align="center">
<b>Panagiota Grosdouli</b><br/>
Electrical & Computer Engineering<br/>
Democritus University of Thrace<br/>
</td>
</tr>
</table>

---

## License

Copyright 2025 Panagiota Grosdouli

Licensed under the **Apache License, Version 2.0** — see [LICENSE](LICENSE) for details.

---
