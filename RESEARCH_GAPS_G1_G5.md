# DynNav G1-G5 Research Programme

**Branch:** `research/g1-g5-program`  
**Status:** implemented research foundations plus bounded mechanism experiments. These modules do not by themselves authorize novelty, deployment-safety, or real-world efficacy claims.

## Programme question

How much additional safe-return information and planning value can DynNav obtain when it relaxes the original assumptions of deterministic trigger history, known independent closure probabilities, and uncompressed trigger identity?

| Gap | Scientific question | Implemented foundation | Publication gate |
|---|---|---|---|
| G1 | What if action-triggered closures have uncertain joint dependence? | finite ambiguity sets, exact LP return bounds, robust history-aware A* | retained dependence-shift planning study + literature audit |
| G2 | What if trigger execution/activation is only noisily observed? | exact activation belief + threshold safety/coverage frontier | repeated-seed parameter sweep + explicit belief/POMDP baseline |
| G3 | What if trigger-to-closure probabilities must be learned while the policy controls exposure? | exposure-aware Beta calibration + safe information probe rule | online safety/learning frontier with policy baselines |
| G4 | Which executed actions causally affect later closures? | logged-propensity IPW effect estimator + null/confounding controls | randomized/interventional graph-recovery study |
| G5 | How much activated-history state is redundant? | exact closure-event quotient + compressed augmented-state A* | scaling study showing equivalence and computational benefit |

## Evidence rule

A new publication-facing claim requires a frozen protocol before retained outcomes, a baseline capable of falsifying the preferred interpretation, a negative/harm regime, raw machine-readable artifacts with seed/configuration provenance, and an explicit scope limitation. Failed and null experiments remain evidence.

## G1 — dependence-ambiguous topology hazards

The original DynNav oracle assumes independent Bernoulli future closures. G1 instead places a joint probability mass `q[w]` over every closure realization `w`. The ambiguity set requires nonnegative masses summing to one, constrains each marginal closure probability to an interval, and may additionally constrain pairwise joint-closure probabilities.

For a fixed state and activated-hazard history, the robust return value is the minimum expected connectivity indicator over every joint distribution satisfying those constraints. Because both the objective and constraints are linear in `q`, the bounded reference problem is a finite linear program solved with SciPy HiGHS.

### Frozen hypotheses

- **G1-H1:** fixed marginals can permit materially different safe-return reliability under different dependence structures.
- **G1-H2:** an independence-assuming planner can be false-safe under positively dependent common-cause closures.
- **G1-H3:** robust history-aware planning can reduce false-safe decisions under dependence shift, with measurable path/runtime cost.
- **G1-H4 negative control:** when independence is correct, robust planning can be unnecessarily conservative.

### Implemented bounded evidence

The CI runner sweeps 2–5 parallel return corridors and marginal closure probabilities 0.2, 0.5, and 0.8. It reports independent-model return probability, worst/best return over the marginal ambiguity set, and a common-cause reference. A pairwise-identified two-corridor case checks that adding the joint probability can collapse the ambiguity interval. A separate planner test freezes a route-choice case in which the independence planner accepts a two-hazard shortcut while the robust planner chooses a trigger-free detour. A paired execution benchmark now evaluates that same decision under independent, common-cause and anti-correlated latent closures.

### Remaining publication experiment

Extend the implemented paired execution study to held-out geometries, heterogeneous marginals, partial pairwise information and repeated independent seeds. Report false-safe rate, irreversible-failure rate, path length, true-joint oracle return, robust lower return, LP/planning latency, and the conservative-cost regime.

## G2 — uncertain trigger activation

G2 separates physical trigger execution from its noisy observation. The repository already contains an exact categorical belief over activated hazard sets. The new frontier benchmark evaluates Bayesian posterior, prior-only, detector-as-truth, and activation-oracle estimates on the same latent trials over a frozen threshold grid.

### Frozen hypotheses

- **G2-H1:** informative correctly specified sensing improves probabilistic calibration over prior-only inference.
- **G2-H2:** treating a noisy detector output as physical truth produces false-safe decisions in an imperfect-sensor regime.
- **G2-H3:** sensor-model misspecification can degrade safety decisions even when the Bayesian update is exact under the assumed model.
- **G2-H4 negative control:** weak sensing can provide negligible operational value.

### Remaining publication experiment

Sweep execution probability, closure probability, sensitivity, specificity, model misspecification, and decision threshold over repeated independent seeds. Report Brier/calibration metrics together with false-safe versus safe-decision coverage, and compare against a small explicit belief-state/POMDP reference before any novelty wording.

## G3 — policy-dependent online calibration

G3 makes the sampling mechanism explicit: avoiding a trigger prevents both hazard exposure and information about `P(closure | trigger)`. A non-exposed opportunity therefore cannot be logged as a negative closure observation.

The implementation uses a Beta-Bernoulli posterior and a transparent safe-probe rule. Candidate probes must satisfy a modeled minimum return probability, after which they are ranked by expected posterior-variance reduction per traversal cost.

### Frozen hypotheses

- **G3-H1:** conservative avoidance reduces exposure coverage and slows learning.
- **G3-H2:** safe probing can reduce posterior uncertainty while satisfying a frozen modeled return threshold.
- **G3-H3:** logging unexposed opportunities as non-closures biases the learned closure probability downward.
- **G3-H4 negative control:** if every informative probe violates the return threshold, the learner must remain uncertain rather than fabricate evidence.

### Implemented bounded evidence

The unified runner compares always-avoid, always-probe, correctly logged half-exposure, and a deliberately incorrect half-exposure logger that records unexposed opportunities as open outcomes. A second online-policy benchmark compares always-avoid, unconstrained probing, the safe-probe rule, and an oracle-known-probability policy on matched latent closure opportunities.

### Remaining publication experiment

Compare always-avoid, unconstrained information probing, safe information probing, and an oracle-known-probability policy across hazard probabilities and route costs. Report calibration, credible-interval coverage, exposures, false-safe decisions, irreversible failures, mission cost, and learning speed.

## G4 — interventional trigger-to-closure effects

G4 is intentionally narrower than generic causal discovery. Given randomized or otherwise ignorable trigger assignment with known logged propensity `e`, the implemented inverse-propensity estimator targets the average effect of executing a trigger on a later binary closure. It does not identify hidden-confounded effects from ordinary observational navigation logs.

### Frozen hypotheses

- **G4-H1:** randomized logged-propensity trials recover an injected trigger-to-closure effect.
- **G4-H2:** injected null trigger/closure pairs remain near zero.
- **G4-H3 negative control:** hidden confounding can create a spurious estimated effect when the assignment model is wrong.

### Implemented bounded evidence

The CI runner contains a randomized positive-effect condition, a randomized null condition, and an intentionally confounded observational condition with a misspecified propensity. The third condition is expected to fail and demonstrates the method boundary.

### Remaining publication experiment

A bounded multi-edge randomized graph-recovery benchmark is implemented and reports precision/recall against three injected positive edges and six null edges. The publication gate is to repeat this over effect sizes, propensities, sample sizes, graph sparsities and explicit confounding regimes. Do not make an arbitrary-SCM or hidden-confounder discovery claim without a substantially stronger method.

## G5 — exact activated-history compression

The raw augmented state tracks activated trigger identities. Under the current independent-closure semantics, two hazards are exactly equivalent when they activate the same future closure cell with the same probability. The quotient therefore tracks closure-event classes instead of trigger identities.

If `m` trigger identities collapse to `k` distinct closure events, the worst-case subset count falls from `2^m` to `2^k`, while the future closure distribution is unchanged. The implementation includes both the quotient map and a compressed A* whose search state is `(cell, activated closure-event IDs)`.

### Frozen hypotheses

- **G5-H1:** quotienting preserves every independent-model safe-return query, route and objective value exactly.
- **G5-H2:** repeated triggers mapped to shared closure events can reduce the augmented subset-state space exponentially in the duplicated-trigger dimension.
- **G5-H3 negative control:** distinct closure cells are never merged merely because they share a probability or happen to yield the same return value in one map.

### Implemented bounded evidence

Tests verify that distinct trigger histories mapping to the same closure event give the same return probability and that raw and compressed A* return the same path, objective value and return probability on a duplicate-trigger construction. The unified runner records theoretical subset-state counts for 2, 4, 8 and 12 trigger identities collapsed to two closure events, and a diamond-chain benchmark compares raw and quotient search nodes and planning latency as duplicate-trigger modules increase.

### Remaining publication experiment

Generate branching map families with controlled trigger/event duplication and compare raw versus quotient search for path, objective value, return probability, expanded states, peak memory and runtime. Include adversarial cases where unsafe over-compression would merge distinct events.

## Reproducible bounded runner

Run:

```bash
PYTHONPATH=. python scripts/run_research_gap_program.py --trials 10000 --seed 20260925 --output results/research_gap_program/g1_g5_summary.json
```

The dedicated GitHub Actions workflow runs the focused G1–G5 tests, executes a smaller CI-sized stochastic run, and uploads the JSON evidence artifact. These artifacts are mechanism evidence, not ROS/Gazebo or physical-robot efficacy evidence.

## Publication strategy

Do not force all five gaps into one paper merely because they share code. The current deterministic DynNav manuscript should remain scoped to history-conditioned action-triggered topology. The strongest immediate extension is G1, with G5 as a natural computational companion if the scaling study is favorable. G2 and G3 form a coherent uncertainty/learning extension if their safety-availability results survive broad sweeps. G4 should remain a separate causal-identification direction unless interventional experiments establish a distinct contribution.
