# V4 held-out O2 — post-outcome scientific review

**Status:** post-outcome evidence review; research decision, **not** a publication claim or an amendment to the frozen protocol.  
**Review date:** 2026-11-01  
**Frozen code SHA:** `610acd5d0aed2d0444fb0205fe1957fa98e4eabe`  
**Workflow:** [V4 held-out evidence, run 37113486282](https://github.com/panagiotagrosdouli/DynNav/actions/runs/37113486282)  
**Canonical merged artifact:** `dynnav-v4-heldout-o2-610acd5d0aed2d0444fb0205fe1957fa98e4eabe` (artifact ID `11273171128`, not expired when reviewed)  
**Scope:** **O2** observation regime, exact frozen scenario set. This review does not infer results for unrun observation regimes, different world models, or physical robots.

## 1. Integrity and sampling checks

The downloaded merged ZIP contains `provenance.json`, `run_metadata.json`, `trials.csv`, `v4_analysis.json`, and the publication table and calibration exports. All **seven** listed file hashes in `provenance.json` were independently checked against their bytes and matched.

| Check | Verified value |
|---|---:|
| Scenarios | 96 |
| Topology families | 8 (12 scenarios each) |
| Paired execution seeds per scenario | 250 |
| Trial records | 168,000 |
| Trial records per planner | 24,000 |
| Planners | 7 |
| Invalid protocol rows | 0 |
| Bootstrap resamples in retained analysis | 5,000 |
| Bootstrap seed | 2026100304 |
| Assumed / true sensitivity and specificity in O2 | 0.85 / 0.85 |

**Statistical unit:** the primary retained intervals are scenario-level/hierarchical estimates (96 scenarios); **168,000 trial rows are not 168,000 independent scenarios**.

The signed differences below use **belief minus baseline**. Lower operational/return failure and Brier scores are favorable; longer paths involve additional movement cost. Values and 95% intervals come from the retained `v4_analysis.json` and `publication/table_v4_primary.tex`, not an independently redesigned hypothesis test.

## 2. Main retained comparisons

| Belief minus baseline | Operational failure (pp) | Brier difference | Path-length difference |
|---|---:|---:|---:|
| Fixed-marginal exact | **−8.679** [−12.388, −5.267] | **−0.07175** [−0.09309, −0.05206] | **+0.3787** [+0.2195, +0.5604] |
| Detector-as-truth | +0.167 [+0.000, +0.446] | **−0.00730** [−0.01094, −0.00417] | −0.0082 [−0.0210, 0.0000] |
| Prior-only | +0.175 [−0.200, +0.758] | **−0.00723** [−0.01150, −0.00342] | −0.0172 [−0.0890, +0.0345] |
| Activation oracle | +0.200 [+0.000, +0.525] | +0.00785 [+0.00409, +0.01208] | −0.0061 [−0.0175, 0.0000] |

**Interpretation:** belief tracking clearly improves the O2 return-risk versus the fixed-marginal state-only comparator, at some path cost. It also improves probabilistic scoring versus both detector-as-truth and prior-only. **It does not establish a safe-return/operational improvement over those stronger information baselines** in this O2 suite. A calibration gain should not be advertised as a navigation-safety gain.

## 3. Decision-level check, from matching paired paths

Paired `(scenario,seed)` paths were compared descriptively across all 24,000 pairs per method, without an additional significance test.

| Belief vs comparator | Different realized path | Fraction | Families with any difference |
|---|---:|---:|---|
| Fixed-marginal exact | 6,132 / 24,000 | **25.55%** | F1, F2, F4, F6 |
| Prior-only | 212 / 24,000 | **0.88%** | **F6 only** |
| Detector-as-truth | 98 / 24,000 | **0.41%** | **F6 only** |
| Activation oracle | 163 / 24,000 | **0.68%** | **F6 only** |

F8's nominal null-control family showed **no path change** against those comparators. However, this single O2/family result is **not** a substitute for the predeclared O0, O6, model-misspecification, or correlation regimes.

The pattern is a useful **research-positioning constraint**: it supports an information-state/calibration contribution more directly than it supports a broad claim that observing posterior belief frequently changes decisions relative to well-matched alternatives.

## 4. Hard-belief comparison is not a like-for-like calibration result

`hard_belief` completed 15,684 / 24,000 missions (**65.35%**), while `belief` completed 24,000 / 24,000 (**100%**) in the retained O2 suite. Its calibration/Brier table uses only **15,684** completed cases; comparing that favorable-looking conditional Brier (0.00112) directly with belief's full-population Brier (0.06011) would confound sample selection with predictor quality. The paired retention report records **8,316 asymmetric mission-success pairs**.

Interpret this result as a **coverage/mission-completion versus return-risk trade-off**, not evidence that hard-belief is universally better calibrated. A fair analysis should jointly present mission completion, operational failure and return feasibility and should preserve the predeclared denominator conventions.

## 5. Calibration exports

The retained O2 calibration table reports:

| Planner | Brier | ECE | n |
|---|---:|---:|---:|
| Activation oracle | 0.05226 | 0.00258 | 24,000 |
| **Belief** | **0.06011** | **0.00340** | 24,000 |
| Prior-only | 0.06734 | 0.00285 | 24,000 |
| Detector-as-truth | 0.06741 | 0.02406 | 24,000 |
| Fixed-marginal exact | 0.13185 | 0.12223 | 24,000 |
| Hard-belief | 0.00112 | 0.00000 | 15,684 (selected completions) |

Brier and ECE measure different properties: belief improves Brier over prior-only despite slightly larger reported ECE. Neither number alone proves safer navigation.

## 6. Gate-by-gate decision relative to the frozen protocol

- **Reproducibility/provenance (O2): supported.** Run/artifact, frozen SHA, counts and file digests are retained.
- **Information-state representation: supported as a mechanism**, conditional on the frozen synthetic model; the posterior matters for return-risk estimation and for some paths versus the fixed baseline.
- **Decision effect versus strong competitors: limited in O2.** Only 0.88% and 0.41% of paired paths differ from prior-only and detector-as-truth respectively, confined to F6; no convincing operational benefit in the primary O2 aggregate.
- **Correct-specification calibration: encouraging but conditional.** Better Brier than prior/detector in O2, with caveats about ECE and comparator conditioning.
- **Null controls:** F8 route-choice null passes descriptively in O2; **other predeclared noise regimes remain unassessed in this artifact**.
- **Misspecification, correlated closure, full noise sweep, and physical-robot generalization:** cannot be judged from this O2 artifact.
- **Hard-versus-soft objective:** needs an explicit joint completion/risk assessment, not a Brier ranking over differently selected populations.

**Recommendation — HOLD for standalone V4 manuscript.** The O2 suite supports a promising calibrated-belief representation, but the stronger novelty claim of operationally better *decisions* under partial observation is **not established against the strongest controls**. Preserve the results regardless of sign; complete already-predeclared regimes and test gates before a publication GO/NO-GO decision. If strong controls continue to tie or outperform belief on operational outcomes, retain V4 as a carefully scoped calibration/representation follow-up to the V3 known-history paper.

## 7. Immediate, protocol-preserving next steps

1. Reconcile `REVIEWER_AUDIT_V4.md` and the freeze checklist **only after** the remaining predeclared outcome suites are reviewed; preserve original checkboxes and timestamps as historical pre-outcome state. This report is explicitly post-outcome.
2. Run/analyze frozen **O0, O6 and model-misspecification** controls with SHA-verified manifests and retained artifacts. Do not change sample size, seeds, estimands or baselines after seeing O2.
3. Report scenario-family effects, paired route changes and honest failure/completion trade-offs alongside Brier/reliability diagrams.
4. Confirm whether F6-only route changes versus prior-only/detector reflect a reproducible predeclared mechanism; treat any **new** hypotheses as exploratory and subject to a fresh freeze.
5. Keep benchmark-code, scenario and estimator definitions unchanged in this documentation-only review PR.

## 8. Source and reproduction pointers

- **Raw data:** workflow artifact ID `11273171128` from run [37113486282](https://github.com/panagiotagrosdouli/DynNav/actions/runs/37113486282).
- **Artifact integrity:** `provenance.json` recorded `trials.csv` SHA256 `ed84db8174dd955e7069930e8f577430e0596badbaa031c71a53bb7e72981620` and `v4_analysis.json` SHA256 `23cdf5542166c1b7d484f4f5089695c0d0c2bbfb54e231fa14510f4511d094b4`.
- **Protocol:** `EXPERIMENT_PROTOCOL_V4.md` (frozen prior to O2 results).
- **Review gates:** `REVIEWER_AUDIT_V4.md`.
- **Output synthesis:** `scripts/render_v4_publication_outputs.py` and `dynnav/experiments/v4_analysis.py`.

**This file is the first outcome inspection record; it must not retroactively alter the frozen pre-outcome documents or authorize manuscript claims by itself.**
