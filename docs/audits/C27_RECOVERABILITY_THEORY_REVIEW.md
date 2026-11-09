# C27 Recoverability Theory Review

**Source:** `b626d6e9b5bf8b8cf1ec87906597d767224f5f37`. C27 has one conceptual `README.md`; it is outside the C01-C26 registry. Status: `CONCEPT_ONLY`.

## Definitions inspected

The proposal covers deterministic return feasibility, stochastic safe-return probability, redundancy-aware return routes, resource-aware recoverability, recoverability maps/gradients/horizons/budgets, and a proposed recoverability barrier. It correctly states that “barrier” alone is not a control barrier function and does not imply invariance.

## Candidate result with defensible assumptions

For a finite grid graph with safe set `S`, state `x`, and independent closure hazards `H` with probabilities `p_i`, exact safe-return reliability is the sum over all closure realizations of realization probability times the indicator that `x` remains connected to `S`. This is an identity under the enumerated independent Bernoulli model, not a novel theorem. It follows by partitioning the sample space into disjoint closure realizations. `dynnav/recoverability_belief.py` implements enumeration for small sets; no C27 proof artifact is present.

A candidate upper bound: if `K` is the set of hazard vertices whose individual removal disconnects `x` from every safe vertex, return requires every member of `K` to remain open. Under independent closures, reliability is at most `product_{v in K}(1-p_v)`. The bound may be loose because non-critical vertices can form joint cutsets. This is a proof sketch, not a formal repository theorem; it must explicitly handle current-cell conditioning and safe-set semantics.

## Counterexample and assumptions

Take two parallel corridors from `x` to `S`, each containing two cells with independent closure probability 0.5. No single cell is critical, so the single-vertex critical-cut estimate is 1. Exact reliability is `1 - (1 - 0.25)^2 = 0.4375` because each corridor fails if either cell closes. This demonstrates optimistic error from multi-cell cutsets.

Independence is critical: perfectly correlated hazards invalidate the product calculation. Resource-aware returnability requires resource state in the Markov state. History-conditioned hazards require active event history in the state, as C00 implements.

## Status

A standalone exhaustive finite counterexample runner now exists at `contributions/27_Recoverability_Theory/experiments/critical_cut_counterexample.py`; it is deliberately outside the C01-C26 registry. It independently enumerates 16 realizations and agrees with the exact oracle at 0.4375 return probability; the single-vertex cut proxy returns 1.0. This is one synthetic counterexample, not a general proof or a validated C27 contribution. C27 remains a theory proposal. Exact oracle and history-aware planners elsewhere in the repository support a narrower C00 research line, not every C27 concept.
