# DynNav research focus

DynNav studies **history-conditioned safe-return planning under action-triggered topology hazards**.

The central research question is whether executed action history carries recoverability-relevant information that an endpoint-only state representation discards when robot actions can activate future topology changes.

Under the current model, the sufficient planning state is the robot grid cell together with the set of activated hazards. The exact reference planner therefore searches over:

```text
(position, activated-hazard state)
```

rather than geometric position alone.

## Current comparison

The publication-facing evaluation uses:

- shortest / NavFn as the geometric reference;
- a state-only marginal return-risk baseline;
- the exact history-aware augmented-state planner;
- the critical-cut history approximation where scaling is studied;
- hard safe-return thresholds where objective-form sensitivity is studied.

The state-only baseline is intentionally restricted. The repository does not claim that state augmentation itself is novel or that the method dominates a general MDP/POMDP that retains the active hazard process.

## Primary outcomes

The current evidence stack reports exact/model safe-return probability, activated hazards, mission success, recovery feasibility, post-invalidation recovery-infeasible failure, path cost/length and planner latency under frozen experiment contracts.

Retained Gazebo runs establish ROS 2/Nav2 execution and measurement validity. They do not establish a stable comparative DynNavHistory-vs-DynNavShortest efficacy effect.

## Boundary

The earlier J0–J3 risk/recoverability-aware online-replanning program remains valuable historical and engineering context but is not the current paper claim. See `EXPERIMENT_PROTOCOL_V3.md`, `CLAIM_EVIDENCE_MATRIX.md`, `docs/REPOSITORY_GUIDE.md` and `paper/dynnav_r/evidence_manifest.json` for the authoritative current scope.
