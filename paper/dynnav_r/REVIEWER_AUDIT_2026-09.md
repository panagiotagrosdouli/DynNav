# Adversarial Reviewer Audit — September 2026

## Executive assessment

DynNav now has a defensible narrow paper core: **executed robot transitions activate stochastic future topology hazards, and the activation history can carry safe-return-connectivity information that is lost by an endpoint-only marginal representation**.

The manuscript should be evaluated as a representation/mechanism paper, not as a universal safety-planning paper and not as a claim that history-dependent planning or action-induced topology is new.

## Strongest paper claim

For two executable histories ending at the same geometric state with true safe-return reliabilities (R_1) and (R_2), every deterministic endpoint-only scalar estimate (g(x)) must satisfy

[
max(|g(x)-R_1|,|g(x)-R_2|) ge |R_1-R_2|/2.
]

The action-triggered bridge construction realizes this gap with (R_1=1) and (R_2=1-p).

This is the cleanest theoretical statement in the paper. The experiments then answer whether the missing variable changes planning behavior under the declared model.

## Closest prior-art constraints

The manuscript must continue to acknowledge all of the following as prior art rather than novelty:

- safe exploration with returnability (Moldovan & Abbeel, ICML 2012);
- safe-return constrained uncertain-MDP planning (Zhang & Guo, CDC 2022; Guo et al., TAC 2023);
- probabilistic history-dependent robot risk (Xiao et al., RA-L 2020);
- deterministic traversal-dependent edge deletion / self-deleting graphs (Carmesin et al., JCSS 2023);
- shortest pathfinding on self-deleting graphs (Dvořák et al., ISAAC 2025);
- coverage with self-induced obstacles (Frenkel et al., RA-L 2026);
- contingency / backup-feasibility planning and reachability-based safe return;
- stochastic topology change in active environments;
- endogenous or decision-dependent uncertainty.

The surviving distinction is the **stochastic trigger–activation–realization model tied specifically to future safe-set connectivity**, together with the endpoint-aliasing analysis and controlled planning evaluation.

## Major reviewer concerns and current status

### 1. “This is just Markovization.”

**Status: addressed, but must remain explicit.**

The augmented state ((x,mathcal A)) is standard Markovization. The paper should never present state augmentation as the algorithmic novelty. The contribution is identifying and experimentally isolating the environmental variable that an endpoint-only marginal representation discards under the proposed trigger semantics.

### 2. “Self-deleting graphs already make topology path-dependent.”

**Status: addressed.**

Carmesin et al., Dvořák et al., and Frenkel et al. are now direct novelty constraints. The manuscript distinguishes deterministic residual-graph deletion from stochastic future closure activation and return-connectivity probability.

### 3. “The state-only baseline is artificially weak.”

**Status: strongly addressed.**

The publication-facing state-only exact control now uses the same exact connectivity oracle and the same additive fragility objective as the history-conditioned planner; only trigger-conditioned activation state is removed. In the retained reviewer-P0 artifact it reproduces shortest paths/outcomes in every controlled, heterogeneous, geometric, and generated unavoidable-hazard scenario. This is a clean representation ablation, while still not serving as a proxy for a general MDP/POMDP with a richer state.

### 4. “The proposed soft objective is cherry-picked.”

**Status: strongly addressed.**

The frozen soft-vs-hard sweep preserves the negative result that hard safe-return thresholds can match the zero-hazard route. This prevents an objective-superiority story and strengthens the representation claim.

### 5. “The effect sizes are unrealistically large / the planner only wins by avoiding all hazards.”

**Status: materially addressed, with synthetic-scope caveat.**

The original large effects arise in constructed worlds where a trigger-free route exists. A frozen reviewer-targeted suite now removes that regime: 96 generated scenarios contain one to four modules and every feasible route activates at least one hazard per module. Across 250 paired seeds per scenario (24,000 trials per planner), history exact is nonworse than state-only exact in 96/96 scenarios, improves 36/96, and reduces mean return-infeasibility from 0.7443 to 0.6660; the scenario-level mean difference is -0.0782 with 95% bootstrap CI [-0.1090,-0.0498]. The generator remains synthetic and structured, so this is not a deployment effect-size estimate.

### 6. “The exact method does not scale.”

**Status: openly acknowledged.**

Exact closure enumeration is a small-hazard reference oracle. The critical-cut approximation gives a useful scaling example but fails on a multi-cell cutset. Both the speed regime and failure boundary should remain publication-facing.

### 7. “There is no realistic execution evidence.”

**Status: integration evidence added; comparative efficacy still unsupported.**

A strict retained ROS 2/Nav2/Gazebo mechanism probe now has 24/24 valid trials and 8/8 outbound navigation successes for each of NavFn, DynNavShortest, and DynNavHistory. Paired latent closure draws are shared across planners and persistent history is reset explicitly between trials. In the frozen probe, DynNavShortest executes the configured trigger in 8/8 trials, DynNavHistory in 7/8, and NavFn in 0/8; realized closures are applied in 7/8, 6/8, and 0/8 trials respectively. Independent costmap recovery assessment is infeasible in 2/8 DynNavShortest trials, 1/8 DynNavHistory trial, and 0/8 NavFn trials. These differences are not sufficient for a comparative efficacy claim. The artifact closes the implementation/execution gap but not the broader simulation-performance gap.

## Submission-critical checks

Before submission:

1. Paper build and repository CI must be green on the exact release commit.
2. Every numeric claim in the manuscript must match paper/dynnav_r/evidence_manifest.json.
3. Every bibliography record must be verified against an authoritative venue/DOI source.
4. No sentence may imply that history-dependent planning, safe return, self-deleting topology, or Markov state augmentation is first-of-kind.
5. Tables must distinguish observed empirical zero failures from formal zero-risk guarantees.
6. Timing claims must remain environment-specific and descriptive.
7. Gazebo claims must remain limited to validated execution/integration; the retained 8-repetition mechanism probe does not support comparative efficacy.
8. Physical-robot safety or deployment claims remain out of scope.

## Optional high-value empirical upgrade

The highest-value additional Gazebo upgrade is a topology in which the same C++ DynNav search graph contains a verified trigger-taking route and a verified trigger-avoiding alternative. The current strict mechanism probe validates execution and measurement, but the history-aware condition changes exposure in only one of eight repetitions. Any stronger Gazebo claim requires a new predeclared topology-level test rather than post-hoc parameter tuning.

The broader automatically generated challenge family is now implemented and retained: 96 frozen scenarios vary module count, detour geometry, direction, and hazard probabilities while enforcing unavoidable stochastic commitments. Further random-map diversity remains useful but is no longer a prerequisite for the narrow representation claim. Repeated timing distributions are also retained (100 measured repetitions after 10 warm-ups), replacing the earlier single-shot latency evidence; these remain runner-specific descriptive measurements.

## Reviewer-facing one-sentence claim

> We isolate a representation failure that arises when executed robot actions activate stochastic future topology hazards: identical geometric states can have different safe-return reliability, and collapsing those histories to one endpoint-only estimate incurs unavoidable error.

## Claims to avoid

Do not write:

- “the first history-aware navigation planner”;
- “the first planner for changing topology”;
- “the first safe-return planner”;
- “DynNav is safer in general”;
- “DynNav guarantees safe return in real environments”;
- “the soft objective outperforms hard safe-return constraints”;
- “the critical-cut estimator is generally exact.”

## Current recommendation

**Strong candidate for a simulation-scoped planning/robotics submission after final exact-head CI/paper-build and release freeze.**

A valid Gazebo execution artifact would materially strengthen the submission, but physical-robot experiments are not required for the narrow mechanism claim if the paper stays explicit about its scope.
