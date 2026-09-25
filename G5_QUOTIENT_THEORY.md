# G5 Theory — Exact Closure-Event Quotient Preserves the Planning Objective

**Status:** theorem/implementation note for the G5 research track.
**Scope:** DynNav's independent future-closure semantics.

## Raw augmented history

Let the raw planning state be s=(x,A), where x is robot position and A is the set of activated trigger identities.

Each trigger i maps to a future closure event e(i)=(c_i,p_i), consisting of a closure cell and closure probability.

Two trigger identities are equivalent when they have the same closure cell and the same closure probability. Let phi(A) be the set of activated equivalence classes. The quotient state is (x,phi(A)).

## Theorem G5-T1 — return-distribution preservation

Under the independent-closure model, for every raw activated set A, position x, and safe region S, the future topology distribution induced by A equals the distribution induced by phi(A). Therefore the exact safe-return probability is unchanged.

### Reason

The independent closure law depends only on the set of distinct active event pairs (cell, probability). Repeating the identity of a trigger that activates an already-active event neither introduces a new Bernoulli closure variable nor changes its parameter.

## Theorem G5-T2 — transition homomorphism

Let a raw transition execute edge x->x' and activate raw set A' = A union H(x,x'), where H(x,x') is the set of triggers attached to that directed edge.

The quotient transition activates E' = phi(A) union phi(H(x,x')). Because set image commutes with union, phi(A') = E'. Thus every raw executed transition maps to exactly the quotient transition used by the compressed planner.

## Theorem G5-T3 — pathwise objective preservation

DynNav's history-aware transition cost is step_cost + lambda*(1-return_probability). By G5-T1 and G5-T2, every concrete executed path has the same return-probability profile in raw and quotient representations. Hence every edge cost is identical and the cumulative path objective is identical.

This is checked mechanically by quotient_path_objective_witness.

## Corollary G5-C1 — optimal objective preservation

Because the quotient changes only the history representation and preserves the objective of every feasible path, the minimum attainable planning objective is unchanged.

If several paths tie at the optimum, implementation-specific tie breaking may return different geometric paths. The theorem concerns objective equivalence, not identical queue order or identical node-expansion counts.

## State-count consequence

With m trigger identities, raw subset history has at most 2^m activation subsets. If those triggers collapse to k <= m distinct closure-event classes, quotient history has at most 2^k event subsets. For d=m-k duplicate-trigger dimensions, the worst-case multiplicative subset-state reduction is 2^d.

Actual reachable-state reduction depends on map topology and trigger reachability.

## What the quotient must not merge

Exactness requires identical future event semantics. The implementation does not merge hazards merely because they have the same closure probability at different cells, happen to yield the same return probability in one state, have similar empirical outcomes, or are correlated but not identical events.

Likewise, two triggers that close the same cell with different probabilities remain distinct under the current representation.

## Claim boundary

This is an exact quotient for DynNav's independent closure-event model. It is not automatically exact for dependence models where trigger identity changes the joint closure law, time-dependent closure parameters, trigger-specific side effects beyond the represented closure event, or observation models in which trigger identity itself carries future information.

For G1-style dependence ambiguity, compression requires an equivalence relation that also preserves the relevant joint-distribution constraints.
