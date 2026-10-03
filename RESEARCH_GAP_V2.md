# Research Gap V2 — Belief-Conditioned Safe Return under Action-Induced Latent Topology State

**Status:** research decision document  
**Literature screen:** updated 2026-10-03  
**Branch:** \`research/belief-conditioned-v4\`

## 1. Research decision

The next DynNav study should not be framed as a better A* planner, a first history-aware planner, a first safe-return planner, a first POMDP navigation method, or a first model in which actions change the environment.

The strongest defensible next question is:

> **When a robot's executed actions can arm latent stochastic topology hazards, and that arming state is only partially observed, what information must the planner retain to estimate and preserve safe-return connectivity?**

The representation progression is

\[
x_t \;\longrightarrow\; (x_t,A_t) \;\longrightarrow\; (x_t,b_t),
\]

where \(x_t\) is geometric state, \(A_t\) is the latent armed-hazard state, and

\[
b_t(A)=P(A_t=A\mid u_{0:t-1},o_{0:t})
\]

is the posterior belief over that environmental state.

The scientific object is not generic path risk. It is the probability that a designated safe set remains reachable after future topology realizations:

\[
R(x,A)=P(x\leadsto \mathcal S_{\mathrm{safe}}\mid A),
\]

and under partial observation

\[
R(x,b)=\sum_A b(A)\,R(x,A).
\]

This is a **representation and information-state problem**. The planner is an experimental instrument for testing it.

## 2. What the current repository already establishes

The V3 repository already provides:

- action-triggered hazards;
- exact small-hazard return-connectivity enumeration;
- augmented-state search over \((x,A)\);
- a same-oracle state-only fixed-field control;
- common-random-number evaluation;
- retained raw artifacts and provenance;
- hard safe-return negative results;
- approximation counterexamples;
- ROS 2/Nav2 and Gazebo integration.

The current primary V3 result is therefore a **known-activation reference condition**, not evidence that the V4 partial-observation method works.

Existing scope must remain unchanged:

- computational/synthetic mechanism evidence;
- no physical-robot efficacy claim;
- no certification claim;
- no arbitrary-map generalization;
- no universal superiority claim.

## 3. Critical audit of the current partial-observation prototype

The branch already contains \`dynnav/activation_belief.py\` and a noisy-activation mechanism benchmark. They are useful research scaffolding but are not yet publication-facing belief-conditioned planning evidence.

### 3.1 What is scientifically sound

The code separates:

1. latent binary environmental state;
2. noisy observation;
3. future closure realization;
4. Bayesian update;
5. posterior-predictive return probability.

This separation is the right direction.

### 3.2 Main conceptual correction

A weaker formulation makes uncertainty about whether a commanded trigger edge was physically crossed. That is questionable if the planning model otherwise assumes the robot's geometric transition is observed.

The cleaner latent variable is **hazard arming after a known trigger execution**.

The V4 causal model should be

\[
\text{known trigger execution}
\rightarrow
\text{latent hazard arming}
\rightarrow
\text{noisy arming evidence}
\rightarrow
\text{future closure realization}.
\]

This has realistic interpretations:

- a latch is armed but not directly visible;
- a controller may or may not accept a trigger;
- traversing terrain may or may not destabilize a later return corridor;
- an action may change the probability of a later obstruction without changing current geometry.

Localization uncertainty or missed executed-transition observations can be studied separately. They should not be conflated with latent environmental arming.

### 3.3 Main missing experiment

The existing mechanism benchmark scores probability estimates. It does not yet establish that a posterior over latent arming changes **multi-step route selection, return connectivity, or mission outcome**.

That is the core missing experiment.

## 4. Literature audit

This is a targeted novelty audit, not a proof that no overlapping work exists.

The closest literature constrains the contribution in four directions.

### 4.1 Safe return / returnability is established

Moldovan & Abbeel established returnability as part of safe exploration. Zhang & Guo study uncertain MDP planning with safe-return constraints. Guo et al. synthesize outbound and return policies under probabilistic temporal tasks.

Key sources:

- Moldovan & Abbeel, *Safe Exploration in Markov Decision Processes*, ICML 2012.
- Zhang & Guo, *Online Planning of Uncertain MDPs under Temporal Tasks and Safe-Return Constraints*, CDC 2022/2023 preprint line.
- Guo et al., *Hierarchical Motion Planning Under Probabilistic Temporal Tasks and Safe-Return Constraints*, IEEE TAC 2023, DOI 10.1109/TAC.2023.3244884.

**Constraint:** DynNav cannot claim novelty for safe return under uncertainty.

### 4.2 Belief-space navigation with noisy topology information is established

Kneebone & Dearden model uncertain PRM edges with noisy observations as a POMDP. Axelrod et al. study provably safe navigation under obstacle uncertainty.

Key sources:

- Kneebone & Dearden, ICAPS 2009, DOI 10.1609/icaps.v19i1.13359.
- Axelrod, Kaelbling & Lozano-Pérez, RSS 2017, DOI 10.15607/RSS.2017.XIII.023.

**Constraint:** belief-space reasoning over uncertain traversability is not itself novel.

### 4.3 History-dependent risk and action-induced topology are established

Xiao, Dufek & Murphy formalize locale-, action-, and traverse-dependent risk. Self-deleting graph work studies traversal-dependent graph change. Frenkel et al. apply self-induced obstacles to robotics coverage.

Key sources:

- Xiao, Dufek & Murphy, RA-L 2020, DOI 10.1109/LRA.2020.2974434.
- Dvořák et al., *Pathfinding in Self-Deleting Graphs*, ISAAC 2025, DOI 10.4230/LIPIcs.ISAAC.2025.28.
- Frenkel, Parker & Mansouri, *Coverage with Self-Induced Obstacles on Grids*, RA-L 2026, DOI 10.1109/LRA.2026.3656776.

**Constraint:** “history matters” and “robot actions change topology” are not novel claims.

### 4.4 Stochastic/correlated uncertain graph traversal is established

AFADA studies navigation in a dynamic environment with stochastic topology change. Lamarre & Kelly study risk-averse traversal with stochastic and correlated edge costs. Zhou & Ceyhan study correlated obstacle fields with noisy sensing and Bayesian updates.

Key sources:

- Kameyama et al., ICRA 2021, DOI 10.1109/ICRA48506.2021.9561111.
- Lamarre & Kelly, *Autonomous Robots* 2026, DOI 10.1007/s10514-025-10240-5.
- Zhou & Ceyhan, arXiv:2509.19559 (preprint; treat accordingly).

**Constraint:** stochastic topology, correlation, information gathering, and Bayesian uncertain-graph reasoning are all active prior art.

### 4.5 Decision-dependent uncertainty is established

Nohadani & Sharma explicitly formulate decision-dependent uncertainty and include a shortest-path example.

- Nohadani & Sharma, *Optimization under Decision-Dependent Uncertainty*, SIAM Journal on Optimization, DOI 10.1137/17M1110560.

**Constraint:** DynNav cannot claim the general concept that actions alter future uncertainty.

## 5. Literature matrix

| Work | Uncertainty source | Action-dependent? | Topology-changing? | Partial observation? | Explicit return objective? | Boundary for DynNav |
|---|---|---:|---:|---:|---:|---|
| Moldovan & Abbeel 2012 | uncertain/non-ergodic MDP | not central | no | model uncertainty | yes/returnability | safe-return concept established |
| Kneebone & Dearden 2009 | uncertain PRM edges | information depends on traversal | not action-induced | yes | no | POMDP navigation on uncertain graph established |
| Axelrod et al. 2017 | obstacle uncertainty | no | no | yes | safety, not return | observation-conditioned navigation safety established |
| Xiao et al. 2020 | motion risk | yes | not DynNav topology | not central | no | action/traverse-dependent risk established |
| Kameyama et al. 2021 | stochastic dynamic topology | environment-driven | yes | online | no | stochastic topology navigation established |
| Liu et al. 2021 | uncertain door-closing workspace | interaction-aware | dynamic workspace | yes/POMDP | escape/self-protection | POMDP + closing workspace is near-neighbor prior art |
| Zhang & Guo 2022/23 | uncertain MDP | policy affects information | no specific action-armed topology | Bayesian | yes | uncertainty + safe return established |
| Guo et al. 2023 | probabilistic task/MDP | not DynNav mechanism | no | probabilistic model | yes | strong safe-return comparator |
| Nohadani & Sharma | decision-dependent uncertainty | yes | general optimization | no | no | endogenous uncertainty established |
| Jung et al. 2025 | contingency feasibility | actions affect future feasibility | no DynNav mechanism | not central | contingency | “keep a backup” is established |
| Dvořák et al. 2025 | traversal-dependent graph | yes | deterministic deletion | no | no | topology-side novelty constraint |
| Frenkel et al. 2026 | self-induced obstacles | yes | deterministic | no | no | closest robotics action-induced-topology comparator |
| Lamarre & Kelly 2026 | stochastic/correlated graph costs | mainly information revelation | exogenous uncertainty | partially revealed | risk, not safe return | strong correlated-graph comparator |
| Zhou & Ceyhan 2025 preprint | correlated uncertain obstacles | information-gathering actions | exogenous obstacles | yes | no | correlation-aware Bayesian planning constraint |

## 6. Defensible research gap

The literature leaves a narrower intersection:

> **Safe-return connectivity when robot actions create a latent environmental state that changes the distribution of future topology, and that action-induced latent state is itself only partially observed.**

The causal structure is

\[
u_t \rightarrow A_{t+1} \rightarrow C_{\mathrm{future}}
\rightarrow \text{return connectivity},
\]

with observations

\[
A_t \rightarrow o_t.
\]

The distinction is specific:

- unlike exogenous uncertain obstacles, the uncertainty distribution is changed by robot execution;
- unlike deterministic self-deleting graphs, execution does not immediately reveal a deterministic residual graph;
- unlike generic history-dependent motion risk, the quantity of interest is future safe-set connectivity;
- unlike generic safe-return MDPs, the hidden state is an action-induced topology-exposure state;
- unlike generic POMDP navigation, the research target is the value and calibration of this specific latent environmental information state.

### Publication-safe wording

Use:

> Existing work studies safe return, belief-space navigation, traversal-dependent topology, stochastic graph traversal, and decision-dependent uncertainty in partially overlapping forms. We study the narrower case in which executed robot actions create a latent stochastic environmental state governing future return connectivity, and that action-induced state is only partially observed.

Do not use “first” language unless a later formal systematic review justifies it.

## 7. Minimum V4 model

Let \(G=(V,E)\), robot state \(x_t\in V\), and safe set \(\mathcal S_{\mathrm{safe}}\subseteq V\).

Hazard \(i\) is

\[
h_i=(e_i,q_i,c_i,p_i),
\]

where:

- \(e_i\): known directed trigger transition;
- \(q_i\): probability the executed trigger arms hazard \(i\);
- \(c_i\): closure cell/event;
- \(p_i\): closure probability conditional on arming.

### 7.1 Latent arming

For binary armed state \(A_{i,t}\),

\[
A_{i,t+1}=A_{i,t}\lor B_{i,t},
\qquad
B_{i,t}\sim \operatorname{Bernoulli}(q_i)
\]

when \(e_i\) is executed.

The original V3 model is the special case \(q_i=1\).

### 7.2 Observation

After trigger execution,

\[
P(Y_i=1\mid A_i=1)=s_i,
\]

\[
P(Y_i=0\mid A_i=0)=c_i^{\mathrm{obs}},
\]

with sensitivity \(s_i\) and specificity \(c_i^{\mathrm{obs}}\).

### 7.3 Belief

\[
b_t(A)=P(A_t=A\mid u_{0:t-1},y_{0:t}).
\]

Under known model parameters, Markov arming dynamics, a known geometric state, and conditionally independent observations with no omitted hidden variables relevant to future closure, \((x_t,b_t)\) is the standard sufficient belief state.

This is standard belief-state Markovization, not a novelty claim.

### 7.4 Posterior-predictive safe return

\[
R(x,b)=\sum_A b(A)\,R(x,A).
\]

This value is exact only relative to the specified activation and closure models.

## 8. Correlated closures are a separate second problem

Partial observability of activation and correlation among future closures are distinct.

Equal per-cell marginals do not determine network reliability. For two redundant return corridors, each with marginal closure probability \(p\):

Independent closures:

\[
P(\text{return})=1-p^2.
\]

Perfectly positively correlated closures with the same marginals:

\[
P(\text{return})=1-p.
\]

Therefore an independent marginal field can be calibrated marginally but wrong about return connectivity.

The correlation study should test this as a separate model-misspecification axis.

## 9. Research questions

**RQ1 — Representation.** Does a posterior over latent action-induced hazard state contain return-connectivity information lost by geometric or fixed-marginal representations?

**RQ2 — Decision value.** Does that information change route selection and improve the risk/cost trade-off relative to detector-as-truth and fixed-prior methods?

**RQ3 — Calibration.** Are posterior-predictive safe-return probabilities calibrated under correct specification, and how do they degrade under sensor/model misspecification?

**RQ4 — Correlation.** How much connectivity-estimation and route-selection error is introduced by independent-closure assumptions under equal-marginal correlated hazards?

**RQ5 — Boundaries.** Where does belief tracking provide no value, become overconservative, or become computationally impractical?

## 10. Falsifiable hypotheses

### H1 — hidden-state aliasing

There exist observation histories ending at the same \(x\) with beliefs \(b_1,b_2\) such that

\[
R(x,b_1)\neq R(x,b_2).
\]

A deterministic estimator restricted to \(x\) cannot represent both exactly.

### H2 — calibration advantage under correct specification

For the predeclared intermediate-noise regime, exact belief tracking has lower paired Brier loss than detector-as-truth and fixed-prior approximations.

### H3 — conditional operational value

In nontrivial intermediate-noise worlds, belief-conditioned planning can reduce return-infeasibility at a measurable path-cost trade-off relative to detector-as-truth.

Perfect sensing and history-irrelevant worlds should collapse toward equivalence.

### H4 — misspecification boundary

Wrong sensor or arming parameters can remove or reverse the calibration/decision advantage of belief tracking.

### H5 — equal marginals are insufficient under correlation

In redundant-return topologies, different joint closure distributions with identical marginals produce materially different \(R\).

### H6 — exact belief inference has a practical scaling boundary

Exact categorical belief tracking eventually becomes computationally impractical as reachable support grows. If it does not within the declared range, approximation work is not justified.

## 11. Theory worth keeping

### 11.1 Hidden-state aliasing lower bound

If two histories at the same \(x\) induce posterior-predictive values \(R_1,R_2\), any deterministic endpoint-only scalar estimator \(g(x)\) satisfies

\[
\max(|g(x)-R_1|,|g(x)-R_2|)
\ge
\frac{|R_1-R_2|}{2}.
\]

This is an elementary representation bound, not new state-abstraction theory.

### 11.2 Belief sufficiency proposition

State the assumptions under which \((x,b)\) is sufficient and explicitly identify violations:

- unknown/changing sensor parameters;
- hidden time-to-closure state;
- non-Markov arming;
- unmodeled common causes/correlation;
- uncertain robot pose coupled to trigger execution;
- observations with predictive information not summarized by \(A\).

### 11.3 Equal marginals do not determine connectivity

Retain a minimal redundant-return counterexample. It directly motivates the correlation experiment.

## 12. Required falsification regimes

The V4 study must include conditions where the proposed method should not win:

1. no triggers;
2. triggers unrelated to return connectivity;
3. perfect observation;
4. uninformative observation;
5. \(q=0\);
6. \(p=0\);
7. only one feasible mission path;
8. severe model misspecification;
9. full latent-state access sanity control;
10. correlated closures evaluated with an independence model;
11. very costly safe detours;
12. unavoidable residual-risk scenarios.

A paper containing only trigger traps is not sufficient.

## 13. Baselines required for a strong paper

At minimum:

- shortest path;
- state-only fixed-marginal exact;
- oracle true-activation planner;
- detector-as-truth planner;
- exact belief-conditioned planner;
- hard belief-safe-return planner.

For small worlds, add an exact finite-horizon belief-policy reference if tractable. This is important because the main receding-horizon belief planner should not be presented as a general optimal POMDP solver.

## 14. Evidence required for publication

### Theory/mechanism

- known-history aliasing;
- hidden-activation aliasing;
- belief-sufficiency assumptions;
- equal-marginal correlation counterexample.

### Controlled planning

- multiple topology families;
- multi-step decisions;
- perfect/intermediate/severe observation noise;
- null cases;
- misspecification;
- correlated hazards.

### Statistics

- common random numbers;
- scenario-level and hierarchical inference;
- effect sizes and confidence intervals;
- Brier/calibration analysis;
- no outcome-based sample-size changes.

### Execution stack

Gazebo should implement the actual information barrier:

\[
\text{simulator truth} \not\rightarrow \text{non-oracle planner}.
\]

The planner receives only the observation channel allowed by its condition.

## 15. Claims to avoid

Do not claim:

- first POMDP safe-return planner;
- first history-dependent planner;
- first action-dependent uncertainty model;
- first robot-induced topology model;
- universal safety improvement;
- real-world calibrated probability;
- formal kinodynamic safety;
- arbitrary-map generalization;
- physical-robot efficacy without a separate retained hardware study.

## 16. Go/no-go criteria

A belief-conditioned paper is worth pursuing only if the frozen V4 study shows:

1. posterior state changes nontrivial multi-step route choice;
2. the effect occurs across several topology families;
3. calibration improves in the target correctly specified noise regime;
4. at least one predeclared intermediate-noise regime shows operational value;
5. null controls behave correctly;
6. misspecification exposes clear failure boundaries;
7. scaling is characterized honestly;
8. Gazebo can enforce the information barrier without truth leakage.

If items 1–4 fail, do not force the paper around belief conditioning. Retain the existing V3 paper and report V4 as a negative/robustness study if scientifically useful.

## 17. Working paper identity

Preferred working title:

> **When the Same Place Is Not the Same Belief: Safe-Return Planning under Partially Observed Action-Triggered Topology Hazards**

Conservative alternative:

> **Belief-Conditioned Safe-Return Planning under Action-Induced Stochastic Topology State**

The final title must follow the frozen results, not precede them.

## 18. Immediate decision

Freeze the V4 experimental protocol before any publication-facing V4 outcome is inspected. The existing prototype may be used for implementation development only; it is not publication evidence.
