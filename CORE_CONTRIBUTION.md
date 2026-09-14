# Smallest Publishable Core

## One-sentence contribution

DynNav studies **history-conditioned safe-return planning under action-triggered topology hazards**: robot actions can activate future closure hazards, so two trajectories that end at the same geometric state can have different future return-connectivity.

## Publication-facing claim

The supported contribution is not generic recoverability or generic history-dependent planning. It is the narrower combination of:

1. action-triggered stochastic degradation of environmental return-connectivity;
2. a same-state/different-history information gap for state-only marginal models;
3. exact augmented-state planning over `(grid cell, activated hazard history)`;
4. a critical-cut approximation with both a scaling regime and an explicit joint-cut failure boundary;
5. retained paired evaluations across controlled, held-out probability/horizon and frozen geometric scenarios;
6. ROS 2 Jazzy / Nav2 integration with persistent history updated from executed transitions.

## Primary baselines

| Baseline | Scientific purpose |
|---|---|
| shortest / NavFn reference | geometric shortest-path control |
| state-only marginal return-risk planner | tests whether geometry plus marginal future risk is sufficient |
| hard safe-return threshold planner | strong feasibility-style safe-return baseline |
| exact history-aware planner | reference history-conditioned method |
| critical-cut history planner | scalable approximation with known limits |

The older J0–J3 risk/recoverability ablation remains useful historical and engineering context, but it is no longer the central publication claim.

## Operational quantities

- `mission_success`: goal reached under the frozen mission contract.
- `recovery_feasible`: safe region remains reachable under the experiment's recovery semantics.
- `irreversible_failure`: mission failure together with `recovery_feasible=false`; tables should prefer the precise wording **post-invalidation recovery-infeasible failure**.
- `activated_hazards`: closure hazards whose directed trigger transitions were actually executed.
- `exact_return_probability`: model-based safe-return probability under the declared closure model.
- `planning_latency`: full planner computation for the compared method, including recoverability/history work.
- `path_length`: geometric or executed path length as specified by the experiment protocol.

## Evidence boundary

Current retained evidence supports:

- the same-state/different-history representation mechanism;
- route-switch behavior in controlled constructions;
- paired stochastic execution effects in the repeated-module family;
- held-out probability/horizon replication;
- replication across three frozen hand-authored geometric topologies;
- exact-vs-cut scaling in a series-critical family;
- a joint-cut counterexample where the cut approximation is optimistic;
- C++ Nav2 integration of persistent history semantics.

Current evidence does **not** support:

- universal superiority of the soft history objective over hard safe-return constraints;
- universal exactness of the critical-cut approximation;
- calibrated real-world closure probabilities;
- completed history-conditioned Gazebo efficacy results;
- physical-robot efficacy or safety certification.

## Publication gate

The IEEE manuscript and retained synthetic/geometric evidence are already integrated. The next hardening gate is valid paired action-triggered Gazebo execution. New execution-level claims should enter the manuscript only after trigger observation, event realization/injection, costmap observation and recovery-label contracts all pass and the resulting artifact is retained with provenance.

See `paper/dynnav_r/evidence_manifest.json` and `CLAIM_EVIDENCE_MATRIX.md` for authoritative claim/evidence mapping.
