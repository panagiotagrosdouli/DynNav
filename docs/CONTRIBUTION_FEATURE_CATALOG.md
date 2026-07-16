# DynNav Contribution Feature Catalog

This catalog explains what every numbered DynNav contribution investigates, what the interactive Streamlit renderer exposes, and how its current maturity should be interpreted.

> The contribution demos are synthetic research interfaces. A renderer, figure, benchmark, or passing test does not by itself establish real-robot safety, generalization, formal correctness, ROS 2 integration, or production readiness.

## How to use the catalog

Run the dashboard and open **Contribution Explorer**:

```bash
python -m pip install -e ".[dashboard]"
streamlit run app/dashboard.py
```

Each contribution has its own controls, graphics, metrics, interpretation, and evidence boundary. The canonical dashboard metadata is stored in [`src/dynnav_dashboard/contribution_registry.yaml`](../src/dynnav_dashboard/contribution_registry.yaml).

## C01–C26 at a glance

| ID | Contribution | What it does | What you can change or inspect | Maturity |
|---|---|---|---|---|
| **C01** | Learned A* Search | Compares classical A* with a learned cost-to-go heuristic and makes the search-effort versus admissibility trade-off visible. | Grid size, obstacle density, heuristic influence, path, expanded nodes, cost, and runtime. | Research Prototype |
| **C02** | Uncertainty Estimation | Explores state-estimation uncertainty, calibration, and the difference between confidence and observed error. | Noise, uncertainty scale, calibration behavior, confidence bands, and error metrics. | Research Prototype |
| **C03** | Risk-Aware A* | Trades geometric path length against expected, peak, or tail-risk exposure. | Risk weight, risk field, competing paths, path cost, average risk, maximum risk, and CVaR-style metrics. | Research Prototype |
| **C04** | Returnability and Recoverability | Measures whether entering a region preserves escape routes, reverse paths, and future recovery freedom. | Bottlenecks, returnability thresholds, reachable recovery cells, escape options, and irreversibility indicators. | Research Prototype |
| **C05** | Safe-Mode Supervisor | Demonstrates a finite-state runtime supervisor that can continue, become cautious, replan, or stop. | Risk and uncertainty thresholds, persistence, hysteresis, cooldown, transitions, and supervisor state. | Research Prototype |
| **C06** | Energy and Connectivity | Classifies mission feasibility under battery reserve and communication constraints. | Battery level, reserve, route cost, communication quality, recharge/relay requirements, and feasibility verdict. | Research Prototype |
| **C07** | Safe Next-Best View | Scores exploration targets using information gain together with travel cost, risk, connectivity, and returnability. | Candidate viewpoints, scoring weights, information gain, route risk, connectivity, and selected target. | Research Prototype |
| **C08** | Security and Intrusion Detection | Studies anomalous or manipulated navigation observations and simple detection responses. | Attack/anomaly strength, detector threshold, score history, alarms, false positives, and detection delay. | Experimental |
| **C09** | Multi-Robot Coordination | Explores shared beliefs, communication links, task allocation, and conflicts among multiple robots. | Robot count, communication range, packet loss, assignments, conflicts, and fleet-level metrics. | Experimental |
| **C10** | Human-Aware Navigation | Adds social costs and personal-space reasoning to route selection around people. | Human positions, comfort radius, social-cost weight, candidate routes, and proximity metrics. | Experimental |
| **C11** | Twin-Critic Reinforcement Learning | Visualizes actor–critic policy choices and disagreement between two value estimators. | State/action controls, critic estimates, policy action, critic gap, reward, and stability indicators. | Experimental |
| **C12** | Diffusion Occupancy Prediction | Demonstrates generative prediction of future occupancy under uncertain motion. | Forecast horizon, sampling/noise controls, predicted occupancy, uncertainty, and scenario samples. | Experimental |
| **C13** | Latent World Model | Compresses observations into a latent state and explores imagined future rollouts. | Latent dimensions, rollout horizon, dynamics controls, reconstruction, and prediction error. | Experimental |
| **C14** | Causal Risk Attribution | Decomposes navigation risk into structured causes rather than reporting only one aggregate score. | Causal factors, interventions, counterfactual settings, total risk, and per-cause attribution. | Experimental |
| **C15** | Neuromorphic Sensing | Explores event-driven perception where changes generate events instead of conventional image frames. | Motion, event threshold, event rate, temporal accumulation, event map, and sparsity. | Experimental |
| **C16** | Federated Navigation Learning | Simulates decentralized model updates across robots without centralizing raw local data. | Client count, local data shift, aggregation rounds, client weights, model convergence, and disagreement. | Experimental |
| **C17** | Semantic Topological Maps | Combines semantic regions with a graph representation for high-level navigation. | Regions, semantic labels, graph edges, route preferences, topology, and selected semantic path. | Experimental |
| **C18** | Formal Safety Shields | Demonstrates runtime interventions inspired by control-barrier functions and temporal logic. | Safety boundary, nominal command, shield threshold, intervention state, and constraint satisfaction. | Experimental |
| **C19** | Language Mission Planner | Converts a natural-language instruction into a structured mission representation and explicit constraints. | Mission text, extracted goals, priorities, forbidden areas, assumptions, and structured plan. | Documentation Concept |
| **C20** | Failure Explanation | Produces structured explanations from navigation events, signals, and failure evidence. | Failure type, evidence channels, event sequence, attributed cause, confidence, and explanation output. | Experimental |
| **C21** | PPO Navigation | Demonstrates policy optimization concepts for navigation behavior. | Policy parameters, reward terms, action probabilities, episode reward, and learning curves. | Experimental |
| **C22** | Curriculum Reinforcement Learning | Shows how progressively harder tasks can change policy training and success. | Curriculum stage, task difficulty, promotion threshold, success history, and policy progression. | Experimental |
| **C23** | Gaussian Splatting Maps | Explores dense scene representations based on Gaussian primitives for navigation context. | Gaussian count/scale, visibility, scene density, rendering controls, and spatial representation. | Documentation Concept |
| **C24** | NeRF Uncertainty | Examines uncertainty-aware neural implicit scene representations. | Sampling density, observation coverage, uncertainty level, field slices, and confidence visualization. | Documentation Concept |
| **C25** | Adversarial Navigation Testing | Injects disturbances or attacks to evaluate how navigation behavior and metrics degrade. | Attack type, perturbation strength, planner response, path deviation, robustness, and failure rate. | Experimental |
| **C26** | Byzantine-Fault-Tolerant Swarm | Explores consensus when some robot reports are faulty, malicious, or untrusted. | Swarm size, faulty-node count, trust/consensus threshold, reports, accepted value, and consensus error. | Experimental |

## Contribution groups

### Planning and mission feasibility

C01, C03, C06, and C07 examine how the selected route changes when the objective includes learned guidance, spatial risk, energy, connectivity, and exploration value.

### Belief, uncertainty, mapping, and prediction

C02, C12, C15, C17, C23, and C24 investigate how the robot represents incomplete knowledge, future occupancy, event-based observations, semantic structure, and dense neural scenes.

### Runtime safety, recovery, and explanation

C04, C05, C14, C18, and C20 expose recoverability, supervisory actions, causal risk, runtime shields, and failure explanations.

### Learning systems

C11, C13, C16, C21, and C22 cover actor–critic learning, latent dynamics, federated updates, policy optimization, and curriculum progression.

### Security, people, and multi-robot systems

C08, C09, C10, C19, C25, and C26 cover anomaly detection, coordination, social navigation, language missions, adversarial testing, and fault-tolerant swarm consensus.

## Shared interactive features

Across the contribution playgrounds, the dashboard aims to provide:

- deterministic seeds where the underlying model supports them;
- sliders and selectors that change the actual computation rather than only the presentation;
- plots that update with the selected assumptions;
- metrics for comparing alternatives;
- short interpretation text explaining why the output changed;
- maturity and evidence-boundary notices;
- downloadable results where the page supports export.

## Evidence interpretation

The maturity labels mean:

- **Research Prototype:** implemented and exercised in controlled synthetic experiments, but not a production or hardware claim.
- **Experimental:** an interactive or computational research module with more limited validation.
- **Documentation Concept:** a structured interface or visualization of a research direction without equivalent implementation maturity.

For the module-level source code, experiments, figures, and bilingual documentation, see [`contributions/CONTRIBUTIONS_README.md`](../contributions/CONTRIBUTIONS_README.md).