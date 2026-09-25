# G2/G4 Control Protocol — Belief Reference and Interventional Identifiability

**Freeze date:** 2026-09-25
**Status:** bounded control protocol for the G2 and G4 support tracks.

## G2 — explicit belief/POMDP reference

### Question

Does DynNav's exact activation-belief update agree with an explicit belief-state decision reference, rather than only producing favorable calibration metrics?

### Frozen one-step decision model

Hidden activation state A is binary. A noisy crossing detector emits a binary observation. After observing it, the decision maker chooses either `continue` or deterministic `detour`.

Continuing has posterior expected loss:

`continue_cost + P(A=1 | O) * closure_probability * failure_cost`.

Detouring has fixed `detour_cost`.

The exact one-step belief/POMDP action minimizes these posterior expected losses.

### G2 hypotheses

- **G2-C1:** DynNav `ActivationBelief` posterior equals the direct closed-form Bayes posterior for both detector outcomes.
- **G2-C2:** using that posterior in the frozen decision loss gives exactly the same action and value as the explicit one-step belief/POMDP reference.
- **G2-C3:** an informative detector can change the optimal action after a positive versus negative report.
- **G2-C4 negative control:** a detector with sensitivity=specificity=0.5 provides no information, so the posterior and action remain equal to the prior-based decision.

### Claim boundary

This closes the explicit belief-state reference requested by the research programme. It is not a general POMDP planning algorithm or POMDP novelty claim.

---

## G4 — repeated interventional effect and propensity controls

### Randomized recovery sweep

The randomized benchmark varies:

- sample size: `{200, 1000, 5000}`;
- treatment propensity: `{0.2, 0.5, 0.8}`;
- injected ATE: `{0.0, 0.1, 0.3, 0.5}`;
- repeated independent seeds;
- baseline closure probability: `0.1`.

Primary metrics are mean estimate, bias, RMSE, approximate-95% interval coverage, and positive-interval rate.

### Confounding boundary control

A binary context variable changes both trigger execution probability and closure probability, but treatment itself has **zero causal effect**.

The exact same generated trials are analyzed in two ways:

1. `correct_record_propensity`: each record contains its true context-specific assignment propensity;
2. `misspecified_marginal_propensity`: every record is assigned only the marginal treatment probability.

### G4 hypotheses

- **G4-C1:** randomized IPW bias and RMSE decrease with information/sample size and large injected effects are recovered reliably.
- **G4-C2:** null randomized effects do not systematically produce positive confidence intervals.
- **G4-C3:** under the zero-ATE common-cause construction, correct record-level propensities recover an effect near zero.
- **G4-C4 negative control:** replacing those propensities with the marginal propensity produces a large spurious positive effect.

### Claim boundary

The corrected confounding condition is not hidden-confounder identification from arbitrary observational logs: it assumes the relevant assignment propensity is known for each record. The misspecified condition exists specifically to demonstrate the failure when that information is not represented.

G4 remains an interventional/known-propensity identification track, not generic causal discovery.

---

## Retained publication-control run parameters

The first retained G2/G4 artifact uses the following fixed run sizes.

### G2 retained frontier

- activation probabilities: `{0.2,0.5,0.8}`;
- closure probabilities: `{0.4,0.8}`;
- correctly specified symmetric detector quality: sensitivity=specificity in `{0.55,0.75,0.95}`;
- additional misspecified missed-activation condition: true sensitivity `0.60`, true specificity `0.90`, assumed sensitivity `0.95`, assumed specificity `0.90`;
- threshold grid: `{0.05,0.10,0.20,0.30,0.40,0.50}`;
- trials per scenario/repetition: `3000`;
- independent repetitions per scenario: `10`;
- master seed: `20260925`.

The exact one-step decision agreement grid uses every generated G2 scenario, both detector observations, failure cost `10`, continue cost `0`, and detour costs `{1,2,4}`. Posterior, action and value differences between the direct reference and DynNav belief implementation must be zero to numerical tolerance.

### G4 retained sweep

- sample sizes: `{200,1000,5000}`;
- treatment propensities: `{0.2,0.5,0.8}`;
- injected ATEs: `{0.0,0.1,0.3,0.5}`;
- baseline closure probability: `0.1`;
- repetitions per randomized condition: `30`;
- confounding-control sample size: `5000`;
- confounding-control repetitions: `50`;
- binary context probability: `0.5`;
- treatment propensity high/low: `0.8/0.2`;
- outcome probability high/low: `0.8/0.1`;
- true treatment ATE in confounding control: exactly `0`;
- master seed: `20260925`.

No sample-size, threshold, sensor-quality or effect grid is retuned after inspection of this first retained artifact without a protocol version change.
