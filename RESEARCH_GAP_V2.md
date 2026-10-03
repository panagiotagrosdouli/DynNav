# Research Gap V2: Belief-Conditioned Safe Return under Action-Induced Latent Topology State

**Status:** research decision document; pre-publication; literature screen current to 2026-10-03.

**Purpose:** decide whether DynNav has a defensible next research question before changing the publication-facing planner or manuscript.

This document supersedes the provisional direction in `RESEARCH_DISCOVERY.md` for the next research phase. It does not retroactively change claims supported by `EXPERIMENT_PROTOCOL_V3.md` or the current manuscript.

---

## 1. Research decision

The next DynNav paper should **not** be framed as a better A* planner, a first history-aware planner, a first safe-return planner, a first POMDP navigation method, or a first model in which actions change the environment.

The strongest defensible next question is:

> **When a robot's executed actions can arm latent stochastic topology hazards, and the arming state is only partially observed, what information must the planner retain to estimate and preserve safe-return connectivity?**

The corresponding representation progression is

[
x_t
;longrightarrow;
(x_t,A_t)
;longrightarrow;
(x_t,b_t),
]

where

- (x_t) is the observed geometric state,
- (A_t) is the latent set of armed action-triggered hazards,
- (b_t(A)=P(A_t=Amid h_t)) is the posterior belief over that latent environmental state given the robot's action/observation history (h_t).

The scientific object is not generic path risk. It is the probability that a designated safe set remains connected after future topology realizations:

[
R(x,A)=P(xleadsto mathcal S_{mathrm{safe}}mid A)
]

and, under partial observation,

[
R(x,b)=mathbb E_{Asim b}[R(x,A)].
]

This is a **representation and information-state question**. The planner is an experimental instrument for testing it.

---

## 2. What the current repository already establishes

The current repository has an unusually strong mechanism-level substrate for this question:

1. an explicit action-triggered hazard model;
2. exact small-hazard return-connectivity enumeration;
3. augmented-state search over position and activated hazards;
4. a same-oracle state-only control that isolates representation from estimator quality;
5. paired common-random-number evaluation;
6. retained raw artifacts and a claim/evidence manifest;
7. negative results for hard safe-return constraints;
8. an explicit approximation counterexample;
9. ROS 2/Nav2 integration and a frozen Gazebo execution protocol.

The current paper's primary retained synthetic result is therefore useful as a **known-activation reference condition**, not as evidence that the partial-observation extension will work.

The current evidence must retain its existing scope:

- synthetic / computational mechanism evidence;
- no physical-robot efficacy claim;
- no safety certification;
- no arbitrary-map generalization;
- no universal superiority claim.

The current Gazebo results remain integration/measurement evidence, not comparative efficacy evidence.

---

## 3. Critical audit of the current partial-observation prototype

The repository already contains `dynnav/activation_belief.py` and `dynnav/experiments/noisy_activation_benchmark.py`. That work is useful, but it is **not yet a publication-facing belief-conditioned planning result**.

### What is already sound

The prototype correctly separates, at code level:

- a latent binary event,
- a noisy observation,
- a later closure event,
- Bayesian updating,
- posterior-predictive return probability,
- Brier-score evaluation,
- an oracle-information reference.

It also explicitly warns that it is a mechanism benchmark rather than a new POMDP algorithm.

### Main conceptual weakness

The existing prototype describes uncertainty as whether a commanded trigger edge was *physically crossed*. In the main DynNav grid model, however, the planner usually treats geometric state as observed. If the robot is known to have moved from the source cell to the target cell, uncertainty about whether that edge was crossed can become artificial unless localization/execution itself is also modeled as partially observed.

For the next paper, the cleaner latent variable is therefore **hazard arming after a known trigger execution**, not uncertain geometric crossing.

The revised causal chain should be:

[
	ext{known trigger execution}
ightarrow
	ext{latent hazard arming}
ightarrow
	ext{noisy arming evidence}
ightarrow
	ext{future topology realization}.
]

This admits realistic mechanisms such as:

- a door latch being armed but not directly visible;
- a gate controller receiving or failing to receive a trigger;
- a traversed surface becoming destabilized with uncertain internal state;
- a robot action changing the probability of a later obstruction without immediate observable geometry change.

A second, separate robotics experiment may model missed executed-transition observations or localization uncertainty. Those should not be conflated with latent environmental arming.

### Main experimental weakness

The current noisy-activation benchmark evaluates probability estimates and a fixed decision threshold. It does **not** yet show that belief state changes route selection, return connectivity, or mission outcomes in a multi-step navigation problem.

That is the central missing experiment.

---

## 4. Literature review method and limits

This review was performed as a targeted novelty audit rather than a formal systematic review. Search families included combinations of:

- safe return / returnability / safe exploration;
- POMDP robot navigation and uncertain roadmaps;
- history-dependent robot risk;
- traversal-dependent / self-deleting graphs;
- robot-induced obstacles;
- stochastic dynamic topology;
- endogenous / decision-dependent uncertainty;
- uncertain obstacles and noisy sensing;
- correlated stochastic obstacles;
- contingency / backup-plan planning;
- action-dependent component failure.

The review used publisher pages, proceedings pages, DOI records, and author/institutional pages where available. It also checked work published through 2026.

This process can support a **bounded novelty position**, but not a claim that no overlapping paper exists. Before submission, backward/forward citation chaining should be repeated for the 5-6 closest works and logged.

---

## 5. Literature matrix

| Work | Core problem | State / belief | Action changes uncertainty? | Action changes topology? | Partial observation? | Explicit safe return? | Relevance / boundary for DynNav |
|---|---|---|---:|---:|---:|---:|---|
| Moldovan & Abbeel, *Safe Exploration in Markov Decision Processes*, ICML 2012, https://arxiv.org/abs/1205.4810 | Safe exploration in non-ergodic MDPs | MDP state/policy | not the central mechanism | no | uncertain dynamics | returnability/ergodicity-based safety | Safe return / returnability is established prior art. |
| Kneebone & Dearden, *Navigation Planning in Probabilistic Roadmaps with Uncertainty*, ICAPS 2009, https://doi.org/10.1609/icaps.v19i1.13359 | Navigation with uncertain PRM edges and noisy edge observations | POMDP belief over uncertain edges | observations depend on traversal | no action-induced latent topology process | yes | no explicit return objective | Strong constraint on novelty of belief-space navigation with noisy topology information. |
| Axelrod, Kaelbling & Lozano-Pérez, *Provably Safe Robot Navigation with Obstacle Uncertainty*, RSS 2017, https://doi.org/10.15607/RSS.2017.XIII.023 | Safety with imperfect obstacle observations | observation-conditioned safety model | no | no | yes | safety, not the same return-connectivity objective | Uncertain-obstacle safety and observation-conditioned guarantees are established. |
| Xiao, Dufek & Murphy, *Robot Risk-Awareness by Formal Risk Reasoning and Planning*, RA-L 2020, https://doi.org/10.1109/LRA.2020.2974434 | Formal locale/action/traverse-dependent motion risk | history-sensitive path representation | yes | not future environmental topology in DynNav's sense | not the main contribution | no | Direct constraint: “history matters” and action/traverse-dependent risk are not novel claims. |
| Kameyama et al., *Active Modular Environment for Robot Navigation*, ICRA 2021, https://doi.org/10.1109/ICRA48506.2021.9561111 | Navigation in an active environment with stochastic topology change | distributed environment representation | environment is active; not DynNav trigger semantics | yes, dynamically | online dynamic state | no | Stochastic topology change in robot navigation is established. |
| Liu et al., *Self-protective motion planning for mobile manipulators in a dynamic door-closing workspace*, Industrial Robot 2021, https://doi.org/10.1108/IR-02-2021-0025 | Planning under an uncertain door-closing workspace | POMDP / belief tree | robot-environment interaction is modeled | dynamic workspace | yes | escape/self-protection, not DynNav return-connectivity formulation | Important near-neighbor: POMDP reasoning about a closing topology-like workspace is not new. |
| Zhang & Guo, *Online Planning of Uncertain MDPs under Temporal Tasks and Safe-Return Constraints*, CDC 2022, https://doi.org/10.1109/CDC51059.2022.9993378 | Bayesian online planning in an uncertain MDP with safe-return constraints | Bayesian uncertain-MDP model | policy affects visited information | not the specific action-armed topology mechanism | uncertainty is learned online | yes | Strong constraint: uncertainty + Bayesian update + explicit safe return already coexist. |
| Guo et al., *Hierarchical Motion Planning Under Probabilistic Temporal Tasks and Safe-Return Constraints*, IEEE TAC 2023, https://doi.org/10.1109/TAC.2023.3244884 | Probabilistic temporal tasks with outbound/return policies | MDP/product abstractions | not DynNav's endogenous topology variable | no | probabilistic labels | yes | Strong safe-return prior art with theory and hardware experiments. |
| Nohadani & Sharma, *Optimization under Decision-Dependent Uncertainty*, SIAM J. Optimization, https://doi.org/10.1137/17M1110560 | Optimization where decisions alter uncertainty sets; includes shortest path | optimization decision state | yes | not specifically robot topology | no | no | Decision-dependent / endogenous uncertainty is not a novel generic claim. |
| Baldes et al., *A Model for Optimal Resilient Planning Subject to Fallible Actuators*, 2024, https://arxiv.org/abs/2405.11402 | MDP planning where actuator use changes future failure exposure | state includes component condition | yes | changes future control capability, not environment topology | not the central issue | resilience, not safe return | Shows action-dependent future capability risk is established. |
| Tao et al., *Backup Plan Constrained Model Predictive Control with Guaranteed Stability*, JGCD 2024, https://doi.org/10.2514/1.G007627 | Maintain alternative/backup mission feasibility | MPC with multiple horizons | actions affect feasibility | no specific latent topology process | model uncertainty, not hidden activation state | backup feasibility | Backup/contingency feasibility is established. |
| Jung, Estornell & Everett, *Contingency Constrained Planning with MPPI within MPPI*, L4DC 2025, https://proceedings.mlr.press/v283/jung25a.html | Nominal planning with embedded contingency planning | sampling-based trajectory optimization | policy affects future contingency feasibility | no DynNav-specific latent topology mechanism | not the central variable | contingency safety | Another strong constraint on generic “keep a backup” claims. |
| Dvořák et al., *Pathfinding in Self-Deleting Graphs*, ISAAC 2025, https://doi.org/10.4230/LIPIcs.ISAAC.2025.28 | Pathfinding when visited vertices delete future edges | traversal-dependent residual graph | yes | yes, deterministically | no | no | Direct topology-side constraint: traversal-dependent graph change is established. |
| Zhou & Ceyhan, *Stochastic Path Planning in Correlated Obstacle Fields*, arXiv 2025, https://arxiv.org/abs/2509.19559 | Correlated uncertain obstacles with noisy sensing and Bayesian updates | posterior obstacle belief | observations/actions gather information | obstacle state is exogenous rather than armed by robot actions | yes | no explicit safe-return objective | Correlation-aware uncertain-obstacle belief planning is active prior art. Treat as preprint. |
| Frenkel, Parker & Mansouri, *Coverage with Self-Induced Obstacles on Grids*, RA-L 2026, https://doi.org/10.1109/LRA.2026.3656776 | Robot actions create future non-traversable structure | self-deleting graph representation | yes | yes, deterministically | no | no | Closest robotics prior art on robot-induced topology; rules out broad “actions modify topology” novelty. |
| Lamarre & Kelly, *Risk-averse traversal of graphs with stochastic and correlated edge costs for safe global planetary mobility*, Autonomous Robots 2026, https://doi.org/10.1007/s10514-025-10240-5 | Risk-averse traversal of stochastic/correlated uncertain graphs | policy over uncertain graph state | mainly information revelation / exogenous edge uncertainty | not action-armed topology | partially revealed uncertainty | safety/risk rather than DynNav safe-return connectivity | Strong uncertain-graph comparator, especially for correlation. |

---

## 6. Closest competing formulations

There is no single paper in the reviewed set that can be dismissed as “the same problem with a different implementation.” Instead, the overlap is distributed across four mature lines:

### 6.1 Safe return under uncertainty

Zhang & Guo and Guo et al. already combine uncertainty with explicit high-probability return policies. DynNav therefore cannot claim that safe-return planning under uncertainty is new.

### 6.2 Belief-space navigation with noisy topology information

Kneebone & Dearden already formulate uncertain graph-edge navigation with noisy observations as a POMDP. Axelrod et al. and later uncertain-obstacle work also make observation-conditioned safety central. DynNav cannot claim that maintaining a belief over uncertain traversability is new.

### 6.3 Traversal/action-dependent topology

Self-deleting graphs and the 2026 self-induced-obstacle robotics paper establish that the robot's own traversal can change future graph feasibility. DynNav cannot claim that robot history changing topology is new.

### 6.4 Endogenous / decision-dependent uncertainty

Decision-dependent uncertainty is a mature optimization concept, and action-dependent future failure exposure also appears in robotics. DynNav cannot claim that decisions changing future uncertainty is new.

---

## 7. The defensible research gap

The reviewed literature leaves a narrower intersection that is scientifically meaningful:

> **Safe-return connectivity when robot actions create a latent environmental hazard state that changes the distribution of future topology, and that action-induced latent state is itself only partially observable.**

The important causal structure is

[
u_t
ightarrow
A_{t+1}
ightarrow
C_{mathrm{future}}
ightarrow
	ext{return connectivity},
]

with observations

[
A_t ightarrow o_t
]

and with (A_t) not generally recoverable from geometric state (x_t) alone.

This differs from:

- exogenous uncertain obstacles, because the distribution changes due to robot actions;
- deterministic self-deleting graphs, because the action changes a latent stochastic environmental state rather than immediately deleting a known edge;
- generic history-dependent risk, because the quantity of interest is future safe-set connectivity of the environment;
- generic safe-return MDPs, because the hidden state specifically records endogenous topology exposure caused by execution;
- generic POMDP navigation, because the research question is not POMDP solution methodology but the value and calibration of this specific action-induced environmental information state.

### Publication-safe wording

Use:

> “Existing work studies safe return, belief-space navigation, traversal-dependent topology, and decision-dependent uncertainty separately and in partially overlapping combinations. We study the narrower case in which executed robot actions create a latent stochastic environmental state governing future return connectivity, and that action-induced state is only partially observed.”

Do **not** use:

- “first belief-aware safe-return planner”;
- “first partially observable dynamic-topology planner”;
- “first action-dependent uncertainty model”;
- “first robot-induced topology planner”;
- “no previous work considers this problem.”

---

## 8. Revised minimum model

Let the environment be a graph (G=(V,E)), current robot state (x_tin V), and safe set (mathcal S_{mathrm{safe}}subseteq V).

Each hazard (i) has:

[
h_i=(e_i,q_i,c_i,p_i),
]

where

- (e_i) is a directed trigger transition;
- (q_i) is the probability that executing (e_i) arms hazard (i);
- (c_i) is the future closure cell/event associated with the hazard;
- (p_i) is the probability of closure conditional on hazard (i) being armed.

### Latent arming

When the robot executes (e_i),

[
A_{i,t+1} =
A_{i,t}lor B_{i,t},
qquad
B_{i,t}sim mathrm{Bernoulli}(q_i).
]

Arming is monotone in the first model. This keeps the state small and makes the causal semantics auditable.

The original DynNav model is recovered by setting (q_i=1).

### Noisy observation

After trigger execution, the robot receives (Y_{i,t}in{0,1}) with

[
P(Y=1mid A_i=1)=s_i
]

and

[
P(Y=0mid A_i=0)=c_i^{mathrm{obs}},
]

where (s_i) is sensitivity and (c_i^{mathrm{obs}}) is specificity.

Use different notation in code for closure cell and observation specificity to avoid collision.

### Belief

[
b_t(A)=P(A_t=Amid u_{0:t-1},y_{0:t}).
]

Under known model parameters, Markov arming dynamics, conditionally independent observation likelihoods, known current geometric state, and no other hidden variables relevant to future closures, ((x_t,b_t)) is the standard sufficient information state for this finite partially observed model. This is an application of standard belief-state Markovization, **not a novelty claim**.

### Return probability

For known activation state,

[
R(x,A)=
Pleft[
exists 	ext{ path } xleadsto mathcal S_{mathrm{safe}}
	ext{ after future closures}
mid A
ight].
]

For belief state,

[
R(x,b)=sum_A b(A)R(x,A).
]

This is the posterior-predictive return reliability under the specified model.

---

## 9. Correlated closures are a second, distinct information problem

A belief over activation state does not solve model error from assuming independent closure realizations.

The current exact oracle assumes independent Bernoulli closures. Connectivity is nonlinear, so matching marginal closure probabilities is not enough.

A minimal counterexample uses two redundant return corridors with identical marginal closure probability (p).

If closures are independent,

[
P(	ext{return})=1-p^2.
]

If the two closures are perfectly positively correlated with the same marginals,

[
P(	ext{return})=1-p.
]

Therefore the same marginal map can imply different safe-return reliability.

This motivates a secondary question:

> How much calibration and decision error is caused by replacing the joint distribution of future topology with independent marginals?

This should be treated as a separate factor from partial observability of activation.

---

## 10. Research questions

### RQ1 — Representation

When action-triggered hazard arming is latent, does a posterior belief over arming state contain return-connectivity information that is lost by geometric or fixed-marginal representations?

### RQ2 — Decision value

Does using that belief change route choices and improve the risk/cost frontier relative to treating detector output as ground truth or ignoring observations?

### RQ3 — Calibration

Are posterior-predictive safe-return probabilities calibrated under a correctly specified model, and how do they degrade under sensor/model misspecification?

### RQ4 — Correlation

How much error results from independent-closure assumptions when the true future topology has correlated closures with the same marginals?

### RQ5 — Boundary conditions

In which regimes does belief tracking provide no value, become overconservative, or become computationally impractical?

---

## 11. Falsifiable hypotheses

The hypotheses are deliberately written so that the preferred method can fail.

### H1 — hidden-state information gap

There exist same-position histories whose posterior beliefs (b_1,b_2) produce distinct posterior-predictive return reliabilities:

[
R(x,b_1)
eq R(x,b_2).
]

An estimator restricted to (x) cannot represent both exactly.

**Falsification signal:** if all tested posterior differences collapse once the state-only baseline is properly conditioned on all information it is legitimately allowed to use, the claimed representation gap is not demonstrated.

### H2 — calibration under correct specification

With informative observations and correctly specified arming/observation/closure parameters, the exact belief model has lower paired Brier loss for return feasibility than detector-as-truth and fixed-prior approximations.

**Falsification signal:** no robust Brier improvement across the predeclared held-out regime.

### H3 — operational value is conditional, not universal

Under intermediate observation noise, belief-conditioned planning improves return-infeasibility at a measurable path-cost tradeoff relative to detector-as-truth. At perfect sensing and in history-irrelevant worlds the methods should converge.

**Falsification signal:** no operational gain in the target intermediate-noise regime, or unexplained differences in perfect-sensing/no-history controls.

### H4 — misspecification can reverse the advantage

A Bayesian posterior with wrong sensor or arming parameters can become miscalibrated and may be worse than a conservative prior-only rule.

**Falsification signal:** the predeclared misspecification grid shows no meaningful calibration or decision degradation.

### H5 — marginal closure maps are insufficient under correlation

For redundant-return topologies, two joint closure models with equal marginals can produce materially different return reliability.

**Falsification signal:** the chosen topology does not produce a measurable joint-distribution effect; redesign is allowed only before the held-out protocol is frozen.

### H6 — exact belief planning has a practical scaling boundary

Runtime and memory increase sharply with hazard/belief support size; exact belief planning will cease to be practical beyond a measurable regime.

**Falsification signal:** exact inference remains cheap over the entire declared range; this is a useful negative result and would remove motivation for approximation work.

---

## 12. Theory worth pursuing

The paper does not need new POMDP theory. Theory should be limited to statements specific enough to clarify the DynNav information problem.

### 12.1 Hidden-state aliasing lower bound

Let two observation histories end at the same (x) with posterior-predictive return values (R_1) and (R_2). Any deterministic estimator (g(x)) satisfies

[
max(|g(x)-R_1|,|g(x)-R_2|)
ge
rac{|R_1-R_2|}{2}.
]

This is the same elementary triangle-inequality argument as the known-history result, now applied to belief-conditioned values. It is a representation lemma, not new state-abstraction theory.

### 12.2 Belief sufficiency proposition

State the assumptions under which ((x,b)) is sufficient and explicitly list violations:

- unknown/changing sensor parameters;
- hidden time-to-closure state;
- non-Markov arming dynamics;
- unmodeled correlation/common causes;
- uncertain robot pose coupled to trigger execution;
- observation histories that affect the future beyond (A).

### 12.3 Equal marginals do not determine connectivity

Use a minimal redundant-path construction to prove that equal per-cell closure marginals can yield different return probabilities under different joint distributions.

This is useful because it directly justifies the correlated-hazard experiment.

---

## 13. Experiments that could invalidate the research claim

The V4 study must include cases where DynNav should not win.

Required null/negative regimes:

1. no triggers;
2. triggers whose closures are not return-critical;
3. perfect activation observation;
4. completely uninformative observation;
5. zero arming probability;
6. zero closure probability;
7. only one mission-feasible path;
8. belief model deliberately misspecified;
9. state-only representation supplied with the full latent state as a sanity control (it should then cease to be “state only” and match the oracle);
10. correlated closure cases evaluated with an independent model;
11. long safe detours where risk reduction may not justify path cost;
12. high-hazard cases where every method must accept substantial residual risk.

A paper with only constructed trigger traps would not be sufficient.

---

## 14. Evidence required for a strong robotics paper

Minimum publication evidence should include:

### A. Mathematical mechanism

- known-history aliasing;
- hidden-activation aliasing;
- belief sufficiency assumptions;
- equal-marginal correlation counterexample.

### B. Controlled synthetic planning

- multiple topology families;
- multi-step route selection, not only one-step probability estimation;
- perfect, intermediate, and severe observation noise;
- null cases;
- model misspecification;
- correlation.

### C. Strong baselines

- shortest path;
- fixed-marginal exact;
- oracle activation state;
- detector-as-truth;
- belief-conditioned exact;
- hard belief-safe-return;
- a stronger POMDP/belief-space comparator if one can be matched fairly to the same discrete model.

### D. Statistical integrity

- common random numbers;
- scenario-level inference;
- hierarchical bootstrap;
- raw denominators and effect sizes;
- calibration metrics;
- no outcome-based sample-size changes.

### E. Execution-level evidence

Gazebo should test noisy trigger/arming observations rather than reusing the old perfect-history mechanism probe.

A physical robot is desirable but not mandatory for the first belief-state paper if the paper is explicit that the contribution is representation/modeling plus controlled robotic-stack validation.

---

## 15. Current claims that should be weakened, removed, or kept separate

For the V4 paper:

### Remove / do not introduce

- “DynNav is a POMDP planner” as a novelty statement;
- “belief-conditioned planning is new”;
- “partial observability is the research gap” without the action-induced latent topology qualifier;
- “Bayesian activation tracking is novel”;
- “history-aware planning is universally safer”;
- “the exact belief planner is deployable at arbitrary scale”;
- “correlated hazard handling is novel” unless a specific new algorithmic result is actually developed.

### Keep, but narrowly

- executed actions can create different future return-connectivity distributions;
- position-only representations can alias those histories;
- exact activation state can be represented by an augmented state;
- under partial observation, a posterior over action-induced latent environmental state is the appropriate information object under stated assumptions;
- a fixed-marginal map can lose information;
- equal closure marginals do not generally determine network reliability.

### Keep separate from V4 until new evidence exists

- comparative Gazebo efficacy;
- hardware efficacy;
- real-world probability calibration;
- formal kinodynamic safety;
- arbitrary-map generalization.

---

## 16. Implementation implications

Do not simply extend the existing `ActivationBelief` API without revisiting its semantics.

Recommended code model:

```text
TriggerExecution
    known edge / action executed
        |
        v
HazardArmingModel
    P(armed | trigger execution) = q
        |
        +------> ActivationObservationModel
        |        P(y | armed)
        |
        v
ActivationBelief
    b(A)
        |
        v
FutureClosureModel
    P(C | A), independent or joint
        |
        v
ReturnConnectivityOracle
    P(return | x, b)
```

Separate interfaces should prevent accidental truth leakage between:

- simulator ground truth;
- planner observation;
- planner belief;
- post-hoc evaluator.

The oracle planner may read truth only in its explicitly named oracle condition.

---

## 17. Go / no-go criteria for the next paper

Proceed toward a belief-conditioned paper only if the frozen V4 study demonstrates all of the following:

1. the belief representation changes route choice in nontrivial multi-step worlds;
2. the effect survives at least several topology families outside serial commitment modules;
3. correct belief tracking improves calibration relative to point-estimate baselines in the target noise regime;
4. operational benefits are visible in at least one predeclared intermediate-noise regime;
5. null controls behave as expected;
6. model misspecification produces documented failure boundaries;
7. the computational scaling is characterized honestly;
8. Gazebo can reproduce the observation/arming semantics without hidden ground-truth leakage.

If 1-4 fail, do **not** force the manuscript around belief conditioning. The scientifically stronger outcome would be to keep the existing known-history paper and publish the partial-observation study as a negative/robustness result if it is independently interesting.

---

## 18. Recommended paper identity, contingent on evidence

Preferred working title:

> **When the Same Place Is Not the Same Belief: Safe-Return Planning under Partially Observed Action-Triggered Topology Hazards**

More conservative alternative:

> **Belief-Conditioned Safe-Return Planning under Action-Induced Stochastic Topology State**

The final title should be chosen after the frozen experiments, not before.

---

## 19. Immediate next step

Freeze `EXPERIMENT_PROTOCOL_V4.md` before implementing publication-facing planner comparisons.

No current manuscript claim should be expanded based on this document alone.
