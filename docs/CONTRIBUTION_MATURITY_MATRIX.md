# DynNav Contribution Maturity Matrix

> Generated from `configs/contributions/registry.yaml`. Registry validation checks metadata and paths; it does not elevate scientific maturity.

## Distribution

| Maturity | Count |
|---|---:|
| Research Prototype | 7 |
| Experimental | 16 |
| Documentation Concept | 3 |

## Contribution-level matrix

| ID | Contribution | Maturity | Current evidence boundary |
|---|---|---|---|
| C01 | Learned A* Search | Research Prototype | Controlled search experiments; no universal admissibility or performance claim |
| C02 | Uncertainty Calibration | Research Prototype | Controlled calibration analysis; no deployment-distribution guarantee |
| C03 | Belief and Risk Planning | Research Prototype | Synthetic/controlled risk fields; no certified safety claim |
| C04 | Irreversibility and Returnability | Research Prototype | Algorithmic recoverability analysis; no real-world escape guarantee |
| C05 | Safe-Mode Navigation | Research Prototype | Explicit supervisor logic; no certified runtime-safety claim |
| C06 | Energy and Connectivity | Research Prototype | Parametric mission-feasibility model; hardware battery/radio validation pending |
| C07 | Next-Best View | Research Prototype | Controlled active-perception scoring; dataset and robot validation pending |
| C08 | Security IDS | Experimental | Synthetic attacks/anomalies; no certified intrusion-detection claim |
| C09 | Multi-Robot Navigation | Experimental | Controlled coordination fixtures; ROS 2 and fleet validation pending |
| C10 | Human, Language, and Ethics | Experimental | Implemented rules/costs only; no general moral-reasoning claim |
| C11 | VLM Navigation Agent | Experimental | Fixture-based interface evaluation; no paid-model or trained-VLM requirement in CI |
| C12 | Diffusion Occupancy | Experimental | Prototype future-occupancy model; no claim based on noise-perturbed grids alone |
| C13 | Latent World Model | Experimental | Controlled latent rollouts; no general world-model accuracy claim |
| C14 | Causal Risk Attribution | Experimental | Attribution under documented assumptions; no causal identification claim |
| C15 | Neuromorphic Sensing | Experimental | Event-stream fixtures; sensor/hardware limitations remain |
| C16 | Federated Navigation Learning | Experimental | Distributed optimization fixtures; federated learning alone is not privacy proof |
| C17 | Topological Semantic Maps | Experimental | Controlled graph/map fixtures; large-scale consistency validation pending |
| C18 | Formal Safety Shields | Experimental | Prototype constraints and intervention logs; no formal guarantee without proof assumptions |
| C19 | LLM Mission Planner | Documentation Concept | Schema and safety architecture; no direct LLM control or validated model claim |
| C20 | Multimodal Failure Explainer | Experimental | Evidence-structured explanations; no unrestricted factual-groundedness claim |
| C21 | PPO Navigation Agent | Experimental | Environment/policy fixtures; no learned-performance claim without checkpoint evidence |
| C22 | Curriculum RL | Experimental | Curriculum mechanics and metrics; no superiority claim without trained comparisons |
| C23 | Gaussian Splatting Mapper | Documentation Concept | Scene-representation interface; no full 3D Gaussian Splatting training claim |
| C24 | NeRF Uncertainty | Documentation Concept | Implicit-field interface; no photorealistic NeRF training claim |
| C25 | Adversarial Attack Simulator | Experimental | Bounded reproducible attack profiles; not an exhaustive threat model |
| C26 | Swarm Consensus | Experimental | Tested scenarios only; no Byzantine-resilience claim outside the declared model |

## Promotion rule

A contribution can be promoted to **Implemented** only when substantive code, coherent public interfaces, focused passing tests, at least one executable command, generated machine-readable evidence, and behavior-matching documentation are all present. Dataset, simulation, ROS 2, hardware, trained-neural, security, and formal-safety labels require corresponding traceable artifacts.