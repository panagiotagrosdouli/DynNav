# Claim–Evidence Matrix

This matrix defines what the current repository may and may not claim. Publication-facing numerical values should be checked against `paper/dynnav_r/evidence_manifest.json` before reuse.

| Claim | Current evidence | Status | Boundary / next step |
|---|---|---|---|
| Action-triggered hazard history is implemented | `CommitmentHazardModel`, exact history-conditioned return probability, deterministic regressions | SUPPORTED | implementation claim only |
| Same geometric state can have different recoverability under different histories | frozen same-endpoint information-gap benchmark; separation equals trigger probability in the controlled construction | SUPPORTED | mechanism result, not universal frequency claim |
| Any deterministic endpoint-only scalar estimator has a worst-history error lower bound under an aliased endpoint | triangle-inequality proposition in `paper/dynnav_r/HISTORY_ALIASING_NOTE.md`; bridge construction gives lower bound `p/2` | SUPPORTED | representation statement only; does not apply once memory/latent state distinguishes histories |
| A state-only marginal model cannot represent both same-state histories exactly | counterfactual benchmark plus elementary minimax lower-bound argument | SUPPORTED | representation result under the stated construction |
| Exact augmented-state history planner is implemented | Python planner over `(cell, activated hazards)` with known-answer and online-history tests | SUPPORTED | computational scaling remains scenario-dependent |
| Critical-cut approximation is exact in the tested series-critical family | exact-vs-cut scaling benchmark | SUPPORTED | do not generalize exactness beyond that family |
| Critical-cut approximation can be optimistic | parallel joint-cut adversarial benchmark; disagreement in all 9 frozen settings | SUPPORTED | explicit failure boundary |
| Repeated timing distributions characterize retained-run computational cost | 100 measured repetitions after 10 warm-ups: 12-hazard exact oracle median 38.47 ms vs critical-cut 0.192 ms; six-module history-exact median 5.79 ms, history-cut 4.06 ms, shortest 0.114 ms | SUPPORTED | runner-specific descriptive timing only; no hardware-independent runtime guarantee |
| History-conditioned planning reduces irreversible failure in the controlled repeated-module execution family | paired CRN stochastic execution benchmark | SUPPORTED | mechanism family only |
| Result generalizes across held-out probability/horizon patterns in the frozen repeated-module family | 6/7/8-module held-out study, 500 paired seeds per scenario | SUPPORTED | not geometric-domain generalization |
| Result replicates across three frozen hand-authored geometric topologies | fork/L-room/chamber held-out study, 500 paired seeds | SUPPORTED | three synthetic geometries, not broad domain guarantee |
| State-only marginal baseline aliases shortest in the frozen history-trigger families | exact paired equality in retained controlled/held-out studies | SUPPORTED | specific baseline/model semantics |
| Exact state-only fixed-field baseline isolates representation from estimator choice | retained Reviewer P0 artifact; exact control uses the same connectivity oracle/objective and reproduces shortest paths/outcomes in all controlled, heterogeneous, geometric, and 24 generated challenge scenarios | SUPPORTED | specific fixed-field ablation; not a proxy for all MDP/POMDP methods |
| History-conditioned planning remains informative when every feasible route activates hazards | retained 96-scenario expansion, 250 paired seeds/scenario: mean return-infeasibility 0.7443 state-only exact vs 0.6660 history exact; scenario-level mean difference -0.0782, 95% bootstrap CI [-0.1090,-0.0498]; improved 36/96, nonworse 96/96 | SUPPORTED | structured synthetic generator; not arbitrary-map or deployment generalization |
| Soft history objective universally outperforms hard safe-return constraints | geometric Pareto sweep shows hard thresholds can match zero-hazard routes | UNSUPPORTED | objective choice depends on operating regime |
| Critical-cut planner universally matches exact history planner | joint-cut counterexample disproves this | UNSUPPORTED | approximation must report topology assumptions |
| History-conditioned C++ planner integrates with ROS 2 Jazzy/Nav2 | plugin build/discovery/tests plus persistent executed-history state | SUPPORTED | integration, not execution efficacy |
| Planned paths do not falsely activate persistent hazard history | planner wiring updates persistent state from executed-transition input only | SUPPORTED | execution source still requires valid observation semantics |
| Action-triggered Gazebo protocol is frozen before comparative outcomes | strict retained 8-repetition-per-planner mechanism probe; 24/24 trials valid with paired latent event draws and explicit per-trial history reset | SUPPORTED | controlled integration evidence, not a broad environment study |
| History-conditioned C++ planner executes successfully in the frozen Gazebo mechanism probe | 8/8 navigation successes and 8/8 valid trials for DynNavHistory; same for NavFn and DynNavShortest | SUPPORTED | execution/integration claim only |
| History-conditioned planner improves Gazebo execution outcomes | DynNavShortest triggers 8/8 and DynNavHistory 7/8; realized closure applied 7/8 vs 6/8; costmap recovery infeasible 2/8 vs 1/8 | UNSUPPORTED | one-trial differences are too small for a comparative efficacy claim; retain as diagnostic/integration evidence |
| Recoverability probabilities are calibrated to real-world recovery success | synthetic/model probabilities only | UNSUPPORTED | calibration/miscalibration study required |
| Robustness to partial observability or delayed hazard revelation | not yet evaluated in the publication-facing evidence stack | UNSUPPORTED | frozen stress-test protocol required |
| Safety is improved in deployment | no formal safety proof, powered hardware study, or certification evidence | UNSUPPORTED | explicit non-certification remains required |
| Physical-robot efficacy | no retained hardware execution study for the history-conditioned planner | UNSUPPORTED | staged named-hardware validation required |

## Interpretation rule

A `SUPPORTED` entry means the repository contains evidence for the **narrow wording shown in that row**. It does not imply safety, deployment readiness, broad generalization, or superiority outside the evaluated assumptions.

The state-only marginal planner is a deliberately restricted ablation that omits active-hazard history. Its null result does not establish superiority over a general MDP/POMDP whose state retains the active hazard process; `(position, active hazards)` is standard Markovization under the model assumptions.
