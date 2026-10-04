# DynNav extension catalog

DynNav has one publication-facing research core:

> **History-conditioned safe-return planning under action-triggered topology hazards.**

The repository also contains a broad set of earlier research modules. They remain available for reuse, comparison and future extensions, but they are not equal parts of the current paper claim.

## Publication-facing core

| Area | Canonical implementation | Role |
|---|---|---|
| Action-triggered hazard model | `dynnav/commitment_hazard.py` | separates planning, executed trigger activation and future closure realization |
| Exact safe-return model | `dynnav/recoverability_belief.py` | computes bounded-hazard future return connectivity |
| Exact history planner | `dynnav/planners/commitment_aware_astar.py` | searches over position plus activated-hazard state |
| Critical-cut approximation | `dynnav/recoverability_cut.py`, `dynnav/planners/commitment_cut_astar.py` | provides a faster approximation with a retained joint-cut failure case |
| Hard safe-return baseline | `dynnav/planners/commitment_safe_return_astar.py` | feasibility-style objective comparison |
| State-only baseline | `dynnav/planners/hazard_reliability_astar.py` | endpoint-only marginal ablation |
| ROS 2/Nav2 implementation | `ros2_ws/src/dynnav_nav2_cpp/` | C++ Jazzy global planner with persistent executed-history state |
| Gazebo validation | `ros2_ws/src/dynnav_nav2_benchmark/` | frozen execution and measurement contracts |

Publication-facing claims and numerical values are governed by `CLAIM_EVIDENCE_MATRIX.md`, `EXPERIMENT_PROTOCOL_V3.md` and `paper/dynnav_r/evidence_manifest.json`.

## Earlier supporting modules

The earlier risk/recoverability stack remains useful for engineering context and exploratory work:

| ID | Module | Supporting role |
|---|---|---|
| **C03** | Risk-Aware A* | Occupancy-risk routing and legacy risk ablations. |
| **C04** | Returnability and Recoverability | Earlier structural escape-option and bottleneck concepts. |
| **C05** | Safe-Mode Supervisor | Runtime replan/recover/stop supervision prototypes. |

These modules should not be presented as the central V3 contribution unless a current evidence artifact explicitly depends on them.

## Supporting modules

These modules may support later experiments without expanding the main claim:

| ID | Module | Possible supporting role |
|---|---|---|
| **C02** | Uncertainty Estimation | Test sensitivity to uncertain or stale occupancy information. |
| **C07** | Safe Next-Best View | Study whether exploration targets preserve safe return options. |
| **C12** | Diffusion Occupancy Prediction | Future comparison against learned dynamic-occupancy prediction. |
| **C14** | Causal Risk Attribution | Explain whether failure originated from risk, bottleneck exposure or return loss. |
| **C18** | Formal Safety Shields | Future runtime layer after planner evaluation is stable. |
| **C20** | Failure Explanation | Generate structured explanations from event traces. |
| **C25** | Adversarial Navigation Testing | Stress-test route invalidation and observation perturbations. |

## Exploratory extensions

The following modules remain in the repository as independent exploratory directions:

- **C01** — Learned A* Search
- **C06** — Energy and Connectivity
- **C08** — Security and Intrusion Detection
- **C09** — Multi-Robot Coordination
- **C10** — Human-Aware Navigation
- **C11** — Twin-Critic Reinforcement Learning
- **C13** — Latent World Model
- **C15** — Neuromorphic Sensing
- **C16** — Federated Navigation Learning
- **C17** — Semantic Topological Maps
- **C19** — Language Mission Planner
- **C21** — PPO Navigation
- **C22** — Curriculum Reinforcement Learning
- **C23** — Gaussian Splatting Maps
- **C24** — NeRF Uncertainty
- **C26** — Byzantine-Fault-Tolerant Swarm

These extensions should not delay validation of the history-conditioned core, its failure boundaries and its reproducible evidence contracts.

## Interactive access

The dashboard remains available as an inspection and demonstration interface:

```bash
python -m pip install -e ".[dashboard]"
streamlit run app/dashboard.py
```

Open **Contribution Explorer** to inspect the individual modules. The canonical dashboard metadata is stored in [`src/dynnav_dashboard/contribution_registry.yaml`](../src/dynnav_dashboard/contribution_registry.yaml).

## Detailed legacy documentation

For module-level source code, experiments, figures and bilingual documentation, see:

- [`contributions/CONTRIBUTIONS_README.md`](../contributions/CONTRIBUTIONS_README.md)
- [`contributions/`](../contributions/)
- [`archive/README.md`](archive/README.md)

## Evidence interpretation

A renderer, figure, test or synthetic benchmark does not by itself establish real-robot safety, broad generalization, formal correctness or production readiness. ROS 2/Nav2 build and Gazebo execution evidence establish their stated integration contracts only. Each module retains its own maturity and evidence boundary.
