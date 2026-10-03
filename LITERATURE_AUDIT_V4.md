# V4 Literature Audit — Novelty Boundary and Citation Chaining

**Status:** targeted pre-submission novelty audit  
**Search date:** 2026-10-03  
**Scope:** safe return, belief-space navigation, action/traversal-dependent risk, action-induced topology, stochastic topology, and decision-dependent uncertainty.

This is not a claim of exhaustive systematic-review coverage. Its purpose is to identify the closest conceptual competitors and constrain DynNav's claims before held-out V4 outcomes are inspected.

## 1. Search logic

The audit deliberately avoided searching only for project-specific wording such as "action-triggered topology hazard." Search concepts included:

- safe return / returnability / safe exploration under uncertainty;
- POMDP navigation with uncertain graph edges and noisy observations;
- history-, action-, and traverse-dependent robot risk;
- traversal-dependent / self-deleting graphs;
- robot-induced environmental obstacles;
- stochastic dynamic topology;
- decision-dependent / endogenous uncertainty and shortest path;
- dynamic door-closing workspaces modeled with POMDPs;
- correlated uncertain graph traversal.

Backward/forward chaining focused on the closest lines below.

## 2. Closest literature lines

| Line | Representative work | What is already established | Consequence for DynNav |
|---|---|---|---|
| Safe return / returnability | Moldovan & Abbeel, ICML 2012; Zhang & Guo, CDC 2022; Guo et al., IEEE TAC 2023 | Returnability and high-probability safe-return policies in uncertain MDPs | Safe return itself is not novel |
| Safe exploration with probabilistic processes | Stephens et al., *Autonomous Robots*, 2024 | Multi-step reachability/returnability reasoning under uncertain environmental processes | Uncertainty + returnability is not enough for novelty |
| Uncertain graph navigation / POMDP | Kneebone & Dearden, ICAPS 2009 | Noisy observations of uncertain roadmap edges represented as a POMDP; approximate belief-space planning | Belief over uncertain graph traversability is not novel |
| Obstacle uncertainty | Axelrod, Kaelbling & Lozano-Pérez, IJRR 2018 / RSS 2017 | Observation-conditioned navigation safety under imperfect obstacle information | Partial observation + navigation safety is not novel |
| History-dependent risk | Xiao, Dufek & Murphy, RA-L 2020 | Locale-, action-, and traverse-dependent risk; rejection of simplistic Markov/additive risk assumptions | "History matters" is not novel |
| Dynamic stochastic topology | Kameyama et al., ICRA 2021 | Navigation in an environment whose topology changes stochastically | Stochastic topology change is not novel |
| POMDP dynamic workspace | Liu et al., *Industrial Robot* 2021 | Belief-tree planning for self-protection in a dynamic door-closing workspace | A POMDP with a closing workspace is a direct near-neighbor |
| Traversal-dependent topology | Carmesin et al., J. Computational Science 2023; Dvořák et al., ISAAC 2025 | Visiting vertices can deterministically delete future edges; pathfinding complexity studied | Action/traversal-induced graph change is not novel |
| Robotics self-induced obstacles | Frenkel, Parker & Mansouri, RA-L 2026 | Robot task execution creates future non-traversable structure, modeled using self-deleting graphs | Closest robotics constraint on broad topology claims |
| Decision-dependent uncertainty | Nohadani & Sharma, SIAM J. Optimization | Decisions affect uncertainty sets; shortest-path example | Endogenous/decision-dependent uncertainty is not novel |
| General POMDP robotics | Kurniawati, Annual Review 2022 | Belief-state planning under action/state uncertainty is mature, with substantial solver literature | Belief-state Markovization is standard theory |

## 3. Citation-chain observations

### 3.1 Safe return

Moldovan & Abbeel make safe exploration depend on avoiding non-returnable behavior in non-ergodic MDPs. Later safe-exploration work explicitly extends reachability/returnability reasoning to multi-step probabilistic settings. Zhang & Guo and Guo et al. explicitly impose high-probability return-to-home/safe-return policies while reasoning under uncertainty.

**Boundary:** V4 must not claim that combining uncertainty and returnability is new.

### 3.2 Uncertain graph belief

Kneebone & Dearden already study a roadmap whose edges may be blocked and are observed noisily during traversal. They explicitly formulate the problem as a POMDP and develop an approximate belief-space method because exact solution does not scale.

**Boundary:** the contribution cannot be "maintain a belief over uncertain topology" or "use observations to update edge uncertainty."

### 3.3 Traversal-dependent topology

Carmesin et al. introduced traversal-dependent edge deletion. Dvořák et al. subsequently study pathfinding directly on self-deleting graphs. Frenkel et al. carry the same structural idea into robotics coverage, where the robot's task actions create obstacles that constrain future motion.

**Boundary:** the contribution cannot be "the robot's own path changes future traversability."

### 3.4 Dynamic-door POMDP

Liu et al. model a workspace released by an opened door that may close and use a POMDP belief tree for self-protective actions including escape.

**Boundary:** V4 must distinguish itself using its causal information state and explicit future safe-set connectivity objective, not merely "partially observable closing topology."

### 3.5 Endogenous uncertainty

Decision-dependent uncertainty has a mature optimization literature, including shortest-path examples where decisions affect uncertain arc quantities.

**Boundary:** the contribution cannot be the general observation that decisions alter future uncertainty.

## 4. Defensible intersection after chaining

The remaining research target is narrower:

> **A robot executes a known action that can stochastically arm a latent environmental state; that latent state is observed imperfectly; if armed, it changes the distribution of future topology; the planning quantity of interest is connectivity back to a designated safe set.**

Causal structure:

[
u_t
ightarrow
A_{t+1}
ightarrow
C_{mathrm{future}}
ightarrow
mathbf 1{xleadsto mathcal S_{mathrm{safe}}},
qquad
A_tightarrow o_t.
]

The proposed scientific question is not whether POMDPs can represent this process. They can.

The question is:

> **How much safe-return information and decision value is lost when this action-induced latent topology state is collapsed to geometric state, fixed marginals, or a point estimate, and when is retaining the posterior worth its cost?**

This phrasing survives removal of DynNav-specific terminology and is therefore a stronger novelty test.

## 5. Strongest threat to novelty

The strongest conceptual combination is not one single prior paper but the union of:

1. Kneebone & Dearden — noisy uncertain graph + POMDP;
2. Zhang/Guo — uncertainty + explicit safe return;
3. Liu et al. — POMDP + closing workspace + escape/self-protection;
4. Frenkel/Parker/Mansouri — robot actions create future obstacles;
5. Nohadani/Sharma — decisions alter uncertainty.

A reviewer can reasonably argue that V4 is a specialized instance of standard POMDP modeling unless the paper demonstrates a useful **representation effect, calibration effect, or risk/efficiency value-of-information result** that is specific to action-induced return connectivity.

Therefore the V4 experimental design must isolate information representation rather than advertise Bayesian filtering itself.

## 6. Claims authorized by the literature audit

Potentially defensible, conditional on V4 evidence:

- action-induced latent topology state can contain safe-return information omitted by position-only or fixed-marginal representations;
- noisy observations of that state create a measurable value-of-information problem for route selection;
- point-estimate collapse can produce overconfident return-connectivity estimates;
- posterior conditioning can improve calibration under a correctly specified model, with explicit misspecification boundaries;
- equal closure marginals need not determine return connectivity when the joint topology distribution differs.

Not authorized:

- first history-aware planner;
- first safe-return planner;
- first POMDP navigation method;
- first belief-space topology planner;
- first action-induced topology model;
- first decision-dependent uncertainty model;
- first robot planner for stochastic topology;
- universal safety superiority.

## 7. Key references for manuscript verification

1. T. M. Moldovan and P. Abbeel, "Safe Exploration in Markov Decision Processes," ICML, 2012. arXiv:1205.4810.
2. M. Kneebone and R. Dearden, "Navigation Planning in Probabilistic Roadmaps with Uncertainty," ICAPS, 2009. DOI: 10.1609/icaps.v19i1.13359.
3. B. Axelrod, L. P. Kaelbling, and T. Lozano-Pérez, "Provably safe robot navigation with obstacle uncertainty," IJRR, 2018. DOI: 10.1177/0278364918778338.
4. X. Xiao, J. Dufek, and R. R. Murphy, "Robot Risk-Awareness by Formal Risk Reasoning and Planning," IEEE RA-L, 2020. DOI: 10.1109/LRA.2020.2974434.
5. S. Kameyama, K. Okumura, Y. Tamura, and X. Défago, "Active Modular Environment for Robot Navigation," ICRA, 2021. DOI: 10.1109/ICRA48506.2021.9561111.
6. C. Liu, B. Gao, C. Yu, and A. Tapus, "Self-protective motion planning for mobile manipulators in a dynamic door-closing workspace," *Industrial Robot*, 2021. DOI: 10.1108/IR-02-2021-0025.
7. Y. Zhang and M. Guo, "Online Planning of Uncertain MDPs under Temporal Tasks and Safe-Return Constraints," CDC, 2022. DOI: 10.1109/CDC51059.2022.9993378.
8. S. Carmesin, D. Woller, D. Parker, M. Kulich, and M. Mansouri, "The Hamiltonian Cycle and Travelling Salesperson problems with traversal-dependent edge deletion," *Journal of Computational Science*, 2023, 74:102156. DOI: 10.1016/j.jocs.2023.102156.
9. M. Dvořák et al., "Pathfinding in Self-Deleting Graphs," ISAAC, 2025. DOI: 10.4230/LIPIcs.ISAAC.2025.28.
10. S. Frenkel, D. Parker, and M. Mansouri, "Coverage with Self-Induced Obstacles on Grids," IEEE RA-L, 2026, 11(3):3454–3461. DOI: 10.1109/LRA.2026.3656776.
11. O. Nohadani and K. Sharma, "Optimization under Decision-Dependent Uncertainty," SIAM Journal on Optimization. DOI: 10.1137/17M1110560.
12. H. Kurniawati, "Partially Observable Markov Decision Processes and Robotics," Annual Review of Control, Robotics, and Autonomous Systems, 2022. DOI: 10.1146/annurev-control-042920-092451.

## 8. Submission-time repeat

Immediately before submission:

- repeat searches for 2026/2027 publications;
- inspect papers citing the self-deleting graph and self-induced-obstacle line;
- inspect papers citing the uncertain-roadmap/POMDP line;
- inspect papers citing the 2022/2023 safe-return MDP work;
- search the target venue proceedings for action-induced/environment-changing navigation;
- update the matrix and manuscript wording if a closer formulation appears.
