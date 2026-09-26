# Claim–Evidence Matrix

This matrix defines what the current repository may and may not claim. Publication-facing numerical values should be checked against `paper/dynnav_r/evidence_manifest.json` before reuse.

| Claim | Current evidence | Status | Boundary / next step |
|---|---|---|---|
| Action-triggered hazard history is implemented | `CommitmentHazardModel`, exact history-conditioned return probability, deterministic regressions | SUPPORTED | implementation claim only |
| Same geometric state can have different recoverability under different histories | frozen same-endpoint information-gap benchmark; separation equals trigger probability in the controlled construction | SUPPORTED | mechanism result, not universal frequency claim |
| A state-only marginal model cannot represent both same-state histories exactly | counterfactual benchmark plus elementary minimax lower-bound argument | SUPPORTED | representation result under the stated construction |
| Exact augmented-state history planner is implemented | Python planner over `(cell, activated hazards)` with known-answer and online-history tests | SUPPORTED | computational scaling remains scenario-dependent |
| Critical-cut approximation is exact in the tested series-critical family | exact-vs-cut scaling benchmark | SUPPORTED | do not generalize exactness beyond that family |
| Critical-cut approximation can be optimistic | parallel joint-cut adversarial benchmark; disagreement in all 9 frozen settings | SUPPORTED | explicit failure boundary |
| History-conditioned planning reduces irreversible failure in the controlled repeated-module execution family | paired CRN stochastic execution benchmark | SUPPORTED | mechanism family only |
| Result generalizes across held-out probability/horizon patterns in the frozen repeated-module family | 6/7/8-module held-out study, 500 paired seeds per scenario | SUPPORTED | not geometric-domain generalization |
| Result replicates across three frozen hand-authored geometric topologies | fork/L-room/chamber held-out study, 500 paired seeds | SUPPORTED | three synthetic geometries, not broad domain guarantee |
| State-only marginal baseline aliases shortest in the frozen history-trigger families | exact paired equality in retained controlled/held-out studies | SUPPORTED | specific baseline/model semantics |
| Soft history objective universally outperforms hard safe-return constraints | geometric Pareto sweep shows hard thresholds can match zero-hazard routes | UNSUPPORTED | objective choice depends on operating regime |
| Critical-cut planner universally matches exact history planner | joint-cut counterexample disproves this | UNSUPPORTED | approximation must report topology assumptions |
| History-conditioned C++ planner integrates with ROS 2 Jazzy/Nav2 | plugin build/discovery/tests plus persistent executed-history state | SUPPORTED | integration, not execution efficacy |
| Planned paths do not falsely activate persistent hazard history | planner wiring updates persistent state from executed-transition input only | SUPPORTED | execution source still requires valid observation semantics |
| Action-triggered Gazebo protocols are frozen before comparative outcomes | frozen legacy protocol plus versioned G1 V2/V3/V4 correlated-hazard protocols and retained failed predecessors | SUPPORTED | protocol changes after invalid integration runs are versioned and preserved |
| Dependence-robust history planning changes route/exposure in controlled Nav2/Gazebo execution | V4: 10/10 paired-valid repetitions per dependence slice; Shortest/History cross both trigger gates in every trial while Robust takes the trigger-free detour in every trial | SUPPORTED | canonical two-hazard mechanism under controlled simulator-odometry localization |
| Dependence-robust history planning reduces realized safe-return infeasibility under common-cause closures | V4 common-cause: History return-infeasible 7/10, Robust 0/10; paired risk difference -0.7, bootstrap 95% interval [-1.0,-0.4], exact McNemar p=0.015625 | SUPPORTED | controlled topology/dependence condition; recovery feasibility, not universal mission-success superiority |
| Dependence-robust history planning universally improves Gazebo outcomes | V4 robust route is much slower and common-cause navigation success is 0.7 versus 1.0 for History; anti-correlated condition has no safe-return benefit | UNSUPPORTED | retain safety-efficiency and mission-completion trade-off |
| G1 correlated-hazard execution is robust to AMCL/localization uncertainty | V3.1 failed preregistered paired-valid gates because of multi-metre AMCL jumps; V4 deliberately removes AMCL from the causal path | UNSUPPORTED | separate localization-robustness protocol required |
| Recoverability probabilities are calibrated to real-world recovery success | synthetic/model probabilities only | UNSUPPORTED | calibration/miscalibration study required |
| Robustness to partial observability or delayed hazard revelation | noisy-activation belief and calibration/misspecification studies exist, but no publication-facing execution study with delayed revelation | UNSUPPORTED | keep as G2 robustness/follow-up rather than fold into G1 execution claim |
| Safety is improved in deployment | no formal safety proof, powered hardware study, or certification evidence | UNSUPPORTED | explicit non-certification remains required |
| Physical-robot efficacy | no retained hardware execution study for the history-conditioned planner | UNSUPPORTED | staged named-hardware validation required |

## Interpretation rule

A `SUPPORTED` entry means the repository contains evidence for the **narrow wording shown in that row**. It does not imply safety, deployment readiness, broad generalization, or superiority outside the evaluated assumptions.

The state-only marginal planner is a deliberately restricted ablation that omits active-hazard history. Its null result does not establish superiority over a general MDP/POMDP whose state retains the active hazard process; `(position, active hazards)` is standard Markovization under the model assumptions.
