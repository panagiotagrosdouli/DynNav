# G3 Theory — Exposure-Only Non-Identifiability and Safe-Learning Lockout

**Status:** theorem/assumption note for the G3 research track.
**Scope:** action-triggered closure probability learning when trigger-conditioned outcomes are observable only after exposure.

## Information model

Let the unknown closure probability be p = P(C=1 | T=1), where T=1 denotes executing the trigger and C=1 denotes the associated future closure.

Assume:

1. the learner receives a closure observation only after trigger exposure;
2. when T=0, no informative proxy or side-channel about C is observed;
3. the conditional parameter p is stationary over the considered learning horizon.

The third assumption is not needed for the one-step impossibility statement, but it is required to interpret repeated exposure as estimating one fixed parameter.

## Theorem G3-T1 — no-exposure observational equivalence

Consider any two values p1,p2 in [0,1]. Under a policy that never exposes the trigger, the complete observed data law is identical under p1 and p2.

Equivalently, the total-variation distance between the two no-exposure data laws is zero for every number of opportunities n.

### Proof

Under the stated information model, every non-exposed opportunity yields the same null observation. Therefore the length-n observed sequence is deterministic and has probability one for every p. The two probability laws are identical, so their total-variation distance is zero.

## Corollary G3-C1 — exact minimax estimation bound

Suppose only that p is in [pL,pU], with 0 <= pL <= pU <= 1.

Because every admissible p produces the same no-exposure data, every estimator based only on those data must output the same value a for all p. The minimizing constant is the midpoint (pL+pU)/2, with exact minimax absolute error (pU-pL)/2.

Thus waiting longer without exposure does not shrink uncertainty.

## Corollary G3-C2 — absorbing strict-safe lockout

Assume additionally that the learner state changes only after exposure and a deterministic safety gate rejects exposure at the initial learner state. Then the learner receives no informative data, its state remains unchanged, and the same gate rejects every future exposure. The rejection is absorbing.

This is the structural explanation for the cold-start lockout already exercised in safe_learning_lockout_theory.py.

## What can break the impossibility

The theorem is conditional on the information structure. Identification can become possible if at least one additional source of information is admitted, for example controlled trigger exposure, a known safe calibration action, informative passive observations, transfer across triggers under an explicit shared-parameter model, external sensing, or a sufficiently narrow structural prior.

Each option changes the assumptions and must report its own risk or transfer-bias cost.

## Consequence for G3 experiments

A method should not be described as safe online learning merely because it keeps avoiding an uncertain trigger. Under exposure-only feedback, complete avoidance is statistically equivalent to receiving no information.

The next G3 experiment should compare assumption classes, not only policies:

1. exposure-only strict gate;
2. finite admitted exploration-risk budget;
3. passive side-information channel;
4. parameter transfer from related triggers;
5. oracle-known probability.

Primary outcomes should include parameter error, information/exposure count, realized return failures, and explicit assumption violations.

## Claim boundary

This is an identifiability result for the declared observation model. It is not a general impossibility theorem for safe reinforcement learning, conservative bandits, active learning, or robotics systems with informative passive sensing.
