# G3/G5 Publication-Control Protocol

**Freeze date:** 2026-09-25
**Status:** frozen before the retained G3 information-assumption and G5 peak-memory artifacts.

## G3 — which assumption breaks exposure-only non-identifiability?

The no-exposure theorem establishes that the target closure probability cannot be learned when trigger-conditioned outcomes are the only information source and the trigger is never exposed.

### Frozen information classes

1. `strict_credible_gate`: target-trigger feedback only; no admitted exploration budget.
2. `risk_budget_20`: target-trigger observations admitted under the existing finite cumulative exploration-risk budget.
3. `passive_same_parameter`: risk-free Bernoulli observations that are explicitly assumed to measure the same target parameter.
4. `transfer_shared_parameter_bias_-0.20`, `+0.00`, `+0.20`: risk-free observations from a related trigger, analyzed under a shared-parameter assumption. Nonzero biases are deliberate structural-misspecification controls.
5. `oracle_known_probability`.

### Frozen grid

- true target closure probability: `{0.1, 0.3, 0.5, 0.7}`;
- minimum return threshold: `{0.5, 0.7, 0.9}`;
- opportunities per condition: `1000`;
- independent repetitions per condition: `20`;
- confidence: `0.90`;
- risk budget: `20.0`;
- passive observation probability per opportunity: `0.25`;
- transfer observation probability per opportunity: `0.25`;
- prior: `Beta(1,3)`;
- master seed: `20260925`.

### G3 primary outcomes

- posterior absolute error;
- target-trigger exposure count;
- realized target-trigger failures;
- side-information sample count;
- cumulative risk-budget spend;
- explicit structural bias of the transfer source.

### Frozen G3 hypotheses

- **G3-P1:** in cold-start locked regimes, the strict gate receives no target information and its uncertainty/error does not improve with more opportunities.
- **G3-P2:** risk-budget exploration can reduce error by acquiring target data, but realized failures are retained as the cost of that information.
- **G3-P3:** correct same-parameter passive information can reduce error without target-trigger failures.
- **G3-P4:** transfer works when the shared-parameter assumption is correct; deliberate transfer bias produces persistent target-parameter bias despite large side-information sample counts.
- **G3-P5:** no method is compared without reporting the additional information/risk assumption that makes identification possible.

## G5 — exact quotient computational scaling

### Frozen family

The existing duplicated-trigger diamond-chain family is used with module counts `{2,3,4,5,6}`. Each module has two trigger identities that activate one identical closure event.

### Frozen planner configuration

- raw history-aware A*;
- exact closure-event quotient A*;
- step cost: repository default;
- recoverability weight: `2.0` for the publication-control run;
- identical map, start, goal and safe region.

### G5 primary outcomes

- raw and quotient optimal objective;
- final return probability;
- A* nodes expanded;
- A* peak traced Python memory;
- complete reachable augmented-state count;
- complete reachable-state enumeration peak traced memory;
- raw/quotient state-count ratio.

### Frozen G5 hypotheses

- **G5-P1:** objective and final return remain equal to numerical tolerance for every module count.
- **G5-P2:** quotient reachable-state count never exceeds raw reachable-state count.
- **G5-P3:** the reachable-state compression ratio increases as duplicate-trigger modules accumulate.
- **G5-P4:** peak memory/node expansion may be noisy or non-monotone at small sizes; such observations are retained. No universal runtime/memory dominance claim is authorized from one Python benchmark.

## Claim boundary

G3 compares information assumptions, not universally available sensing modalities. G5 is an exact quotient for the independent closure-event semantics only. Neither protocol broadens the G1 dependence-model claim.
