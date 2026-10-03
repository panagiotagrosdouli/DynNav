# V4 Development Findings

**Status:** development-only mechanism evidence. Not publication-facing. Not authorized for manuscript claims.

**Workflow run:** 37105534362  
**Head SHA:** e7f441aad9dc64b0422a318e8475a89eab6b5a0f  
**Artifact ID:** 11267827909  
**Artifact digest:** `sha256:fe83c37e4118fc7335f00c8e81b3d1770b1bc1a250ab9e5e1bbb1e5af0ed62dc`  
**Trials:** 5,000 paired seeds per regime; 40,000 raw rows across two regimes and four methods.

The artifact explicitly records `development_only_not_publication_evidence`.

---

## Purpose

This benchmark was run after the V4 research question and protocol were written, but before construction of the frozen 96-scenario held-out suite.

It answers one narrow question:

> Can the same geometric state select different outbound routes because of uncertainty about a previously armed return-corridor hazard?

The world has two redundant return corridors. A previous action may have armed a hazard affecting one corridor. A short final route arms a second hazard affecting the other corridor. A longer route avoids the second trigger.

Methods:

- activation oracle;
- exact Bayesian activation belief;
- prior-only activation belief;
- detector-as-truth point estimate.

The result is deliberately treated as a development/falsification check rather than evidence for the final paper.

---

## Retained results

### Medium correctly specified observation

True model:

- prior arming probability: 0.7;
- sensitivity: 0.85;
- specificity: 0.85;
- conditional closure probability: 0.8.

| Method | Mean path | Downstream trigger | Return-infeasible | Mean predicted return | Brier |
|---|---:|---:|---:|---:|---:|
| Activation oracle | 2.4016 | 0.2992 | 0.0000 | 1.0000 | 0.0000 |
| Belief | 2.2860 | 0.3570 | 0.0696 | 0.93336 | 0.05606 |
| Detector as truth | 2.2860 | 0.3570 | 0.0696 | 1.0000 | 0.06960 |
| Prior only | 3.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |

### Interpretation

This is an important **non-dominance result**.

The belief and detector-as-truth methods choose the same route in this simple medium-noise world, so belief conditioning does **not** improve the operational failure rate here.

It does improve probability quality:

[
mathrm{Brier}_{belief}=0.0561
<
mathrm{Brier}_{detector}=0.0696.
]

The prior-only method has zero observed return failures because it always takes the longer no-trigger route. Therefore the belief method's shorter path is purchased with additional residual return risk.

This is a safety/availability trade-off, not a universal improvement.

The activation oracle shows that perfect information could obtain both lower mean path length than prior-only and zero observed failure by taking the direct route only when the previous hazard is truly inactive.

This establishes a useful value-of-information ceiling.

---

## Miss-heavy correctly specified observation

True model:

- prior arming probability: 0.7;
- sensitivity: 0.70;
- specificity: 0.95;
- conditional closure probability: 0.8.

| Method | Mean path | Downstream trigger | Return-infeasible | Mean predicted return | Brier |
|---|---:|---:|---:|---:|---:|
| Activation oracle | 2.4000 | 0.3000 | 0.0000 | 1.0000 | 0.0000 |
| Belief | 3.0000 | 0.0000 | 0.0000 | 1.0000 | ~0 |
| Detector as truth | 2.0040 | 0.4980 | 0.1378 | 1.0000 | 0.1378 |
| Prior only | 3.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |

### Interpretation

Here the detector-as-truth baseline is overconfident after missed detections. It chooses the short route in about half the trials and produces a 0.1378 realized return-infeasible rate while predicting return probability 1.

The exact belief method retains enough posterior probability on the missed hazard to reject the second exposure and records no return-infeasible outcomes in this development run.

However, it is exactly as conservative as the prior-only method:

[
L_{belief}=L_{prior}=3.0.
]

Therefore this regime supports a narrower statement:

> retaining uncertainty prevents an overconfident point estimate from creating false-safe route choices.

It does **not** show that Bayesian belief dominates a conservative prior policy on mission efficiency.

---

## What this result changes

It does **not** change the frozen V4 held-out protocol.

Instead it sharpens what the held-out suite must discriminate.

A publishable result cannot merely show:

[
belief < detector_as_truth
]

on failure rate.

That comparison can be achieved by conservatism.

The stronger question is whether belief conditioning improves the **risk/path-cost frontier** relative to both:

- an overconfident point estimate; and
- a conservative prior/fixed-marginal representation.

The held-out suite therefore needs scenarios in which observations create useful conditional decisions rather than merely causing the belief planner to always choose the conservative route.

---

## Falsification implications

The development result already falsifies an overly broad hypothesis:

> “Belief-conditioned planning always improves operational safety and efficiency relative to simpler representations.”

That hypothesis is false in the development world.

A more defensible hypothesis remains:

> Correctly represented uncertainty can improve probabilistic calibration and can prevent false-safe decisions caused by point-estimate trigger observations; whether it improves the operational risk/cost frontier depends on topology, observation quality and the value of information.

The frozen held-out experiment must test this narrower statement.

---

## Artifact integrity

The downloaded artifact ZIP digest matches the GitHub Actions artifact digest:

`fe83c37e4118fc7335f00c8e81b3d1770b1bc1a250ab9e5e1bbb1e5af0ed62dc`.

The artifact contains:

- `trials.csv`: 40,000 raw trial rows;
- `summary.json`;
- `run_metadata.json`;
- `provenance.json`;
- `SHA256SUMS.txt`.

Retained inner-file hashes:

- `trials.csv`: `69742d77b4d16fa3b815a7d8661ad1aeec99387fa73a61f82afc86daa058ca63`;
- `summary.json`: `349fc72385a96425926cbb2b2cd882f06ca878e60769878c6f5825818a6ce6c8`;
- `run_metadata.json`: `ecd651a6309179d61bb35b705fc3e15ec7972d7ced6a0146421bcce5e5d64ef6`;
- `provenance.json`: `eec6970a82e2753b3e8010df73e1e7691572c3ddcb9e91478cf97e6f11782005`.

These values document the development run only. They must not be copied into the publication evidence manifest.


---

## Extended development audit: exact-policy and correlation boundaries

A later development-only workflow extended the same research track without promoting any result to publication evidence.

**Workflow run:** 37108332731  
**Head SHA:** f5be4a3127c04ce89081b19c16e96e198093c9e4  
**Artifact ID:** 11268129840  
**Artifact digest:** \`sha256:d4d6aca5635247d5577dbbbb6951967f9cabafab854a8a0543425c1a65af75ad\`

The artifact retains the original route-choice benchmark plus two additional falsification studies.

### Exact observation-contingent policy comparison

A random development search over 50 small candidate worlds found:

- 50/50 candidates comparable;
- 0 first-action disagreements between receding-horizon predictive-belief planning and the exact finite-horizon observation-contingent reference;
- maximum first-action regret 0 in that random candidate set;
- mean exact states evaluated: 169.28.

This is a useful null result, but it is not evidence that the receding-horizon approximation is exact.

A deliberately constructed future-information counterexample produced:

\[
a_{\mathrm{exact}} \neq a_{\mathrm{receding}},
\]

with:

- exact first action: \((0,2)\);
- receding-horizon first action: \((0,4)\);
- exact value: 10.8;
- exact value of the receding first action: 11.0;
- first-action regret: **0.2**;
- exact states evaluated: 233.

Therefore the main V4 planner has an explicit approximation boundary:

> Marginalizing observations that have not yet occurred can lose decision value when an action is valuable because of information that will become available before a later commitment.

The planner must continue to be described as a **receding-horizon predictive-belief method**, not an optimal belief-space/POMDP policy solver.

### Equal-marginal correlation boundary

The development correlation study evaluated 30 exact reliability cases across two topology classes.

For the parallel joint-cut topology, the maximum absolute error from replacing the true common-cause joint closure model with independent marginals was:

\[
\boxed{0.25}.
\]

For the serial-any-cut topology, the maximum absolute error was also:

\[
\boxed{0.25}.
\]

The sign depends on topology:

- parallel redundant returns can make independence **optimistic** about reliability;
- serial cut structures can make independence **pessimistic** relative to the tested positively correlated common-cause model.

This reinforces an important modeling result:

> equal per-hazard closure marginals do not determine safe-return connectivity.

Correlation remains a misspecification boundary rather than a second headline contribution unless the project develops a new joint-model planning method.

### Research consequence

These extended development results strengthen the paper only by narrowing it.

The V4 paper must explicitly distinguish three information/approximation losses:

1. collapsing latent action-induced state to geometric or fixed-marginal state;
2. collapsing posterior uncertainty to a point estimate;
3. planning with a predictive belief while ignoring the value of future observations inside the search tree.

The held-out experiment tests (1) and (2). The exact-policy counterexample documents the limitation in (3).


---

## Additional retained development evidence: exact-policy approximation boundary

A later retained V4 development artifact extends the original route-choice benchmark with two independent falsification studies.

**Workflow run:** 37108332731  
**Head SHA:** f5be4a3127c04ce89081b19c16e96e198093c9e4  
**Artifact ID:** 11268129840  
**Artifact digest:** `sha256:d4d6aca5635247d5577dbbbb6951967f9cabafab854a8a0543425c1a65af75ad`

The artifact remains explicitly marked `development_only_not_publication_evidence`.

### Random exact-policy search

The exact finite-horizon observation-contingent reference was compared with the receding-horizon predictive-belief planner on 50 deterministic, seeded tiny worlds.

Retained summary:

- candidates: 50;
- exact/receding comparable: 50;
- first-action disagreements: **0/50**;
- positive exact first-action regret: **0/50**;
- mean exact states evaluated: **169.28**.

This is useful negative evidence. It indicates that ordinary small random cases do not automatically expose the approximation made by receding-horizon planning.

It must not be interpreted as evidence of POMDP optimality.

### Constructed future-information counterexample

A separate hand-constructed counterexample deliberately creates value in a future observation-contingent decision.

Retained exact first-action values:

[
Q_{mathrm{exact}}((0,2))=10.8,
]

[
Q_{mathrm{exact}}((0,4))=11.0.
]

The exact finite-horizon policy selects first action ((0,2)), while the receding predictive-belief A* selects ((0,4)).

Therefore the receding planner has exact first-action regret

[
11.0-10.8=oxed{0.20}.
]

The exact solver evaluated 233 belief-policy states in this constructed case.

This is an explicit approximation boundary: the receding planner can fail to value future information because candidate-path search marginalizes future observations rather than branching on them.

The correct claim is therefore:

> The V4 planner is a receding-horizon belief-conditioned reference method whose decisions can differ from an exact observation-contingent policy when future information has action value.

It must never be described as a general optimal POMDP solver.

---

## Additional retained development evidence: correlation model misspecification

The same development artifact includes an equal-marginal common-cause study over:

[
pin{0.25,0.50,0.80},
qquad
hoin{0,0.25,0.50,0.75,1}.
]

Thirty topology/model combinations were evaluated.

Two deliberately opposite network structures were retained.

### Parallel joint cut

Two individually redundant return corridors form a joint cut.

The independent-marginal model is optimistic under positive common-cause dependence.

Maximum retained signed error:

[
hat R_{mathrm{independent}}-R_{mathrm{joint}}
=
oxed{+0.25}.
]

### Serial any-cut

Either one of two serial closures can destroy the only return path.

For the same equal-marginal positive-dependence family, the independent model can instead be pessimistic.

Minimum retained signed error:

[
hat R_{mathrm{independent}}-R_{mathrm{joint}}
=
oxed{-0.25}.
]

Thus correlation does not have one universal direction of error. The topology determines whether replacing the joint distribution with independent marginals is optimistic or pessimistic.

The publication-safe conclusion is:

> Equal per-hazard closure marginals do not determine safe-return connectivity; dependence structure and network topology jointly determine reliability error.

Correlation should remain a model-misspecification boundary rather than a second headline contribution unless it motivates a new inference/planning method.

---

## Additional negative result: hard constraint mission refusal

The V4 contract tests exposed a valid case where the hard belief-safe-return baseline with

[
R(x,b)ge 0.90
]

admits no outbound successor.

The planner therefore refuses the mission while remaining protocol-valid.

This behavior is now retained as a meaningful baseline outcome rather than treated as an implementation failure.

It reinforces the distinction between:

- preserving a representation of return uncertainty; and
- choosing a soft versus hard decision objective.

A hard safe-return constraint may preserve a threshold by making the mission infeasible.

---

## Model-misspecification infrastructure

The V4 executor now separates:

[
	ext{true generative model}

eq
	ext{planner-assumed model}.
]

Ground-truth arming and observations are generated from the true (q,s,c), while non-oracle belief updates and future predictive planning may use independently specified assumed parameters.

Property tests require that changing the assumed model does **not** change keyed latent truth:

- true armed set;
- detector observations;
- realized closures;
- realized return outcome.

The change may alter posterior probability, predicted return probability, and route choice.

This establishes the correct experimental substrate for the predeclared model-misspecification study. It is infrastructure/correctness evidence only; no held-out misspecification outcome has yet been inspected.

---

## Current development conclusion

The strongest V4 story after these falsification checks is not “Bayesian belief is always safer.”

Instead:

1. a posterior over action-induced latent topology state can prevent false certainty relative to a latched detector point estimate;
2. a conservative prior can still dominate on return risk by paying path cost;
3. the operational question is therefore a risk–efficiency/value-of-information question;
4. the receding planner is not generally observation-contingent optimal, and a retained counterexample quantifies that limitation;
5. closure correlation can make an independent topology model either optimistic or pessimistic.

The frozen held-out suite remains unopened.
