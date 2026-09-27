# DynNav Final Independent Audit Prompt

**Repository author:** Panagiota Grosdouli

Use this prompt for the final pre-submission audit of DynNav.

---

You are acting simultaneously as:

1. a senior robotics / autonomous-systems peer reviewer;
2. an algorithms and probability reviewer;
3. a reproducibility auditor;
4. a statistical reviewer;
5. a citation and literature fact-checker;
6. a research-integrity auditor;
7. an Area Chair / meta-reviewer.

Your task is to perform a **hostile-but-fair, source-verified, end-to-end audit** of the entire DynNav research repository and manuscript.

Do not assume the manuscript, README, evidence manifest, tables, figures, comments, CI summaries, or previous reviews are correct.

Treat every important scientific statement as a claim that must be independently verified.

Repository:

https://github.com/panagiotagrosdouli/DynNav

Repository author:

**Panagiota Grosdouli**

Primary manuscript:

`paper/dynnav_r/main.tex`

Also inspect the complete repository, including source code, tests, experiment generators, workflows, raw results, retained artifacts, evidence manifests, README files, protocol files, ROS 2/Nav2 code, Gazebo benchmarks, supplementary research notes, and publication-readiness documents.

If web access is available, independently verify all external scientific sources.

---

# CORE AUDIT RULES

Follow these rules throughout the review.

## Rule 1 — Never trust a number because it appears in the paper

Trace every publication-facing numerical result back to the lowest available evidence layer:

manuscript
→ evidence manifest
→ retained summary
→ raw trial data
→ generating code
→ frozen protocol / seed
→ workflow / commit provenance.

If any link is missing, say so.

## Rule 2 — Never trust a citation because it is in the bibliography

Every cited paper must be independently verified using authoritative sources where possible.

Prefer:

- IEEE Xplore;
- ACM Digital Library;
- Springer;
- Elsevier / ScienceDirect;
- PMLR;
- NeurIPS proceedings;
- Dagstuhl / LIPIcs;
- official conference/journal pages;
- Crossref;
- arXiv for genuine preprints.

Do not rely on Google snippets, Semantic Scholar, ResearchGate, citation mirrors, or random bibliography pages when a primary source exists.

## Rule 3 — Verify citation content, not only metadata

A real citation can still be misused.

For every citation in the manuscript, check whether the cited work actually supports the sentence in which it appears.

Flag:

- citation stretching;
- partial support;
- incorrect comparison;
- incorrect novelty distinction;
- incorrect publication status;
- misleading wording;
- missing seminal work.

## Rule 4 — Distinguish observation from inference

Label conclusions using the following evidence classes:

- **SOURCE VERIFIED** — verified from an authoritative external source;
- **RAW EVIDENCE VERIFIED** — verified from retained raw repository artifact;
- **CODE VERIFIED** — verified directly from implementation/tests;
- **MANUSCRIPT CLAIM ONLY** — stated but not independently established;
- **INFERENCE** — reasonable interpretation, not direct evidence;
- **UNVERIFIED** — evidence unavailable or insufficient;
- **CONTRADICTED** — available evidence conflicts with the claim.

Do not silently upgrade one class into another.

## Rule 5 — Do not protect the authors from criticism

If the contribution is incremental, say so.

If a theorem is mathematically correct but elementary, say so.

If a benchmark is constructed so that an outcome is nearly inevitable, say so.

If a baseline is unfair, say so.

If a citation threatens novelty, explain exactly how.

If a result is not strong enough for a claim, reject the claim.

Do not manufacture criticism merely to sound strict.

Every criticism must be technically justified.

---

# PART A — RECONSTRUCT THE PAPER FROM SCRATCH

Before reading the manuscript's own contribution list, reconstruct the project independently from the implementation and experiment code.

State:

1. the actual research problem;
2. the environmental model;
3. the planner state;
4. the stochastic variables;
5. the safe-return quantity being estimated;
6. the planner objective;
7. the baselines;
8. the evaluation unit;
9. the strongest empirical result;
10. the strongest mathematical result;
11. the strongest negative result;
12. the strongest limitation.

Then compare your reconstruction against the manuscript.

Report any discrepancy.

---

# PART B — CLAIM INVENTORY

Extract every meaningful scientific claim from:

- abstract;
- introduction;
- contribution list;
- related work;
- mathematical formulation;
- methods;
- results;
- captions;
- discussion;
- limitations;
- conclusion;
- README;
- evidence manifest;
- claim-evidence matrix.

Create a table:

| Claim | Location | Evidence required | Evidence found | Status | Problem |

Classify every claim as:

- SUPPORTED;
- PARTIALLY SUPPORTED;
- UNSUPPORTED;
- OVERSTATED;
- PRIOR ART;
- STANDARD / TRIVIAL;
- AMBIGUOUS.

Pay special attention to words such as:

- safe;
- safety;
- reliable;
- exact;
- optimal;
- significant;
- robust;
- general;
- novel;
- first;
- guarantee;
- improve;
- reduce;
- avoid;
- outperform;
- validate;
- real-time;
- scalable.

---

# PART C — NOVELTY AUDIT

Perform an independent literature search.

Do not merely inspect the bibliography.

Search specifically around:

- safe-return planning;
- returnability;
- safe exploration;
- SafeMDP;
- history-dependent robot risk;
- non-Markovian risk;
- state augmentation / Markovization;
- state abstraction;
- bisimulation;
- traversal-dependent graphs;
- self-deleting graphs;
- self-induced obstacles;
- Canadian Traveller Problem;
- uncertain-topology navigation;
- stochastic shortest path;
- decision-dependent uncertainty;
- endogenous uncertainty;
- action-dependent environmental transitions;
- dynamic doors / gates / passages;
- persistent action effects;
- contingency planning;
- backup-plan MPC;
- reachability-based safety;
- reversible planning;
- graph reliability;
- network reliability;
- cut-set reliability;
- stochastic network interdiction;
- MDPs / POMDPs with latent environmental modes.

Look specifically for any work that may already model:

executed action
→ activation of a future stochastic environmental event
→ changed graph connectivity
→ changed recoverability / safe return
→ history-dependent planning.

For each close work, report:

| Paper | What it already does | Overlap with DynNav | Difference that remains | Novelty threat |

Then give a novelty verdict using exactly one category:

- clearly novel;
- narrow but defensible novelty;
- incremental novelty;
- novelty unclear;
- substantially covered by prior work.

Never claim “first” unless independently justified.

---

# PART D — COMPLETE CITATION AUDIT

Audit every bibliography entry.

For each citation verify:

- paper exists;
- exact title;
- exact authors;
- year;
- venue;
- volume;
- issue;
- pages;
- DOI;
- arXiv identifier where applicable;
- peer-reviewed vs preprint status;
- whether the manuscript describes its status correctly.

Produce:

| Citation key | Exists? | Metadata correct? | DOI/arXiv correct? | Publication status correct? | Manuscript use correct? | Correction |

Then perform a sentence-level citation-content audit.

For every sentence containing citations:

1. extract the factual proposition;
2. open the cited source;
3. identify what the source actually claims;
4. determine whether the source supports the full sentence;
5. flag any citation stretching.

Also list:

### Missing seminal work

### Missing close prior work

### Novelty-threatening papers

### Citations that should be removed

### Citations that should be replaced

---

# PART E — MATHEMATICAL AUDIT

Independently check all mathematical definitions and propositions.

Verify:

- definition of safe-return reliability;
- augmented state;
- closure-event semantics;
- activation vs realization;
- independence assumptions;
- conditioning assumptions;
- same-cell conditioning;
- safe-set semantics;
- duplicate triggers targeting one latent closure event;
- whether probabilities are associated with events or triggers;
- whether active-hazard history is sufficient to make the process Markov.

Determine exactly when

`z = (x, A)`

is a sufficient state.

List assumptions under which it stops being sufficient, including:

- correlated hazards;
- delayed realization;
- time-dependent probabilities;
- partial observations;
- noisy trigger detection;
- hidden realization state;
- nonstationary hazards.

Audit the endpoint-aliasing result:

`max(|g(x)-R1|, |g(x)-R2|) >= |R1-R2|/2`.

Check:

- proof correctness;
- assumptions;
- significance;
- novelty;
- relation to state aggregation / abstraction / bisimulation.

Explicitly say if it is mathematically correct but elementary.

Do not present an elementary inequality as a major theorem.

---

# PART F — PLANNER CORRECTNESS

Audit both Python and C++ implementations.

Check:

- search state;
- transition semantics;
- trigger activation;
- initial activated hazards;
- duplicate-state handling;
- cost accumulation;
- return-oracle calls;
- heuristic;
- termination;
- completeness;
- optimality;
- admissibility;
- consistency;
- weighted-A* behavior;
- computational complexity;
- closure enumeration complexity.

Verify the exact scope of any optimality statement.

Check the configured `heuristic_weight` in publication runs.

If optimality only holds for `heuristic_weight = 1`, require the manuscript to say so.

---

# PART G — PLANNED VS EXECUTED HISTORY

This is a critical audit item.

Verify that:

planned search expansions
do NOT
modify persistent executed hazard history.

Persistent activation must come only from real executed transitions or the declared execution observation interface.

Audit:

- Python semantics;
- ROS 2 bridge;
- C++ Nav2 plugin;
- executed-transition subscription;
- history reset;
- trial isolation;
- observation resynchronization;
- sampling gaps.

Look for leakage in which hypothetical paths accidentally activate persistent hazards.

---

# PART H — PYTHON / C++ SEMANTIC PARITY

Compare Python and C++ definitions for:

- safe-set reachability;
- no-active-hazard behavior;
- closure conditioning;
- current-cell traversability;
- multiple triggers for one closure event;
- probability validation;
- exact return probability;
- trigger directionality;
- history persistence.

Flag any semantic mismatch.

Verify tests exist for important parity cases.

---

# PART I — BASELINE FAIRNESS

Audit:

- shortest path;
- state-only single-return baseline;
- state-only exact baseline;
- exact history-conditioned planner;
- critical-cut history planner;
- hard safe-return threshold baseline.

For each baseline report:

| Baseline | Information available | Oracle | Objective | Fair comparison? | Scientific role |

Most importantly, verify that the publication-facing state-only exact baseline uses:

- the same exact connectivity oracle;
- the same fragility objective;
- the same environment probabilities;

while differing primarily in whether return probability is conditioned on executed activation history.

If not, state that representation and estimator quality are confounded.

Do not treat the state-only baseline as representative of all MDP/POMDP approaches.

---

# PART J — EXPERIMENT DESIGN AUDIT

For every experiment identify:

- hypothesis;
- independent variable;
- dependent variable;
- random variable;
- pairing strategy;
- unit of analysis;
- number of scenarios;
- number of seeds;
- predeclared/frozen status;
- post-hoc decisions;
- whether test worlds structurally favor one method.

Separate:

1. controlled mechanism experiments;
2. held-out probability/horizon tests;
3. hand-authored geometry tests;
4. unavoidable-hazard generated suite;
5. approximation/scaling experiments;
6. objective-sensitivity tests;
7. ROS 2/Nav2/Gazebo integration experiments.

Look for:

- data leakage;
- benchmark tuning after seeing results;
- pseudo-replication;
- repeated use of the same scenario family;
- trivial trigger-free escape;
- insufficient topology diversity;
- unbalanced baselines.

---

# PART K — 96-SCENARIO EXPANDED SUITE

Audit the publication-facing expanded unavoidable-hazard suite independently.

Verify from raw artifacts:

- scenario count;
- generator seed;
- seed count per scenario;
- total trials per planner;
- every-route-has-hazard invariant;
- planner list;
- same-oracle baseline;
- actual per-scenario outcomes.

Check the aggregate results from raw data.

Do not trust manuscript values.

Recalculate:

- mean state-only exact return-infeasibility;
- mean history-exact return-infeasibility;
- scenario-level mean difference;
- 95% bootstrap interval;
- number of improved scenarios;
- number of non-worse scenarios;
- mean exact return probability;
- mean path length;
- mean activated hazards.

Check whether the statistical unit for the confidence interval is correctly the scenario rather than each individual seed when the claim is cross-scenario generalization.

Assess whether the 96 scenarios are genuinely distinct enough to justify calling this broader evidence.

State explicitly that a structured synthetic generator is not arbitrary-map or deployment generalization.

---

# PART L — STATISTICS AUDIT

Verify all statistical methods from implementation.

Check:

- paired common random numbers;
- seed matching;
- bootstrap level;
- scenario-level vs trial-level resampling;
- McNemar implementation;
- confidence level;
- number of bootstrap resamples;
- independence assumptions;
- multiple comparison issues;
- effect-size interpretation.

For empirical zero failures:

- distinguish zero observed failures from zero true probability;
- calculate an appropriate binomial confidence bound if statistically relevant;
- determine whether zero risk follows analytically from the declared model instead of from sampling.

Do not use extremely small p-values as the main scientific evidence when the effect is structurally determined.

Prefer:

- effect size;
- confidence interval;
- scenario-level robustness;
- trade-off measurements.

---

# PART M — RESULT REPRODUCTION

Trace all publication-facing numbers to retained evidence.

At minimum verify:

- same-state/different-history separation;
- analytic phase boundary;
- controlled execution;
- held-out module counts;
- geometric held-out worlds;
- hard-safe-return negative result;
- state-only exact control;
- expanded unavoidable-hazard suite;
- approximation scaling;
- augmented-state search scaling;
- joint-cut counterexample;
- repeated timing distributions;
- Gazebo integration results.

Create:

| Result | Manuscript value | Recomputed raw value | Match? | Evidence class |

Any mismatch, even rounding, must be reported.

---

# PART N — TIMING / PERFORMANCE AUDIT

Timing claims require special treatment.

Check:

- which clock is used;
- warm-up count;
- repetition count;
- whether diagnostics are inside or outside the measured interval;
- whether the planner's internal timing matches the intended online computation;
- runner / CPU environment;
- median;
- Q1;
- Q3;
- IQR;
- p95;
- mean;
- min/max if useful.

Verify exact-vs-cut timing and planner-level timing from raw retained trial rows.

Timing values must be described as:

**runner-specific descriptive measurements**

unless a stronger benchmarking protocol justifies broader claims.

Never convert CI-run timing into a hardware-independent real-time guarantee.

Check artifact provenance carefully because timings may differ between CI executions.

The publication must point to one pinned retained timing artifact.

---

# PART O — CRITICAL-CUT APPROXIMATION

Audit independently.

Check:

- mathematical upper-bound direction;
- independence assumption;
- exactness conditions;
- individually critical cells;
- multi-cell cutsets;
- optimistic failure modes;
- adversarial counterexample.

Compare the approach with classical network-reliability and cut-set literature.

Determine whether this belongs as:

- a main contribution;
- a supporting approximation;
- supplementary material.

Do not credit standard network-reliability reasoning as novel.

---

# PART P — GAZEBO / ROS 2 / NAV2

Audit execution evidence at separate levels.

Determine whether the repository establishes:

1. plugin exists;
2. plugin builds;
3. plugin tests pass;
4. executed history persists correctly;
5. independent trials reset history;
6. planned paths do not activate persistent history;
7. valid paired Gazebo trials exist;
8. outbound navigation succeeds;
9. trigger observation works;
10. closure injection works;
11. recovery assessment works;
12. comparative efficacy is supported;
13. physical-robot efficacy is supported.

Do not collapse these into one “validated in Gazebo” statement.

For the retained Gazebo mechanism probe independently verify:

- number of repetitions;
- number of planners;
- valid trials;
- navigation successes;
- paired latent draws;
- trigger observations;
- closure realizations;
- closure applications;
- recovery feasibility.

If the history planner differs from the comparison by only one or a few trials, determine whether that is enough for an efficacy claim.

If not, explicitly state:

> ROS 2/Nav2/Gazebo integration is demonstrated, but comparative execution-level efficacy is not established.

Do not infer hardware evidence from Gazebo.

---

# PART Q — REPRODUCIBILITY AUDIT

Evaluate whether an independent researcher can reproduce the central paper.

Inspect:

- Python version;
- dependency versions;
- ROS version;
- test commands;
- workflow definitions;
- random seeds;
- generator seeds;
- frozen protocols;
- raw CSV/JSON retention;
- artifact IDs;
- artifact digests;
- commit hashes;
- evidence manifest;
- claim-evidence matrix;
- README commands.

Rate:

- Excellent;
- Good;
- Moderate;
- Weak;
- Not reproducible.

Explain the rating.

Check that artifact metadata is internally consistent.

Example failure to detect:

a raw run may contain 96 scenarios while an old protocol file accidentally still says 24.

Do not ignore provenance inconsistencies even when the numerical result is correct.

---

# PART R — REPOSITORY-WIDE CONSISTENCY AUDIT

Search the entire repository for stale or contradictory numbers.

Check whether README, manuscript, claim matrix, submission-readiness report, evidence manifest, reviewer audit, figures, tables, and captions all agree.

Search for old values from superseded runs.

Examples:

- old 24-scenario values after a 96-scenario suite exists;
- single-shot latency after repeated timing measurements exist;
- stale artifact IDs;
- stale commit hashes;
- pre-fix Gazebo outcomes described as current;
- old terminology such as “irreversible failure” after metric wording changed.

List every stale statement.

---

# PART S — TABLE AND FIGURE AUDIT

Review each table and figure as both a scientist and a reviewer.

Ask:

- Does it communicate the central contribution?
- Is it redundant?
- Does it make a constructed benchmark look more important than it is?
- Are many zero entries visually dominating the Results section?
- Would a figure communicate the result better?
- Are captions scientifically precise?
- Are confidence intervals or sample counts missing?
- Are numbers overly precise?

For the main Results section, assess whether the expanded unavoidable-hazard suite should be visually central.

Consider whether controlled zero-heavy tables belong in:

- appendix;
- supplementary material;
- one compressed mechanism table.

Recommend a publication-quality structure.

---

# PART T — MANUSCRIPT LANGUAGE AUDIT

Review every section:

- title;
- abstract;
- introduction;
- related work;
- formulation;
- method;
- experiments;
- results;
- discussion;
- threats to validity;
- conclusion.

Flag:

- overclaiming;
- defensive wording;
- redundancy;
- ambiguous terms;
- undefined notation;
- excessive caveats;
- hidden assumptions;
- conclusions stronger than evidence.

Rewrite any sentence whose current wording is not fully supported.

For every proposed rewrite, explain why.

---

# PART U — RESEARCH-INTEGRITY AUDIT

Look specifically for:

- fabricated or unverifiable citations;
- fabricated numbers;
- selective reporting;
- omitted negative results;
- hidden benchmark exclusions;
- outcome-dependent tuning;
- inconsistent seeds;
- overwritten artifacts;
- mismatch between claim and retained evidence;
- apparent p-hacking;
- inappropriate safety claims.

Do not infer misconduct from an ordinary bug or documentation mismatch.

Separate:

- error;
- methodological weakness;
- reporting weakness;
- research-integrity concern.

---

# PART V — AUTHOR / REPOSITORY METADATA AUDIT

Verify that repository author metadata consistently identifies:

**Panagiota Grosdouli**

Check:

- top-level README;
- Greek README;
- CITATION.cff;
- pyproject.toml;
- ROS package maintainers;
- any author metadata intended for public repository use.

Important:

The manuscript may intentionally contain “Anonymous Author(s)” for double-blind review.

Do NOT replace anonymous manuscript metadata unless the selected venue is confirmed to allow author identification.

For camera-ready preparation, separately report what author/affiliation fields must be restored.

---

# PART W — THREE INDEPENDENT REVIEWS

Produce three genuinely independent reviews.

## Reviewer 1 — Robotics / Motion Planning

Focus on:

- robotics significance;
- planning formulation;
- realism;
- execution evidence;
- baseline relevance;
- integration.

Output:

- Summary;
- Strengths;
- Major concerns;
- Minor concerns;
- Questions;
- Required changes;
- Confidence 1–5;
- Recommendation.

## Reviewer 2 — Algorithms / Probability

Focus on:

- mathematical validity;
- Markovization;
- representation claim;
- state abstraction;
- graph reliability;
- computational complexity;
- novelty.

Same output fields.

## Reviewer 3 — Experimental / Reproducibility

Focus on:

- experiment design;
- pairing;
- statistical unit;
- confidence intervals;
- artifact provenance;
- frozen protocols;
- reproducibility;
- reporting.

Same output fields.

Use recommendations:

- Strong Accept;
- Weak Accept;
- Borderline;
- Weak Reject;
- Strong Reject.

Do not force reviewer agreement.

---

# PART X — META-REVIEW

Act as Area Chair.

Report:

## Strongest reason to accept

## Strongest reason to reject

## Novelty verdict

## Evidence verdict

## Reproducibility verdict

## Most dangerous reviewer objection

Write the objection exactly as a skeptical reviewer might.

Then give the strongest scientifically honest response.

## What would change the decision?

Identify the minimum additional evidence or revision that would move the recommendation upward.

---

# PART Y — FINAL SOURCE-VERIFIED CITATION REPORT

End with:

### Verified and correctly used citations

### Real citations with metadata errors

### Real citations used too strongly

### Missing seminal work

### Missing close prior work

### Novelty-threatening work

For every novelty-threatening paper explain:

- what it does;
- what overlaps;
- what remains distinct;
- whether the DynNav claim survives.

---

# PART Z — FINAL RESULT-VERIFICATION REPORT

Produce a table:

| Experiment | Raw artifact found? | Recomputed? | Paper matches? | Statistical design OK? | Claim allowed? |

Include all publication-facing experiments.

Then give:

### Numbers safe to publish

### Numbers that need correction

### Results that are only descriptive

### Results that must not support efficacy/safety claims

---

# FINAL REVISION PLAN

Create a prioritized table:

| Priority | Problem | Evidence | Exact fix | Effort | Acceptance impact |

Use:

- **P0** — must fix before submission;
- **P1** — strongly recommended;
- **P2** — useful;
- **P3** — optional.

Do not give vague recommendations.

For example, do not say:

“run more experiments.”

Instead say:

“Generate N frozen topologies using X predeclared generator, use Y paired seeds, report scenario-level bootstrap CI on history-minus-state-only exact risk difference.”

---

# FINAL SUBMISSION VERDICT

End with exactly these fields:

**Scientific correctness:**  
PASS / CONDITIONAL PASS / FAIL

**Citation integrity:**  
PASS / CONDITIONAL PASS / FAIL

**Result reproducibility:**  
PASS / CONDITIONAL PASS / FAIL

**Statistical validity:**  
PASS / CONDITIONAL PASS / FAIL

**Novelty:**  
CLEAR / NARROW-BUT-DEFENSIBLE / INCREMENTAL / UNCLEAR / COVERED

**Robotics evidence:**  
STRONG / ADEQUATE / LIMITED / INSUFFICIENT

**Submission readiness:**  
GO / CONDITIONAL GO / NO-GO

Then explain the decision in no more than five paragraphs.

---

# MOST IMPORTANT INSTRUCTION

Do not evaluate the paper based on how polished it sounds.

Evaluate whether every important sentence survives independent verification against:

- source literature;
- mathematics;
- implementation;
- raw evidence;
- statistical design;
- retained provenance.

If the sources do not support a statement, say so explicitly.

If evidence is unavailable, do not guess.

If a conclusion is an inference rather than a fact, label it as an inference.

The goal is not to make DynNav look impressive.

The goal is to make sure that what Panagiota Grosdouli submits is **scientifically defensible, source-verifiable, reproducible, and difficult for a careful reviewer to invalidate**.
