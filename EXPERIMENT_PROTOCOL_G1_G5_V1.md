# Experiment Protocol G1-G5 V1

**Freeze date:** 2026-09-25  
**Protocol status:** pilot-informed confirmatory synthetic study.

Pilot mechanism outputs were inspected before this protocol was frozen. Therefore this is not a claim of outcome-blind preregistration from project inception. The purpose of V1 is to prevent further tuning of the full-study grids, metrics and negative controls after the first full-study artifact is observed.

## Global rules

- Master seed: `20260925`.
- Default full-study repetitions: 5.
- Default stochastic trials per condition: 2000.
- Methods sharing a condition/repetition use matched latent random processes whenever the benchmark supports pairing.
- Failed or null hypotheses remain in the retained artifact.
- No outcome-based exclusion or parameter retuning is allowed without a protocol version change.
- Synthetic probabilities are model inputs, not calibrated real-world frequencies.
- Results do not imply physical-robot safety, certification or deployment efficacy.
- Full-study output is written to `results/research_gap_program/full_study.json`.

## G1 — dependence shift

### Frozen construction

The route-choice world has two alternative return corridors. The shortcut activates two closure hazards with marginal probability 0.5. The robust planner uses the marginal-only dependence ambiguity set. The independence planner uses the original independent-closure oracle.

True execution distributions:

1. `independent`: two independent Bernoulli(0.5) closures;
2. `common_cause`: both close together with probability 0.5;
3. `anti_correlated`: exactly one closes, each marginal remaining 0.5.

Planner recoverability weight is 12.0 in the frozen construction.

### Primary outcomes

- irreversible return failure rate;
- path length;
- activated hazard count.

### Primary interpretation

The key falsifiable condition is whether an independence-assuming decision can remain attractive under its model while becoming more failure-prone under common-cause dependence than under the independent data-generating process.

The robust planner is allowed to lose on path cost. That cost is part of the result.

### Analytic control

For `n` parallel corridors with equal closure marginal `p`, the Frechet-Hoeffding return bounds are:

- worst-case return: `1 - p`;
- best-case return: `1 - max(0, n*p - (n-1))`.

The LP oracle must match these bounds in the corresponding construction.

## G2 — uncertain activation observation

### Frozen grid

Activation probabilities:

`q in {0.2, 0.5, 0.8}`

Conditional closure probabilities:

`p in {0.2, 0.5, 0.8}`

Sensor/model profiles:

1. strong calibrated: true/assumed sensitivity 0.95, true/assumed specificity 0.95;
2. weak calibrated: true/assumed sensitivity 0.65, true/assumed specificity 0.65;
3. sensitivity miscalibrated: true sensitivity 0.60, assumed sensitivity 0.95, true/assumed specificity 0.90.

Decision thresholds:

`{0.05, 0.10, 0.20, 0.30, 0.40, 0.50}`

Methods:

- Bayesian activation posterior;
- prior-only activation estimate;
- detector-as-truth point estimate;
- activation oracle.

### Primary outcomes

- Brier score;
- false-safe rate among decisions called safe;
- safe-decision coverage.

### Interpretation rule

No single threshold is selected post hoc as "best." Results are reported as safety/availability frontiers. The activation oracle is an upper-information reference, not an implementable method.

## G3 — policy-dependent online calibration

### Frozen grid

True trigger-conditioned closure probabilities:

`{0.1, 0.3, 0.5, 0.7, 0.9}`

Minimum modeled return probabilities:

`{0.5, 0.7, 0.9}`

Policies:

- always avoid;
- always probe;
- safe information probe;
- oracle-known probability.

The prior for learned policies is Beta(1, 3).

### Primary outcomes

- exposure count;
- observed closures;
- posterior mean absolute error;
- return failures in the simplified single-critical-trigger model;
- cumulative exposure cost.

### Negative control

A separate mechanism benchmark intentionally logs unexposed opportunities as open outcomes. If exposure occurs with probability `r` and closure conditional on exposure has probability `p`, this naive estimator converges to `r*p`, not `p`.

## G4 — interventional trigger effects

### Frozen injected graph

Triggers: `t0, t1, t2`  
Closures: `c0, c1, c2`

Positive causal effects above a baseline closure probability of 0.10:

- `t0 -> c0`: +0.55;
- `t1 -> c2`: +0.35;
- `t2 -> c1`: +0.25.

All six other trigger/closure pairs have zero injected effect.

Randomized execution propensity is 0.5.

Sample sizes per trigger/closure pair:

`{250, 500, 1000, 2000}`

Edge screen:

- minimum estimated effect: 0.15;
- approximate 95% interval lower bound must be positive.

### Primary outcomes

- precision;
- recall;
- true positives;
- false positives;
- false negatives.

### Mandatory failure boundary

The retained hidden-confounding example has no causal treatment effect, but a common cause changes both execution probability and closure probability. With the frozen binary parameters, the expected observational treated-control difference is 0.42. The IPW estimator using an incorrect constant propensity is expected to be biased; this is a required negative result.

## G5 — exact event-state quotient

### Frozen scaling family

Diamond-chain module counts:

`{1, 2, 3, 4, 5, 6, 7, 8}`

Each module contains two distinct directed trigger identities that activate the same future closure event. The raw planner tracks trigger IDs; the quotient planner tracks the shared closure-event class.

### Exactness requirements

For every retained case:

- success/failure status must agree;
- geometric path length must agree under the matched objective;
- final safe-return probability must agree to numerical tolerance;
- any disagreement invalidates the compression claim.

### Scaling outcomes

- raw and quotient hazard/event counts;
- nodes expanded;
- planning latency;
- path length;
- final return probability.

Timing is descriptive and machine-dependent. The primary algorithmic evidence is exactness plus state/search reduction, not a hardware-independent speedup claim.

## Statistical reporting

The full study is intended to produce retained raw rows, not only aggregate point estimates.

For stochastic comparisons:

- preserve repetition/seed identity;
- report means and dispersion across repetitions;
- use paired differences when the same latent trials support pairing;
- report confidence intervals for primary rate differences where appropriate;
- do not treat threshold points or methods sharing the same trials as independent samples.

For deterministic exactness/theory checks, report exact agreement or counterexample rather than a significance test.

## Claim gate after the full study

A track advances toward a manuscript claim only if:

1. its primary hypothesis survives the frozen full-study grid;
2. the mandatory negative/harm regime is also reproduced;
3. results are traceable to a clean commit and retained artifact;
4. literature positioning remains defensible after a systematic review;
5. wording is narrower than the evaluated domain.

ROS/Gazebo and physical-robot claims require separate execution protocols and are not supplied by V1.
