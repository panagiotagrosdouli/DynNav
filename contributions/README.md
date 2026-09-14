# DynNav Contributions

This directory contains DynNav's numbered research modules plus shared experimental infrastructure. The numbered folders are not all at the same maturity level and they should not be read as 27 equally validated scientific claims. Some are core research components, some are reproducible prototypes, some are exploratory integrations, and some are supporting research directions.

The project-level publication claim is narrower than this directory. The current paper track is centered on history-conditioned recoverability under action-triggered topology hazards; the broader modules below are retained as independent research/engineering contributions and future experimental tracks.

## How to read this directory

Each numbered contribution should answer five questions in its local `README.md`: what problem it addresses, what is actually implemented, how to run it, what evidence exists, and what remains unvalidated. Synthetic tests, unit tests, or numerical demonstrations are evidence for those environments only; they are not hardware validation, formal certification, or proof of universal superiority.

Recommended local structure:

```text
NN_module_name/
├── README.md          # authoritative English entry point
├── README_GR.md       # optional Greek overview
├── code/              # implementation when separated from experiments
├── experiments/       # reproducible experiment entry points
├── results/           # retained/generated evidence artifacts
├── models/            # model code or artifacts
└── docs/              # protocols, theory, extended notes
```

## Numbered research modules

| # | Module | Research role / scope |
|---:|---|---|
| 01 | [`learned_astar`](01_learned_astar/) | Learning-augmented heuristic search: learned guidance is used to accelerate or bias A*-style planning while preserving a classical planning reference point for evaluation. |
| 02 | [`uncertainty_calibration`](02_uncertainty_calibration/) | Calibration and evaluation of uncertainty estimates used by downstream planning or perception components; the emphasis is on whether confidence values are empirically meaningful. |
| 03 | [`belief_risk_planning`](03_belief_risk_planning/) | Belief- and risk-aware path planning, including route-risk objectives and risk-sensitive comparisons against geometric shortest-path baselines. |
| 04 | [`irreversibility_returnability`](04_irreversibility_returnability/) | Structural recoverability, returnability, and irreversibility metrics for identifying states from which safe return or recovery becomes difficult or impossible. This is a direct ancestor of the current DynNav-R research line. |
| 05 | [`safe_mode_navigation`](05_safe_mode_navigation/) | Runtime supervision and fallback/safe-mode behavior when nominal navigation becomes unreliable. Treat this as a supervisory mechanism, not as a formal safety certificate unless a specific formal result is supplied. |
| 06 | [`energy_connectivity`](06_energy_connectivity/) | Joint reasoning about motion cost, energy/resource constraints, and connectivity/return feasibility. |
| 07a | [`nbv_exploration`](07_nbv_exploration/) | Next-best-view exploration and information-gain-driven sensing/navigation experiments. |
| 07b | [`next_best_view`](07_next_best_view/) | Legacy/split implementation of the same numbered NBV research track. The duplicate numbering is intentional historical debt until migration is completed; do not count 07a and 07b as two independent contributions. |
| 08 | [`security_ids`](08_security_ids/) | Navigation-oriented anomaly / intrusion-detection experiments and security monitoring hooks. |
| 09 | [`multi_robot`](09_multi_robot/) | Multi-robot coordination and shared navigation experiments. |
| 10 | [`human_language_ethics`](10_human_language_ethics/) | Human-language interaction, mission-level interpretation, and explicit treatment of operational/ethical constraints around language-driven navigation. |
| 11 | [`vlm_navigation_agent`](11_vlm_navigation_agent/) | Vision-language-assisted semantic navigation: visual observations can inform high-level goal or waypoint selection. External model integration is an optional layer, not evidence of autonomous semantic reliability by itself. |
| 12 | [`diffusion_occupancy`](12_diffusion_occupancy/) | Generative / diffusion-style occupancy prediction for representing multiple plausible future occupancy outcomes and deriving risk maps. |
| 13 | [`latent_world_model`](13_latent_world_model/) | Latent dynamics / world-model planning experiments in which candidate actions can be evaluated through imagined rollouts before execution. |
| 14 | [`causal_risk_attribution`](14_causal_risk_attribution/) | Causal and counterfactual failure attribution: attempts to explain which modeled factors most influenced a navigation failure or elevated risk. |
| 15 | [`neuromorphic_sensing`](15_neuromorphic_sensing/) | Event-based / neuromorphic sensing prototypes for obstacle or motion perception, including simulated event-camera style pipelines. |
| 16 | [`federated_nav_learning`](16_federated_nav_learning/) | Federated-learning experiments for navigation models, aimed at learning across robots without centralizing raw local data. Privacy or robustness guarantees must be evaluated explicitly rather than inferred from the architecture. |
| 17 | [`topological_semantic_maps`](17_topological_semantic_maps/) | Higher-level topological-semantic map representations layered above metric occupancy grids for zone- or concept-level navigation. |
| 18 | [`formal_safety_shields`](18_formal_safety_shields/) | Experimental runtime shields / monitors inspired by temporal-logic and barrier-function methods. Any formal guarantee applies only if the assumptions, model, solver, and proof obligations for that specific implementation are satisfied. |
| 19 | [`llm_mission_planner`](19_llm_mission_planner/) | Language-model-based mission decomposition and high-level task planning. It should be treated as a high-level proposal generator that requires downstream validation and constraint checking. |
| 20 | [`multimodal_failure_explainer`](20_multimodal_failure_explainer/) | Multimodal post-hoc failure explanation using navigation traces and other available observations; explanation quality is distinct from causal correctness. |
| 21 | [`ppo_navigation_agent`](21_ppo_navigation_agent/) | PPO-based reinforcement-learning navigation baseline / prototype for comparison with search- and model-based planners. |
| 22 | [`curriculum_rl`](22_curriculum_rl/) | Curriculum-learning infrastructure for progressively harder reinforcement-learning navigation tasks. |
| 23 | [`gaussian_splatting_mapper`](23_gaussian_splatting_mapper/) | Experimental Gaussian-splatting mapping / scene-representation track for richer spatial reconstruction than a basic occupancy grid. |
| 24 | [`nerf_uncertainty`](24_nerf_uncertainty/) | NeRF-style scene representation with uncertainty-oriented analysis for navigation or mapping experiments. |
| 25 | [`adversarial_attack_simulator`](25_adversarial_attack_simulator/) | Adversarial / fault-injection simulator used to stress navigation perception, communication, or planning assumptions in controlled tests. |
| 26 | [`swarm_consensus`](26_swarm_consensus/) | Swarm / distributed consensus experiments for coordinating multiple agents under local information exchange. |
| 27 | [`Recoverability_Theory`](27_Recoverability_Theory/) | Recoverability theory and supporting formulations. This is conceptually closest to the current history-conditioned safe-return work, but theoretical claims must be read together with their stated assumptions and proofs. |

## Shared research infrastructure

The non-numbered directories are infrastructure rather than additional numbered contributions:

- [`benchmarking/`](benchmarking/) — common benchmark utilities and comparative experiment support.
- [`ablation_study/`](ablation_study/) — controlled component-removal / sensitivity experiments.
- [`hybrid_learned_astar/`](hybrid_learned_astar/) and [`hybrid_planner/`](hybrid_planner/) — integration experiments combining classical and learned/pluggable planning components.
- [`learned_uncertainty_astar/`](learned_uncertainty_astar/) — combined learned-heuristic / uncertainty-aware planning experiments.
- [`realtime_replanning/`](realtime_replanning/) — online replanning support and real-time-oriented prototypes.
- [`tests/`](tests/) — cross-contribution test coverage.
- [`_unsorted/`](_unsorted/) — historical material awaiting classification; it is not an authoritative contribution entry point.

## Evidence hierarchy

Use the following labels consistently in local documentation and project claims:

1. **Implemented** — source exists and the documented entry point is runnable in its stated environment.
2. **Unit-tested** — local behavior is covered by automated tests.
3. **Synthetic / benchmark evidence** — evaluated in controlled generated or benchmark scenarios.
4. **Simulator evidence** — executed in a robotics simulator such as ROS2/Nav2/Gazebo with retained traces/artifacts.
5. **Hardware evidence** — executed on a physical robot with retained experimental records.
6. **Formal result** — theorem/certificate/guarantee with explicit assumptions and a verifiable argument or solver contract.

These labels are not interchangeable. In particular, passing tests do not imply safety, simulation does not imply hardware reliability, and a module name such as `formal_safety_shields` does not itself establish a formal guarantee.

## Current publication-focused track

The strongest currently developed DynNav research result is the history-conditioned recoverability line: when robot actions activate future topology hazards, two trajectories may reach the same geometric cell while inducing different future safe-return probabilities. The planner therefore augments geometric state with executed action-trigger history. The retained synthetic, held-out, geometric, ROS2/Nav2, and Gazebo infrastructure for that line lives primarily outside the legacy numbered modules under `dynnav/`, `ros2_ws/`, `results/`, and `paper/`.

This distinction is deliberate: the numbered contributions document the broader research program, while the paper makes only the narrower claims supported by retained evidence.

## Documentation policy

Every contribution README should avoid unsupported phrases such as "guaranteed safe", "provably safe", "real-time", "state of the art", or "production ready" unless the repository contains the corresponding proof, timing protocol, comparative study, or deployment evidence. Numerical claims should point to retained artifacts or reproducible commands.

See the root [`README.md`](../README.md), [`docs/REPOSITORY_AUDIT.md`](../docs/REPOSITORY_AUDIT.md), and the paper evidence manifest for project-level provenance and claim boundaries.
