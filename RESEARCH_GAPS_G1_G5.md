# DynNav G1-G5 Research Programme

**Branch:** `research/g1-g5-program`  
**Status:** implemented research foundations plus bounded mechanism experiments. These modules do not by themselves authorize novelty, deployment-safety, or real-world efficacy claims.

## Programme question

How much additional safe-return information and planning value can DynNav obtain when it relaxes the original assumptions of deterministic trigger history, known independent closure probabilities, and uncompressed trigger identity?

| Gap | Scientific question | Implemented foundation | Publication gate |
|---|---|---|---|
| G1 | What if action-triggered closures have uncertain joint dependence? | finite ambiguity sets, exact LP return bounds, robust Python/C++ history planners, finite-data ambiguity, V4 Gazebo execution | **main mechanism gate passed**; remaining gate is manuscript/literature/release freeze |
| G2 | What if trigger execution/activation is only noisily observed? | exact activation belief + threshold safety/coverage frontier | repeated-seed parameter sweep + explicit belief/POMDP baseline |
| G3 | What if trigger-to-closure probabilities must be learned while the policy controls exposure? | lockout theorem, risk-budget frontier, safe-sentinel transfer with misspecification controls | **identifiability boundary established**; new method would need justified information source/transfer assumptions |
| G4 | Which executed actions causally affect later closures? | logged-propensity IPW estimator, randomized graph recovery, sample/propensity/effect stress grid, confounding control | **validation primitive characterized**; not a generic causal-discovery contribution |
| G5 | How much activated-history state is redundant? | exact closure-event quotient, compressed A*, exhaustive reachable-state scaling to 8 modules | **exact representation gate passed**; use as computational companion, not universal online speedup |

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

### Publication status after V4

G1 now has retained held-out topology evidence, finite-data ambiguity results, repeated synthetic dependence-shift trials, and a localization-controlled Nav2/Gazebo confirmatory study.

In V4, all three dependence slices achieved 10/10 paired-valid History↔Robust repetitions and a stable frozen route audit. Robust planning eliminated both-trigger exposure (10/10 -> 0/10) in every slice. Under common-cause truth, realized return infeasibility fell from 7/10 for the independence-history planner to 0/10 for the robust planner; under anti-correlation both were 0/10, while Robust retained a large navigation-time penalty.

The remaining G1 work is not another hand-tuned benchmark. It is:
1. integrate theory, finite-data results and V4 execution into the manuscript;
2. finish venue-specific literature verification;
3. reconcile all publication numbers to retained manifests;
4. freeze a clean tagged release.

Further heterogeneous-marginal/high-dimensional-dependence studies are valuable generalization extensions, not prerequisites for the narrow current G1 claim.

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

### Status after risk-budget and side-information stress tests

The target-only credible gate has an absorbing cold-start lockout under the exposure-only update semantics. Two explicit deadlock breakers have now been evaluated:

1. **finite exploration-risk budget:** improves identification by buying target exposure, but failures increase with the admitted budget;
2. **safe sentinel side information:** can recover the target closure parameter without target-conditioned data under an exact shared-parameter assumption, but optimistic misspecification can create hundreds of false-safe target exposures while pessimistic misspecification recreates lockout.

This is sufficient to support the identifiability/assumption boundary. A future G3 method should not simply add another probe heuristic; it must specify where information comes from and prove or empirically stress the assumptions that transfer that information to the target hazard.

## G4 — interventional trigger-to-closure effects

G4 is intentionally narrower than generic causal discovery. Given randomized or otherwise ignorable trigger assignment with known logged propensity `e`, the implemented inverse-propensity estimator targets the average effect of executing a trigger on a later binary closure. It does not identify hidden-confounded effects from ordinary observational navigation logs.

### Frozen hypotheses

- **G4-H1:** randomized logged-propensity trials recover an injected trigger-to-closure effect.
- **G4-H2:** injected null trigger/closure pairs remain near zero.
- **G4-H3 negative control:** hidden confounding can create a spurious estimated effect when the assignment model is wrong.

### Implemented bounded evidence

The CI runner contains a randomized positive-effect condition, a randomized null condition, and an intentionally confounded observational condition with a misspecified propensity. The third condition is expected to fail and demonstrates the method boundary.

### Status after randomized stress grid

The multi-edge recovery benchmark has now been repeated over effect strength, treatment propensity and per-pair sample size. Weak 100-sample conditions can have mean recall as low as 0.10; by 1000 samples the frozen grid has minimum mean recall 0.933 and minimum mean precision 0.96. This quantifies the support requirement of the narrow randomized estimator.

The hidden-confounding failure remains a hard boundary. Do not make an arbitrary-SCM, passive-log, or hidden-confounder discovery claim without a substantially stronger method.

## G5 — exact activated-history compression

The raw augmented state tracks activated trigger identities. Under the current independent-closure semantics, two hazards are exactly equivalent when they activate the same future closure cell with the same probability. The quotient therefore tracks closure-event classes instead of trigger identities.

If `m` trigger identities collapse to `k` distinct closure events, the worst-case subset count falls from `2^m` to `2^k`, while the future closure distribution is unchanged. The implementation includes both the quotient map and a compressed A* whose search state is `(cell, activated closure-event IDs)`.

### Frozen hypotheses

- **G5-H1:** quotienting preserves every independent-model safe-return query, route and objective value exactly.
- **G5-H2:** repeated triggers mapped to shared closure events can reduce the augmented subset-state space exponentially in the duplicated-trigger dimension.
- **G5-H3 negative control:** distinct closure cells are never merged merely because they share a probability or happen to yield the same return value in one map.

### Implemented bounded evidence

Tests verify that distinct trigger histories mapping to the same closure event give the same return probability and that raw and compressed A* return the same path, objective value and return probability on a duplicate-trigger construction. The unified runner records theoretical subset-state counts for 2, 4, 8 and 12 trigger identities collapsed to two closure events, and a diamond-chain benchmark compares raw and quotient search nodes and planning latency as duplicate-trigger modules increase.

### Status after exhaustive reachable-state scaling

The exact quotient now has retained complete-state scaling through 8 duplicated-trigger modules. At 8 modules the raw augmented graph has 398,583 reachable states and the quotient has 207, a 1,925.5x ratio with 99.948% state reduction. Peak BFS frontier is 30,045 versus 14.

The frozen early-goal A* result remains deliberately alongside this strong full-state result: a planner that reaches its goal early may realize only modest node/time savings. G5 therefore supports an exact representation-compression claim and a potential computational benefit, not a universal online speedup guarantee.

## Reproducible bounded runner

Run:

```bash
PYTHONPATH=. python scripts/run_research_gap_program.py --trials 10000 --seed 20260925 --output results/research_gap_program/g1_g5_summary.json
```

The dedicated GitHub Actions workflow runs the focused G1–G5 tests, executes a smaller CI-sized stochastic run, and uploads the JSON evidence artifact. These artifacts are mechanism evidence, not ROS/Gazebo or physical-robot efficacy evidence.

## Publication strategy

Do not force all five gaps into one paper merely because they share code. The current deterministic DynNav manuscript should remain scoped to history-conditioned action-triggered topology. The strongest immediate extension is G1, with G5 as a natural computational companion if the scaling study is favorable. G2 and G3 form a coherent uncertainty/learning extension if their safety-availability results survive broad sweeps. G4 should remain a separate causal-identification direction unless interventional experiments establish a distinct contribution.
