# DynNav Contribution Dependency Graph

> Generated explanatory architecture — not experimental evidence.
>
> Relationships come from `configs/contributions/registry.yaml` and represent intended integration boundaries.

```mermaid
graph LR
  C01["C01 Learned A*"] --> C03["C03 Belief and Risk Planning"]
  C01 --> C04["C04 Returnability"]
  C01 --> C05["C05 Safe Mode"]
  C02["C02 Uncertainty Calibration"] --> C03
  C02 --> C12["C12 Diffusion Occupancy"]
  C02 --> C24["C24 NeRF Uncertainty"]
  C03 --> C04
  C03 --> C05
  C04 --> C05
  C06["C06 Energy and Connectivity"] --> C05
  C06 --> C07["C07 Next-Best View"]
  C07 --> C03
  C07 --> C06
  C08["C08 Security IDS"] --> C05
  C08 --> C14["C14 Causal Attribution"]
  C08 --> C25["C25 Attack Simulator"]
  C09["C09 Multi-Robot"] --> C16["C16 Federated Learning"]
  C09 --> C26["C26 Swarm Consensus"]
  C10["C10 Human/Language/Ethics"] --> C19["C19 Mission Planner"]
  C10 --> C20["C20 Failure Explainer"]
  C11["C11 VLM Agent"] --> C19
  C11 --> C20
  C12 --> C02
  C12 --> C03
  C13["C13 Latent World Model"] --> C03
  C13 --> C21["C21 PPO"]
  C14 --> C05
  C14 --> C20
  C15["C15 Neuromorphic Sensing"] --> C02
  C16 --> C09
  C16 --> C26
  C17["C17 Topological Semantic Maps"] --> C19
  C18["C18 Formal Safety Shields"] --> C05
  C19 --> C05
  C19 --> C20
  C21 --> C22["C22 Curriculum RL"]
  C22 --> C21
  C23["C23 Gaussian Splatting"] --> C03
  C24 --> C02
  C24 --> C03
  C25 --> C08
  C25 --> C05
  C26 --> C09
  C26 --> C16
  C26 --> C05
```

## Integration clusters

### Search, risk, recoverability, and supervision

C01 supplies learned search behavior; C02 calibrates uncertainty; C03 incorporates belief and risk; C04 evaluates reversibility; C05 owns runtime supervisory responses.

### Resource-aware active perception

C06 provides battery/connectivity feasibility and C07 combines it with information gain, travel cost, and risk-aware viewpoint selection.

### Security and explanation

C25 generates reproducible attacks, C08 detects and fuses trust signals, C14 structures attribution under explicit assumptions, and C20 produces evidence-grounded explanations. C05 remains the mitigation boundary.

### Multi-robot learning and consensus

C09 provides coordination scenarios, C16 studies distributed model updates, and C26 studies consensus under a bounded Byzantine threat model.

### Language and multimodal planning

C10 and C11 provide human-, language-, and perception-facing inputs. C19 translates accepted instructions into schema-constrained plans, while C20 explains failures without bypassing C05 safety controls.

## Claim boundary

An edge means that interfaces or research questions should compose. It does not prove empirical benefit, safety, causal identification, Byzantine resilience, ROS 2 execution, or hardware validation.