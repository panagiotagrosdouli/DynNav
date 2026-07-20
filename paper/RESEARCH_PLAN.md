# DynNav Paper Research Plan

## Working title

**DynNav-R: Recoverability-Aware Risk-Sensitive Navigation with Runtime Safety Supervision**

## Scope

This paper isolates and integrates three DynNav components:

- C03: risk-aware path planning;
- C04: returnability, recoverability, and irreversibility estimation;
- C05: finite-state runtime supervision.

The paper will not claim novelty or validation for all DynNav modules. Its central contribution is a focused navigation framework that reasons about both immediate route risk and the robot's future ability to recover from a commitment.

## Research question

> Does explicitly modelling recoverability reduce irreversible navigation failures and improve mission success compared with shortest-path and conventional risk-aware planners, without unacceptable efficiency loss?

## Main hypothesis

A planner that combines route risk with a recoverability penalty, and is monitored by a hysteretic runtime supervisor, will:

1. enter fewer fragile or irreversible states;
2. recover more often after route invalidation;
3. reduce peak and tail risk exposure;
4. preserve a competitive mission-success rate;
5. incur a measurable but controllable path-length and runtime overhead.

## Proposed method

For path \(\pi=(x_0,\ldots,x_T)\), define

\[
J(\pi)=L(\pi)+\lambda_r R(\pi)+\lambda_i I(\pi),
\]

where:

- \(L(\pi)\) is geometric path cost;
- \(R(\pi)\) is expected, maximum, or CVaR route risk;
- \(I(\pi)\) is route-level irreversibility;
- \(\lambda_r\) controls risk aversion;
- \(\lambda_i\) controls recoverability preservation.

A first route-level irreversibility functional is

\[
I(\pi)=\max_{x\in\pi}\left(1-R_{\mathrm{rec}}(x)\right),
\]

with an additional optional degradation term

\[
D(\pi)=\max_t \left[R_{\mathrm{rec}}(x_t)-R_{\mathrm{rec}}(x_{t+1})\right]_+.
\]

The runtime supervisor consumes path risk, recoverability, and their temporal trends and selects one of:

```text
NORMAL -> CAUTION -> REPLAN -> RECOVER -> SAFE_STOP
```

The initial implementation may retain the current three-state controller while exposing the richer five-action interpretation in the paper as an extension to evaluate.

## Baselines

1. Dijkstra shortest path
2. A* shortest path
3. Risk-aware A* without recoverability
4. Recoverability-aware A* without risk
5. DynNav-R without runtime supervisor
6. Full DynNav-R

Optional stronger dynamic-planning baseline:

7. D* Lite or Lifelong Planning A*

## Ablations

- remove risk term;
- remove recoverability term;
- replace maximum irreversibility with mean irreversibility;
- remove temporal recoverability degradation;
- remove hysteresis;
- remove persistence and cooldown;
- fixed versus adaptive thresholds;
- expected risk versus maximum risk versus CVaR.

## Scenario families

The benchmark should contain procedurally generated and hand-designed maps covering:

- open environments;
- narrow passages;
- cul-de-sacs;
- one-way-like commitments;
- bottlenecks that become blocked;
- dynamic obstacle route invalidation;
- uncertain high-risk regions;
- limited-energy return-to-base missions;
- communication-degraded regions.

Each scenario family should be evaluated over multiple map sizes, obstacle densities, risk-map seeds, dynamic-event times, and start-goal pairs.

## Primary metrics

- mission success rate;
- collision or invalid-state rate;
- irreversible-state entry rate;
- return-to-base success rate;
- recovery success after route invalidation;
- minimum recoverability along path;
- maximum irreversibility;
- expected, maximum, and CVaR risk;
- path length;
- travel steps or time;
- replanning count;
- safe-mode activations;
- unnecessary safe stops;
- planning runtime and expanded nodes.

## Statistical protocol

- use at least 30 seeds per controlled scenario family for preliminary results;
- target hundreds or thousands of paired trials for the final benchmark;
- reuse identical scenarios across all planners;
- report mean, median, standard deviation, and 95% confidence intervals;
- use paired tests because planners are evaluated on the same scenarios;
- report effect sizes, not only p-values;
- predefine primary metrics before final runs.

## Evidence boundaries

The first paper version may support claims about controlled grid-based simulation only. It must not claim:

- certified safety;
- real-robot reliability;
- universal optimality;
- kinodynamic recoverability;
- collision avoidance guarantees;
- generalization beyond evaluated scenario distributions.

ROS 2/Nav2 and Gazebo validation should be presented as a later extension unless implemented and evaluated before submission.

## Minimum publishable experiment

A credible workshop or short-paper submission requires:

1. one integrated DynNav-R planner;
2. at least four baselines;
3. three or more scenario families;
4. repeated-seed paired evaluation;
5. ablations for recoverability and supervision;
6. confidence intervals and failure-case analysis;
7. reproducible CSV outputs and configuration manifests.

## Full-paper target

A stronger conference paper additionally requires:

- D* Lite or another competitive replanning baseline;
- richer dynamic environments;
- sensitivity analysis for \(\lambda_r\), \(\lambda_i\), and supervisor thresholds;
- qualitative route visualizations;
- computational-complexity discussion;
- Gazebo or comparable robotics-simulator validation.

## Immediate implementation milestones

- [ ] Define a canonical integrated scenario and configuration schema.
- [ ] Implement the recoverability-aware objective.
- [ ] Connect C03 route risk to C04 recoverability metrics.
- [ ] Connect the integrated planner to C05 supervision.
- [ ] Implement common baseline adapters.
- [ ] Build paired multi-seed benchmark runner.
- [ ] Add ablation configuration matrix.
- [ ] Export trial-level and aggregate CSV files.
- [ ] Generate publication figures and tables.
- [ ] Write the first complete manuscript draft.
