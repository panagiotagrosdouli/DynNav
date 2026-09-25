# DynNav G1-G5 Research Programme

**Branch:** `research/g1-g5-program`  
**Status:** implementation + bounded mechanism benchmarks. No new novelty or deployment claim is authorized by this document.

## Programme question

How much additional safe-return information and planning value can be obtained when DynNav moves beyond a deterministic activated-hazard set with independent known closure probabilities?

The programme separates five research gaps that must not be conflated:

| Gap | Question | New implementation | Claim gate |
|---|---|---|---|
| G1 | What if action-triggered closures have uncertain joint dependence? | finite distributional ambiguity set, LP return bounds, robust history-aware A* | held-out dependence-shift study + literature audit |
| G2 | What if trigger execution/activation is only noisily observed? | existing exact activation belief + noisy-observation benchmark | threshold frontier, repeated seeds, explicit POMDP comparison |
| G3 | What if trigger->closure probabilities must be learned online and policy controls exposure? | Beta calibration + safe information-probe acquisition rule | predeclared online-learning study with safety/coverage frontier |
| G4 | Which executed actions causally affect later closures? | logged-propensity IPW trigger-effect estimator | randomized/interventional benchmark; no hidden-confounding claim |
| G5 | How much activated-history state is redundant? | exact quotient by future closure-event semantics | scaling study + transition-consistency proof/tests |

## Common scientific rule

Every new claim needs all of:

1. a frozen hypothesis and protocol before the retained outcome;
2. a baseline that can falsify the preferred interpretation;
3. a negative/harm regime;
4. raw machine-readable artifacts with seed/configuration provenance;
5. a wording boundary saying what the result does not establish.

A failed or null experiment remains a retained result.

---

## G1 - Dependence-ambiguous topology hazards

### Question

DynNav currently uses independent Bernoulli future closures after hazards become active. Equal marginal closure probabilities do not identify safe-return reliability when closures can share a common cause.

For active closure cells (C_1,ldots,C_h), define a finite joint distribution (q_\omega) over closure realizations (\omega\subseteq\{1,\ldots,h\}). The ambiguity set constrains:

[
q_\omega\ge0,\qquad \sum_\omega q_\omega=1,
]

marginals

[
\underline p_i \le \sum_{\omega:i\in\omega}q_\omega \le \overline p_i,
]

and optional pairwise joints

[
\underline p_{ij}\le\sum_{\omega:i,j\in\omega}q_\omega\le\overline p_{ij}.
]

Worst-case return reliability is

[
\underline R(x,A)=
\min_{q\in\mathcal P(A)}
\sum_\omega q_\omega
\mathbf 1[x\leftrightarrow S_{safe}\text{ under }\omega].
]

The bounded reference implementation solves this linear program exactly with SciPy HiGHS.

### Frozen hypotheses

- **G1-H1:** fixed marginals can admit materially different return reliability under different dependence.
- **G1-H2:** an independence-assuming planner can be false-safe under positive common-cause dependence.
- **G1-H3:** robust history-aware planning reduces false-safe decisions under dependence shift at a measurable path/runtime cost.
- **G1-H4 negative control:** when independence is correct, robust planning can be unnecessarily conservative.

### Experiments

1. Parallel-return-corridor analytic construction.
2. Common-cause corridor family with increasing redundancy.
3. Route-switch phase boundary: independence accepts while robust return constraint rejects.
4. Ambiguity-information sweep: marginals only -> pairwise bounds -> identified joint.
5. Held-out topology and dependence shifts.
6. Runtime scaling in hazard count.

Primary metrics: false-safe rate, irreversible-failure rate, path length, worst-case return, oracle return under true joint distribution, LP/planning latency.

---

## G2 - Uncertain trigger activation

The repository already contains an exact categorical belief over activated hazard sets and a noisy crossing benchmark.

### Frozen hypotheses

- **G2-H1:** informative correctly specified observations improve probabilistic calibration over prior-only inference.
- **G2-H2:** treating a noisy detector report as ground truth increases false-safe decisions in an identifiable sensor-quality regime.
- **G2-H3:** sensor-model misspecification can make an exact Bayesian update unsafe in decision terms despite being mathematically correct under the assumed model.
- **G2-H4 negative control:** weak sensing can provide negligible decision value.

### Required next experiment

Predeclare a grid over execution probability, closure probability, sensitivity, specificity and decision threshold. Run repeated independent seeds and report calibration error/Brier score together with false-safe versus safe-decision coverage. Compare against a small explicit belief-state/POMDP reference before any novelty wording.

---

## G3 - Policy-dependent online calibration

Avoiding a trigger preserves safety but also prevents observing the trigger-conditioned closure process. Therefore data coverage is policy dependent.

The bounded implementation uses a Beta-Bernoulli posterior for (P(closure\mid trigger)). A non-exposed opportunity does **not** count as evidence of no closure.

The safe-probe acquisition rule only considers candidates satisfying a declared return-probability floor and ranks them by expected posterior-variance reduction per traversal cost.

### Frozen hypotheses

- **G3-H1:** conservative avoidance produces lower exposure coverage and slower probability learning.
- **G3-H2:** safe probing can reduce posterior uncertainty while respecting a frozen modeled return threshold.
- **G3-H3:** incorrect logging that treats unexposed opportunities as negative outcomes biases the learned closure probability downward.
- **G3-H4 negative control:** when all informative probes violate the return threshold, the learner must remain uncertain rather than fabricate evidence.

### Required experiment

Compare: always avoid, greedy information probe without return constraint, safe information probe, and oracle-known probability. Sweep true hazard probabilities and route costs. Report posterior calibration, interval coverage, exposure count, false-safe decisions, return failures, and mission cost.

---

## G4 - Interventional trigger-to-closure effects

This track asks a narrower question than general causal discovery: under randomized or otherwise ignorable trigger execution with known logged propensity, what is the interventional effect of executing trigger (T) on later closure (C)?

The initial estimator is inverse-propensity weighting:

[
\widehat{ATE}
=
\frac1n\sum_k
\left(
\frac{T_kY_k}{e_k}
-
\frac{(1-T_k)Y_k}{1-e_k}
\right).
]

### Frozen hypotheses

- **G4-H1:** randomized logged-propensity trials recover injected trigger->closure effects.
- **G4-H2:** null trigger/closure pairs remain near zero and act as negative controls.
- **G4-H3:** observational confounding can break the estimator; this must be demonstrated rather than hidden.

### Claim boundary

No claim of arbitrary SCM discovery, hidden-confounder identification, or causality from ordinary navigation logs is permitted from the current estimator.

### Required experiment

Inject a known trigger/closure causal graph. Randomize trigger opportunities with frozen propensities, include null edges and a deliberately confounded observational condition, and measure edge precision/recall plus effect estimation error.

---

## G5 - Exact activated-history compression

The current augmented state tracks activated hazard indices. If multiple triggers activate the same future closure cell with the same closure probability, their identities are redundant for the independent-closure return model.

Define event equivalence

[
h_i\sim h_j
\iff
(c_i,p_i)=(c_j,p_j).
]

The quotient state tracks activated equivalence classes rather than trigger identities. This preserves the future closure distribution exactly while reducing the worst-case subset count from (2^m) trigger subsets to (2^k) event subsets, where (k\le m).

### Frozen hypotheses

- **G5-H1:** event quotienting preserves every independent-model safe-return query exactly.
- **G5-H2:** maps with repeated triggers to shared closure events obtain exponential state-count reduction in the duplicated-trigger dimension.
- **G5-H3 negative control:** distinct closure cells are not merged merely because they have equal probability or happen to share one return value.

### Required experiment

Generate families with controlled trigger/event duplication. Compare raw versus quotient augmented search for exact path, cost, return probability, expanded states, memory and runtime. Add adversarial cases where unsafe over-compression would merge distinct events.

---

## CI-sized mechanism runner

Run:

```bash
PYTHONPATH=. python scripts/run_research_gap_program.py \
  --trials 10000 \
  --seed 20260925 \
  --output results/research_gap_program/g1_g5_summary.json
```

This runner produces bounded mechanism evidence for all five tracks:

- G1 marginal-only dependence bounds and pairwise identification;
- G2 noisy activation/miscalibration metrics;
- G3 exposure-aware online Beta calibration;
- G4 randomized trigger-effect recovery;
- G5 exact event-state count reduction.

It is intentionally not a substitute for the predeclared larger studies.

## Publication strategy

Do **not** force G1-G5 into one paper unless the evidence supports one coherent claim. The preferred sequence is:

- current DynNav paper: deterministic action-triggered history/state-aliasing result;
- strongest extension candidate: G1, optionally combined with G5 if compression is needed for computational feasibility;
- G2/G3: uncertainty and online-learning extension if the safety/availability frontier is robust;
- G4: separate causal-identification paper only if interventional experiments support a distinct scientific contribution.

All tracks remain falsifiable research branches until their own claim-evidence gates are satisfied.
