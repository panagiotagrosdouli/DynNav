# V4 Pre-Outcome Freeze Audit

**Project:** DynNav  
**Protocol:** `EXPERIMENT_PROTOCOL_V4.md`  
**Branch:** `research/belief-conditioned-v4`  
**Status:** pre-outcome freeze candidate; held-out outcomes not yet authorized

## Scientific question

The V4 study tests whether a posterior belief over latent, action-induced topology state contains decision-relevant safe-return information beyond geometric state, fixed marginals, or a detector-as-truth approximation.

The primary representation is

\[
(x_t,b_t), \qquad
b_t(A)=P(A_t=A\mid u_{0:t-1},o_{0:t}).
\]

The causal semantics are fixed as:

\[
\text{known trigger execution}
\rightarrow
\text{latent hazard arming}
\rightarrow
\text{noisy arming observation}
\rightarrow
\text{future closure realization}.
\]

This avoids conflating latent environmental response with uncertainty about whether a known geometric transition occurred.

## Novelty boundary

The V4 study does **not** claim novelty for:

- history-aware planning;
- safe-return planning;
- belief-space/POMDP navigation;
- stochastic topology;
- self-deleting/action-induced topology;
- endogenous or decision-dependent uncertainty.

The bounded research target is their narrower intersection: safe-return connectivity when robot actions induce a latent environmental topology-exposure state that is only partially observed.

## Development evidence already inspected

Development evidence has been inspected and therefore cannot be used for unbiased headline claims.

Observed development findings include:

- belief conditioning can improve probability calibration relative to detector-as-truth;
- belief conditioning does not necessarily reduce operational failure relative to detector-as-truth in every regime;
- a prior-only planner can be safer while taking longer routes;
- under miss-heavy sensing, belief tracking may collapse toward conservative prior-only behavior.

These findings motivated making `prior_only` a mandatory strong comparator and framing the study around the risk-efficiency frontier rather than universal safety superiority.

No development outcome may be promoted to held-out evidence.

## Frozen primary comparison

Primary observation regime:

- O2: sensitivity = 0.85
- O2: specificity = 0.85

Primary method:

- `belief`

Mandatory primary baselines:

- `detector_as_truth`
- `prior_only`

Additional retained comparators:

- `shortest`
- `fixed_marginal_exact`
- `activation_oracle`
- `hard_belief`

Primary operational endpoint:

\[
\Delta_{risk}
=
risk(\text{belief})-risk(\text{detector-as-truth}).
\]

Primary probabilistic endpoint:

\[
\Delta_{Brier}
=
Brier(\text{belief})-Brier(\text{detector-as-truth}).
\]

The corresponding belief-vs-prior-only effects are mandatory companion analyses and must be reported even if they weaken the headline conclusion.

## Held-out scenario freeze

The committed V4 manifests are authoritative:

- `benchmarks/v4/development.json`
- `benchmarks/v4/validation.json`
- `benchmarks/v4/heldout.json`

Held-out design:

- 96 scenarios;
- 8 topology families;
- 12 scenarios per family;
- 250 paired stochastic seeds per scenario in primary O2;
- 7 planner conditions;
- deterministic keyed common random numbers.

Committed manifest digests are stored in:

`benchmarks/v4/SHA256SUMS.txt`

The held-out manifest must not be regenerated after authorization.

## Statistical freeze

The primary analysis is scenario-weighted and paired.

Inference hierarchy:

\[
\text{scenario}
\rightarrow
\text{paired execution seed}.
\]

Publication intervals use hierarchical bootstrap:

1. resample scenarios with replacement;
2. resample paired seed indices within selected scenarios;
3. preserve planner pairing.

Primary publication output uses 5,000 bootstrap replicates with frozen seed `2026100304`.

Mission failure, operational failure, conditional return risk, Brier loss, and path length are kept distinct. Mission failures must not be silently dropped from the comparison.

## Information barrier

Only `activation_oracle` may read true armed state during decision making.

Non-oracle planners receive only their permitted information:

- detector-as-truth: detector observations;
- belief: detector observations plus declared probabilistic model;
- prior-only: predictive model without detector conditioning;
- fixed-marginal: frozen marginal field;
- shortest: geometry only.

Post-hoc scoring may read simulator truth.

Any ground-truth leakage invalidates the affected publication run.

## Artifact integrity

The held-out pipeline must retain:

- frozen Git SHA;
- manifest SHA-256;
- per-shard raw trial SHA-256;
- complete per-scenario planner/seed key set;
- merged raw `trials.csv`;
- run metadata;
- hierarchical analysis output;
- calibration output;
- generated publication tables/figures;
- final artifact digest.

Shard merging must reject:

- missing shards;
- digest mismatch;
- duplicate trial keys;
- incomplete per-scenario seed/planner grids;
- disagreement in frozen metadata.

## Null and failure-boundary obligations

Regardless of headline result, the paper must report:

- perfect-sensing O0 behavior;
- uninformative O6 behavior;
- F8 history-irrelevant controls;
- model misspecification;
- path-cost trade-offs;
- hard-constraint comparison;
- regimes where belief tracking provides no measurable advantage.

Negative results are retained.

## Authorization rule

Held-out execution is prohibited until the freeze candidate passes the preflight test suite and the exact authorized commit is recorded.

After authorization, no semantic change to:

- planner decision logic;
- belief update;
- scenario manifests;
- stochastic event semantics;
- primary endpoints;
- statistical analysis;
- pairing rules

is permitted without invalidating the run and creating a new protocol amendment.

The authorization commit itself may only add the authorization record and must not alter research semantics.
