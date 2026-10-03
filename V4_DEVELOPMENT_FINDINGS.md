# V4 Development Findings

**Status:** development-only mechanism evidence. Not publication-facing. Not authorized for manuscript claims.

**Workflow run:** 37103838608  
**Head SHA:** 912350d34df65aed6338b02d349797366523663c  
**Artifact ID:** 11267051205  
**Artifact digest:** `sha256:f0bc231f16e32082429c5a049c99fa19210abe72e6830f52f122c2a9f55cf991`  
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

`f0bc231f16e32082429c5a049c99fa19210abe72e6830f52f122c2a9f55cf991`.

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
