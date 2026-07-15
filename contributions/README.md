# DynNav Contributions

This directory contains the numbered research contributions of DynNav.

Each contribution must explain what it does **as a standalone module**: its problem, inputs, method, outputs, validation status, and limitations. Cross-module integrations are optional extensions, not substitutes for a complete standalone description.

## Standalone contribution map

| # | Contribution | What it does on its own |
|---|---|---|
| 01 | Learned A* | Uses a learned heuristic to guide A* search and evaluates search effort, path quality, and inference overhead against classical baselines. |
| 02 | Uncertainty calibration | Audits whether predicted uncertainty matches observed error and calibrates the uncertainty signal before downstream use. |
| 03 | Belief-risk planning | Plans routes using probabilistic belief and risk-sensitive path costs rather than geometry alone. |
| 04 | Irreversibility and returnability | Rejects or penalizes actions that reduce the robot's ability to return, recover, or escape from future states. |
| 05 | Safe-mode navigation | Monitors mission conditions and switches among nominal, cautious, replanning, and stop behaviors using explicit rules. |
| 06 | Energy and connectivity | Selects routes while accounting for remaining energy and communication quality. |
| 07 | Next-best-view exploration | Selects informative viewpoints while balancing travel cost, path risk, returnability, and connectivity. |
| 08 | Security IDS | Detects abnormal or adversarial sensor-estimation behavior and produces alarms or trust signals. |
| 09 | Multi-robot navigation | Coordinates multiple robots, allocates tasks, and manages conflicting plans or shared resources. |
| 10 | Human-language and ethics | Converts human instructions and preference constraints into machine-readable navigation objectives and restrictions. |
| 11 | VLM navigation agent | Uses visual and language observations to propose semantic navigation goals or waypoints. |
| 12 | Diffusion occupancy | Produces multiple possible future occupancy maps and derives uncertainty or risk estimates from their distribution. |
| 13 | Latent world model | Predicts possible future navigation outcomes in a learned latent state before selecting an action sequence. |
| 14 | Causal risk attribution | Represents navigation failures with a causal model and ranks candidate root causes using interventions or counterfactual reasoning. |
| 15 | Neuromorphic sensing | Converts event-camera-like observations into asynchronous obstacle or motion cues for navigation. |
| 16 | Federated navigation learning | Trains shared navigation models across multiple robots without centralizing their raw local data. |
| 17 | Topological semantic maps | Builds a graph of meaningful places and grounds semantic queries to graph nodes for high-level routing. |
| 18 | Formal safety shields | Checks temporal safety predicates and modifies proposed controls using safety-filter constraints in the implemented prototype. |
| 19 | LLM mission planner | Converts a high-level mission description into an ordered, structured sequence of navigation tasks. |
| 20 | Multimodal failure explainer | Combines navigation signals and failure evidence to generate structured, human-readable explanations. |
| 21 | PPO navigation agent | Learns a navigation policy through proximal policy optimization and evaluates the learned policy in controlled environments. |
| 22 | Curriculum reinforcement learning | Trains navigation agents on progressively harder tasks to study whether staged difficulty improves learning. |
| 23 | Gaussian-splatting mapper | Represents a scene with Gaussian primitives and exposes mapping or frontier information for navigation experiments. |
| 24 | NeRF uncertainty | Estimates view-dependent scene uncertainty from neural radiance-field predictions for exploration or risk estimation. |
| 25 | Adversarial attack simulator | Injects controlled attacks or corruptions into navigation inputs to test detector and planner robustness. |
| 26 | Swarm consensus | Studies how a robot group can agree on shared decisions when some agents may provide faulty or conflicting information. |
| 27 | Recoverability theory | Formalizes recoverability as a navigation property and studies conditions under which future safe options remain available. |

## Required README sections

Every numbered contribution should contain:

1. **Standalone purpose** — the exact problem solved by this module.
2. **Inputs** — data required to run it independently.
3. **Method** — algorithm or model implemented.
4. **Outputs** — files, predictions, plans, scores, or decisions produced.
5. **Quick start** — a repository-valid command.
6. **Evaluation** — metrics, baselines, seeds, and evidence provenance.
7. **Limitations** — what has not been demonstrated.
8. **Optional integrations** — links to other contributions only after the standalone behavior is clear.

## Canonical structure

```text
NN_module_name/
├── README.md
├── README_GR.md          # optional Greek version
├── code/                 # implementation specific to the contribution
├── experiments/          # reproducible experiment entry points
├── results/              # generated summaries and traceable artifacts
├── docs/                 # theory or extended technical notes
└── tests/                # module-local tests when appropriate
```

Use one primary English `README.md` and at most one Greek `README_GR.md`. Legacy names such as `readmegr.md` should not be added.

## Evidence maturity

Documentation must distinguish among:

- **Implemented** — code exists and is exercised by tests or reproducible commands.
- **Experimental** — prototype code or synthetic evaluation exists, but broader validation is incomplete.
- **Planned** — design documentation exists without a verified implementation.
- **Hardware validation required** — physical-robot evidence is not available.

Passing unit tests does not establish a formal safety guarantee, real-world robustness, or state-of-the-art performance.

## Numbering and consolidation

One contribution number should eventually map to one canonical directory. A directory must not be removed until its code, tests, results, and inbound links have been migrated.

- Contribution 02 is maintained under [`02_uncertainty_calibration/`](02_uncertainty_calibration/).
- Contribution 07 currently spans `07_nbv_exploration/` and `07_next_best_view/` because both contain active material. They must remain until a controlled code-and-test migration is completed.

## Supporting research directories

Unnumbered directories such as ablation studies, benchmarking, hybrid planners, and realtime replanning are supporting experiments rather than standalone numbered contributions. They should remain clearly identified as support material until a later repository-wide move updates all code, tests, and links.
