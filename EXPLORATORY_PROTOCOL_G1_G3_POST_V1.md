# Post-V1 Exploratory Protocol: G1 Topology Interaction and G3 Risk-Budget Learning

**Freeze date:** 2026-09-25  
**Status:** exploratory, designed after inspection of the frozen V1 full study and before inspection of the first retained risk-budget artifact.

This protocol does not replace `EXPERIMENT_PROTOCOL_G1_G5_V1.md`. V1 remains the confirmatory synthetic study. The purpose here is to prevent outcome-driven reinterpretation of the two post-V1 research directions.

## E1 — G1 two-hazard topology/dependence interaction

For fixed closure marginals `p1`, `p2`, write `q = P(C1 closes AND C2 closes)`.

Let `f_ab` be the deterministic safe-return connectivity indicator when hazard 1 has closure state `a` and hazard 2 has closure state `b`.

Expected return reliability is affine in `q`, with slope

`kappa = f00 - f10 - f01 + f11`.

### Frozen interpretation

- `kappa < 0`: increasing positive dependence lowers return reliability.
- `kappa = 0`: dependence is irrelevant at fixed marginals.
- `kappa > 0`: increasing positive dependence raises return reliability.

Parallel redundant return has `kappa = -1`; a two-cell serial cut has `kappa = +1`.

### Claim boundary

The intended contribution is not "correlation is harmful." The stronger and narrower statement is that dependence sensitivity is topology-dependent and, for two bounded hazards, is exactly characterized by the connectivity interaction coefficient.

### Validation

1. exact unit tests for parallel, serial and zero-interaction truth tables;
2. agreement between the analytic affine formula and scenario enumeration;
3. later held-out topology survey without changing the identity.

The mathematical identity is deterministic; significance testing is not appropriate.

---

## E2 — G3 finite exploration-risk budget

The strict one-sided credible-return gate can cold-start deadlock when:

1. trigger-conditioned outcomes are only observed after exposure;
2. the prior conservative return bound is below the required return threshold;
3. the policy prohibits every exposure while that bound remains below threshold.

The new exploratory method permits a finite number of otherwise rejected probes through an explicit cumulative exploration-risk budget. Each exploratory probe is charged by the one-sided posterior upper quantile of closure probability.

This is an accounting mechanism for studying the learning/risk frontier. It is **not** a deployment-safety guarantee.

### Frozen policies

- `credible_gate`: strict conservative gate, zero exploration budget;
- `posterior_mean_gate`: V1 heuristic;
- `risk_budget_5`;
- `risk_budget_20`;
- `risk_budget_50`;
- `oracle_gate`: true closure probability known, information upper reference.

### Frozen grid

- true closure probability: `{0.1, 0.3, 0.5, 0.7}`;
- minimum return threshold: `{0.5, 0.7, 0.9}`;
- confidence: `0.90`;
- opportunities per condition in the CI exploratory artifact: `1000`;
- prior: `Beta(1,3)`;
- matched latent closure sequence within each condition;
- master seed inherited from the post-V1 diagnostic runner: `20260925`.

### Primary outcomes

- number of trigger exposures;
- number of exploratory exposures;
- posterior absolute error;
- observed return failures in the simplified critical-trigger model;
- cumulative charged risk budget.

### Frozen hypotheses

- **E2-H1:** when the strict credible gate is locked at the prior, any positive risk budget that can pay the first risk charge obtains at least one trigger-conditioned observation.
- **E2-H2:** increasing the budget weakly increases the maximum possible exploratory exposure count; it is not required to improve every finite-sample posterior realization monotonically.
- **E2-H3:** additional exposure can reduce posterior error in learnable regimes but may increase realized failures; both effects must be reported.
- **E2-H4 negative boundary:** for genuinely high-risk hazards, a larger exploration budget can produce more failures. Such a regime is evidence about the trade-off, not an experiment to discard.
- **E2-H5:** a zero-budget policy does not solve the cold-start identification problem without passive or transferred information.

### Promotion gate

This mechanism is not promoted to a G3 paper method merely because it breaks lockout. Promotion requires:

1. a reproducible accuracy/risk frontier across the frozen grid;
2. explicit comparison with side-information or contextual-transfer alternatives;
3. theoretical accounting of what the budget controls and what it does not control;
4. literature review against safe active learning, constrained bandits and risk-budget exploration.

If those conditions are not met, the result remains an impossibility/trade-off study.
