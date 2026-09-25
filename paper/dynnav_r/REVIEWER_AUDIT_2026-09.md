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

**Status: partially addressed by framing.**

The baseline is deliberately restricted and should remain described as a representation ablation, not as a proxy for general MDP/POMDP planning. The endpoint-only lower bound is important because it applies to any deterministic scalar endpoint estimate under the same aliasing condition, not only the implemented marginal baseline.

### 4. “The proposed soft objective is cherry-picked.”

**Status: strongly addressed.**

The frozen soft-vs-hard sweep preserves the negative result that hard safe-return thresholds can match the zero-hazard route. This prevents an objective-superiority story and strengthens the representation claim.

### 5. “The effect sizes are unrealistically large.”

**Status: addressed in threats to validity.**

The large paired risk differences arise in constructed worlds designed to expose the mechanism. They are not estimates of deployment effect size. The manuscript now states this explicitly.

### 6. “The exact method does not scale.”

**Status: openly acknowledged.**

Exact closure enumeration is a small-hazard reference oracle. The critical-cut approximation gives a useful scaling example but fails on a multi-cell cutset. Both the speed regime and failure boundary should remain publication-facing.

### 7. “There is no realistic execution evidence.”

**Status: still the largest empirical limitation.**

The ROS 2/Nav2 implementation supports the semantics at software level, but the current manuscript must not claim Gazebo efficacy or hardware efficacy without a retained valid execution artifact. A simulation-scoped paper is still possible if this boundary remains explicit.

## Submission-critical checks

Before submission:

1. Paper build and repository CI must be green on the exact release commit.
2. Every numeric claim in the manuscript must match paper/dynnav_r/evidence_manifest.json.
3. Every bibliography record must be verified against an authoritative venue/DOI source.
4. No sentence may imply that history-dependent planning, safe return, self-deleting topology, or Markov state augmentation is first-of-kind.
5. Tables must distinguish observed empirical zero failures from formal zero-risk guarantees.
6. Timing claims must remain environment-specific and descriptive.
7. If no valid Gazebo comparison is retained, Gazebo must remain implementation/protocol evidence only.
8. Physical-robot safety or deployment claims remain out of scope.

## Optional high-value empirical upgrade

The highest-value additional experiment is a valid paired action-triggered ROS 2/Gazebo execution study using the already frozen protocol. It would not establish real-world safety, but it would close the largest gap between the graph-level mechanism and the integrated robotics stack.

A second valuable extension is a broader automatically generated topology family that is frozen before outcomes are inspected. This would improve geometric diversity without pretending to provide real-world generalization.

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

**Strong candidate for a simulation-scoped planning/robotics submission after final CI, bibliography, and claim-to-evidence audit.**

A valid Gazebo execution artifact would materially strengthen the submission, but physical-robot experiments are not required for the narrow mechanism claim if the paper stays explicit about its scope.
