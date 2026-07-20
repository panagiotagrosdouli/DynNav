# DynNav-R: Recoverability-Aware Risk-Sensitive Navigation with Runtime Safety Supervision

**Panagiota Grosdouli**

> Working manuscript. Numerical claims must be inserted only after running the integrated benchmark defined in `RESEARCH_PLAN.md`.

## Abstract

Autonomous navigation in partially observed and dynamically changing environments requires more than minimizing geometric path length. A route may be immediately collision-free yet lead the robot into a bottleneck, cul-de-sac, or fragile state from which recovery becomes difficult after new hazards appear. This paper introduces **DynNav-R**, a recoverability-aware navigation framework that combines risk-sensitive route planning, explicit estimation of future recovery freedom, and auditable runtime supervision. The planner augments geometric and risk costs with a route-level irreversibility term derived from return distance, escape options, bottleneck structure, and local obstacle density. A finite-state supervisor monitors route risk and recoverability to trigger conservative operation, replanning, recovery, or stopping actions. We evaluate the framework against shortest-path, risk-aware, and component-ablated baselines across controlled dynamic grid environments. The study measures mission success, irreversible-state entry, recovery success, tail-risk exposure, path efficiency, replanning frequency, and computation time. [Insert verified results.] The intended contribution is not a formal safety guarantee, but a reproducible framework for studying whether preserving future recovery options improves navigation robustness under route invalidation and uncertainty.

## 1. Introduction

Shortest-path planning is insufficient when the environment is uncertain or changes during execution. Two candidate paths may have similar length and immediate collision risk while differing substantially in their future recoverability. A route through a narrow corridor may remain feasible at planning time but become effectively irreversible if an obstacle later blocks the exit. Conventional risk-aware planning can reduce exposure to known hazardous regions, but it does not necessarily model whether the robot retains escape routes or a feasible return path.

This work studies the following question:

> Does explicit recoverability modelling reduce irreversible navigation failures and improve mission success compared with shortest-path and conventional risk-aware planning?

DynNav-R combines three mechanisms:

1. risk-sensitive path evaluation;
2. state- and route-level recoverability estimation;
3. hysteretic runtime supervision.

The contributions of this paper are:

- a recoverability-aware planning objective that separates geometric cost, route risk, and irreversibility;
- an auditable integration between route selection and runtime supervisory actions;
- a benchmark protocol for dynamic commitments, bottlenecks, and route invalidation;
- an ablation study isolating the effects of risk, recoverability, and supervision;
- a reproducible implementation with trial-level manifests and paired multi-seed evaluation.

## 2. Related Work

### 2.1 Classical and incremental path planning

Discuss Dijkstra, A*, D* Lite, Lifelong Planning A*, and dynamic replanning.

### 2.2 Risk-aware navigation

Discuss expected-risk objectives, worst-case risk, chance constraints, and CVaR-based planning.

### 2.3 Viability, reachability, and recoverability

Distinguish the proposed grid-based operational recoverability score from formal viability kernels, backward reachability, controllability, and kinodynamic safety analysis.

### 2.4 Runtime assurance and supervisory control

Discuss finite-state supervisors, Simplex-style runtime assurance, hysteresis, safety shields, and emergency-stop limitations.

## 3. Problem Formulation

Let the environment be a grid graph \(G=(V,E)\), with start state \(s\), goal state \(g\), trusted recovery region \(B\subseteq V\), obstacle map, and spatial risk field \(q:V\rightarrow[0,1]\).

For a path \(\pi=(x_0,\ldots,x_T)\), define geometric cost

\[
L(\pi)=\sum_{t=0}^{T-1} c(x_t,x_{t+1}).
\]

Let \(\rho(\pi)\) denote a selected route-risk functional, such as accumulated risk, maximum risk, or CVaR.

Let \(R_{\mathrm{rec}}(x)\in[0,1]\) denote state recoverability and

\[
I(x)=1-R_{\mathrm{rec}}(x)
\]

denote irreversibility.

The integrated objective is

\[
J(\pi)=L(\pi)+\lambda_r\rho(\pi)+\lambda_i I_{\pi},
\]

where

\[
I_{\pi}=\max_{x\in\pi}I(x).
\]

An optional temporal degradation penalty is

\[
D_{\pi}=\max_t [R_{\mathrm{rec}}(x_t)-R_{\mathrm{rec}}(x_{t+1})]_+.
\]

## 4. Method

### 4.1 Spatial risk representation

Document the exact risk-map construction and distinguish known risk, uncertainty-derived risk, and dynamic-obstacle occupancy risk.

### 4.2 Recoverability estimation

Define the normalized combination of:

- reachability of the trusted base;
- normalized return distance;
- local escape-option count;
- bottleneck score;
- obstacle density or clearance.

All coefficients and normalization ranges must be fixed from training/development scenarios or declared a priori before test evaluation.

### 4.3 Recoverability-aware search

Describe how edge or node costs incorporate route risk and irreversibility. State whether the heuristic remains admissible. When it is not admissible, describe the method as weighted or best-first search rather than claiming optimal A*.

### 4.4 Runtime supervisor

Document state transitions, thresholds, hysteresis, persistence, cooldown, replanning requests, and stop actions. Clearly separate a simulated software stop from certified emergency stopping.

### 4.5 Dynamic replanning

Describe route invalidation, obstacle updates, recomputation frequency, and recovery target selection.

## 5. Experimental Design

### 5.1 Scenario families

- open maps;
- bottlenecks;
- cul-de-sacs;
- dynamically blocked exits;
- uncertain risk corridors;
- return-to-base missions.

### 5.2 Baselines

- Dijkstra;
- A*;
- risk-aware A*;
- recoverability-only planner;
- DynNav-R without supervisor;
- full DynNav-R;
- optional D* Lite.

### 5.3 Metrics

Report mission success, irreversible-state entry, recovery success, return-to-base success, expected/maximum/CVaR risk, minimum recoverability, path length, travel time, replanning count, safe stops, expanded nodes, and planning runtime.

### 5.4 Statistical analysis

Use paired scenarios and seeds. Report 95% confidence intervals, effect sizes, paired significance tests, and failure counts. Correct for multiple comparisons where appropriate.

## 6. Results

### 6.1 Main comparison

Insert the final baseline table only from generated benchmark outputs.

### 6.2 Recoverability ablation

Quantify the effect of removing \(I_{\pi}\).

### 6.3 Supervisor ablation

Quantify the effect of removing hysteresis, persistence, or the complete supervisor.

### 6.4 Sensitivity analysis

Sweep \(\lambda_r\), \(\lambda_i\), recoverability thresholds, and risk thresholds.

### 6.5 Computational cost

Report runtime, expanded nodes, memory usage where measurable, and scaling with map size.

## 7. Discussion

Discuss when recoverability helps, when it produces excessive conservatism, failure cases, sensitivity to trusted-base selection, and the distinction between heuristic recoverability and formal viability.

## 8. Limitations

The current framework is grid-based, uses simplified dynamics, depends on hand-designed or calibrated risk signals, and does not establish formal or hardware safety. Recoverability is an operational heuristic rather than a complete kinodynamic reachability measure. Synthetic evaluation may not transfer directly to physical robots.

## 9. Conclusion

DynNav-R investigates whether autonomous navigation should preserve not only immediate feasibility but also future recovery freedom. The final conclusion will be written after the integrated experiments are complete and must match the measured evidence.

## Reproducibility checklist

- [ ] repository commit recorded;
- [ ] environment and dependency versions recorded;
- [ ] scenario seeds exported;
- [ ] all planner parameters exported;
- [ ] raw trial-level results included;
- [ ] aggregate tables generated from scripts;
- [ ] figure-generation commands documented;
- [ ] limitations and negative results retained.
