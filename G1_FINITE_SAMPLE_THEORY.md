# G1 Finite-Sample Returnability Certificate

**Status:** post-V1 theory companion to the exploratory finite-data ambiguity experiment.

## Setting

Let `h` future closure hazards be observed jointly in `N` i.i.d. calibration trials from a stationary conditional closure law `P*` for the same activated-hazard semantics used at planning time.

For each hazard `i`, retain the Bernoulli marginal moment `E[C_i]`. Optionally, for each pair `i<j`, retain the joint moment `E[C_i C_j]`.

Let `M` be the number of retained moment constraints. The implementation constructs a two-sided Clopper-Pearson interval for each Bernoulli moment at per-constraint error level `alpha/M`, where `alpha = 1 - family_confidence`.

## Proposition 1 — simultaneous moment coverage

Each Clopper-Pearson interval has coverage at least `1 - alpha/M`. By the union bound, with probability at least `1 - alpha` over the calibration sample, **all** retained true marginal and pairwise probabilities lie in their intervals simultaneously.

No independence assumption between the estimated moments is required for the Bonferroni step.

## Proposition 2 — returnability envelope

Define the empirical ambiguity set `P_N` as all joint closure distributions over the finite `2^h` scenario space whose retained moments lie inside the simultaneous intervals.

On the simultaneous-coverage event, the true joint law `P*` belongs to `P_N`.

For any fixed robot state/history and deterministic return-connectivity indicator `r(omega)`, define

`R_lower = min_{Q in P_N} E_Q[r]`

and

`R_upper = max_{Q in P_N} E_Q[r]`.

Because `P*` is feasible whenever the moment intervals cover,

`R_lower <= E_{P*}[r] <= R_upper`.

Therefore the LP bounds form a finite-sample confidence envelope for model-implied safe-return probability with family confidence at least `1-alpha`.

## Corollary — data-dependent route choice

The inclusion event `P* in P_N` is independent of which candidate route is ultimately selected from the same fitted ambiguity set. Consequently, conditional on the ambiguity set containing `P*`, the lower return bound remains conservative for any route whose future closure semantics are represented by the same scenario law.

This does **not** imply a physical-robot safety guarantee. It is a statistical certificate inside the declared closure model.

## Assumptions and failure boundaries

The guarantee requires:

1. matched observations of the retained hazard variables;
2. i.i.d. or otherwise valid binomial sampling for each retained event indicator;
3. stationarity between calibration and the planning-time conditional closure law;
4. correct mapping from closure scenarios to graph connectivity;
5. no unmodeled hazards outside the declared scenario support.

Policy-dependent sampling, distribution shift, noisy closure labels, hidden changes in activation semantics, or using data collected under a different conditional hazard regime can invalidate the certificate.

## Relation to prior art

Finite-sample ambiguity-set guarantees are established ideas in data-driven distributionally robust optimization and distributionally robust motion planning. The DynNav-specific contribution is not the generic confidence-set construction. The research question is its composition with executed-history hazard activation, return-connectivity, and dependence-sensitive route choice.
