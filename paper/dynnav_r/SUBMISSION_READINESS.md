# DynNav Submission-Readiness Audit

## Central claim

> When executed robot actions can activate future topology hazards, activated-hazard history can contain safe-return-connectivity information that a state-only marginal environmental-risk representation cannot, in general, represent from geometric state alone.

This is a representation/mechanism claim. It is not universal planner superiority, certified safety, arbitrary-map generalization, real-world probability calibration, or physical-robot efficacy.

## September 25, 2026 paper-hardening pass

The submission branch now strengthens the manuscript in four ways:

- adds a formal endpoint-aliasing lower bound: for same-endpoint histories with reliabilities (R_1,R_2), every deterministic endpoint-only scalar estimate has worst-history absolute error at least (|R_1-R_2|/2);
- expands direct novelty constraints to include returnability-based safe exploration, uncertain-MDP safe-return planning, traversal-dependent edge deletion, shortest pathfinding on self-deleting graphs, and coverage with self-induced obstacles;
- reorganizes the evaluation around four research questions: representation, planning consequence, objective sensitivity, and computational/approximation boundary;
- distinguishes empirical zero observed failures from formal zero-risk or safety guarantees.

Citation-key integrity on the branch is clean: every manuscript citation key resolves to exactly one bibliography entry, with no unused entries. The closest new bibliography records were checked against venue/DOI or authoritative archive metadata.

The surviving paper claim is intentionally narrower than any of the individual prior-art categories: **executed transitions activate stochastic future closures; activation and realization are distinct; the resulting activation history can change safe-return connectivity at the same geometric endpoint.**


## Raw-artifact verification completed

The publication-facing retained evidence has now been checked below the README/manuscript layer by downloading the actual GitHub Actions artifacts.

### Hazard-planner retained artifact

- workflow run: `34714856493`
- artifact: `10303733811`
- artifact digest: `sha256:2d45ba9666be630b27c31138e954fdfcf9fc3d0a6db741a1e783ffe9f94ca135`
- retained raw directories include information-gap, phase-boundary, stochastic execution, held-out history generalization, cut scaling, augmented-state scaling, hard-threshold sensitivity, and joint-cut counterexample trials/summaries.

Verified values from the downloaded artifact:

| Experiment | Raw retained result | Audit status |
|---|---|---|
| Same-state/different-history | 5 trials; mean separation `0.5`; maximum separation `0.9`; risky-history state-only max abs error `0.0` | VERIFIED |
| Analytic phase boundary | 75 trials; analytic-boundary match rate `1.0` | VERIFIED |
| Homogeneous execution p=0.2 | shortest/state-only `0.512`; exact/cut/hard `0.000`; 1000 trials/planner | VERIFIED |
| Homogeneous execution p=0.5 | shortest/state-only `0.881`; exact/cut/hard `0.000`; 1000 trials/planner | VERIFIED |
| Homogeneous execution p=0.8 | shortest/state-only `0.992`; exact/cut/hard `0.000`; 1000 trials/planner | VERIFIED |
| State-only control | identical failure outcomes to shortest at p=0.2/0.5/0.8; discordant pairs `0`; exact McNemar `p=1.0` | VERIFIED |
| 6/7/8-module held-out | shortest/state-only `0.992 / 0.998 / 1.000`; exact history `0 / 0 / 0`; 500 paired trials/scenario | VERIFIED |
| Exact vs critical-cut scaling | at 12 hazards exact `49.539307 ms`, cut `0.262433 ms`, retained ratio `188.769350661x`; max cut error `0.0` in this series-critical construction | VERIFIED, REPRESENTATIVE TIMING ONLY |
| Augmented-state scaling at 6 modules | shortest: 25 nodes / 24 length / `0.178244 ms`; cut: 72 / 36 / `5.537094 ms`; exact: 72 / 36 / `12.496013 ms` | VERIFIED, REPRESENTATIVE TIMING ONLY |
| Joint-cut counterexample | 9/9 optimism/disagreement settings; exact return on cut route `0.96`, `0.75`, `0.36` for p=0.2/0.5/0.8; cut estimate `1.0`; equal path length 6 | VERIFIED |

The stochastic artifact also contains the paired binary statistics. At p=0.8, exact-history versus shortest has risk difference `-0.992`, 95% paired bootstrap interval `[-0.997,-0.986]`, 992 baseline-only discordant events, zero proposed-only events, and two-sided exact McNemar p-value `4.778309726736481e-299`.

### Frozen geometric retained artifact

- workflow run: `34823759539`
- source SHA: `8552a42466b598fcf12c9e20137eb4166b866cbd`
- artifact: `10339442639`
- artifact digest: `sha256:d8b59cfd6432d8ade1351b882cc29c6371e3437504346322817d41bb4b608e93`
- raw trial rows: 4500 = 3 scenarios x 3 planners x 500 paired seeds.

Verified from raw `trials.csv` and `summary.json`:

| Scenario | Shortest | State-only | Exact history | Path length shortest/history | Activated hazards shortest/history | Paired 95% CI exact-shortest | Exact McNemar p |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fork | 0.810 | 0.810 | 0.000 | 6 / 8 | 1 / 0 | [-0.844,-0.776] | 2.420369946780824e-122 |
| L-room | 0.756 | 0.756 | 0.000 | 8 / 8 | 1 / 0 | [-0.794,-0.718] | 3.248565551764031e-114 |
| Chamber/two-trigger | 0.890 | 0.890 | 0.000 | 7 / 9 | 2 / 0 | [-0.916,-0.862] | 2.2013136429275836e-134 |

These are real retained computational experiment results. They are not physical-robot measurements and are not safety guarantees.

### Frozen soft-vs-hard Pareto artifact

- workflow run: `34823943257`
- source SHA: `1bd538b831e741f869161828b2a3f63672ee124a`
- artifact: `10339560355`
- artifact digest: `sha256:864fe19cf7c02efd1f4c978fbe80dbbbdb546aa90f1f6488ef6327e7696401aa`

The downloaded raw artifact verifies the negative result: every hard-return threshold in `{0.5,0.7,0.8,0.9,0.95,0.99}` selects a zero-activated-hazard route with zero observed irreversible failure in all three frozen worlds. The soft objective requires weight >=2 in Fork and >=1 in L-room/Chamber to select the zero-hazard route. Therefore universal soft-objective superiority is falsified and must not be claimed.

## Reviewer-P0 retained artifact

A dedicated same-oracle / unavoidable-hazard audit has now completed successfully.

- workflow: `Reviewer P0 evidence`
- run: `36122469824`
- source branch head: `1246ce280bc92b3765f43915505e4dcdd4214830`
- PR merge checkout: `b6551e46245e8b33ac7772f27d36dafc091c2a85`
- artifact: `10857728526`
- downloaded artifact SHA-256: `e065873facb23770ad7f0d667a9b70638fa67f95f2163e5695af741c6d0d7175`

The exact state-only control uses the same exact connectivity oracle and additive fragility objective as the history-conditioned planner, while applying one fixed hazard field without trigger conditioning. It reproduces shortest-path choices and outcomes in all retained controlled, heterogeneous, geometric, and generated challenge scenarios.

The frozen unavoidable-hazard suite contains 24 generated scenarios, one to four route-choice modules per scenario, and 500 paired seeds per scenario. Every feasible start-to-goal path activates at least one hazard per module. Aggregate retained outcomes:

| Planner | Mean return-infeasibility | Mean exact return | Mean path length | Mean activated hazards |
|---|---:|---:|---:|---:|
| Shortest | 0.7796 | 0.2242 | 12.71 | 2.54 |
| State-only exact | 0.7796 | 0.2242 | 12.71 | 2.54 |
| History exact | 0.6926 | 0.3105 | 14.29 | 2.54 |

History exact changes the activated-hazard choice and improves exact final return probability in 8/24 scenarios, is nonworse in empirical return-infeasibility in 24/24, and has scenario-level mean risk difference `-0.087` versus state-only exact with 95% bootstrap interval `[-0.1629,-0.0247]`. This directly addresses the reviewer concern that the original effects could arise only from selecting trigger-free routes.

## Statistical audit

The publication-facing binary comparisons are paired by shared seed/scenario/event identity. `paired_binary_effect` computes proposed-minus-baseline risk difference, paired bootstrap intervals over pairwise differences, discordant-pair counts, and a two-sided exact McNemar conditional binomial p-value. State-only versus shortest correctly produces zero discordant pairs in the frozen history-trigger families.

Timing numbers are not promoted to population-level performance claims: the cut and augmented-state timing values above are representative retained CI-run measurements and are sensitive to runtime environment.

## Falsification boundary

The evidence stack must preserve the following controls/negative results: same-state/same-history agreement; directed-trigger reverse traversal non-activation; same-cell non-activation; sampling gaps not interpolated; unrealized events not injected; hard-safe-return equivalence; joint-cut optimism; and limitations from miscalibration, correlated closures, delayed revelation, kinodynamic mismatch, localization/discretization, and narrow necessary passages.

## Gazebo execution gate

The frozen action-triggered scenario remains:

- seed `20260914`;
- planners `NavFn`, `DynNavShortest`, `DynNavHistory`;
- trigger `(174,189) -> (175,189)`;
- closure cell `(181,191)`;
- closure probability `0.8`;
- recoverability weight `4.0`.

The implementation uses deterministic event draws keyed by `(seed, scenario, repetition, hazard_id)` and reuses the same latent draw across planners. Same-cell observations are ignored, adjacent observed transitions are accepted, and sampling gaps invalidate the observation stream rather than being interpolated. The runner injects the blocker only after the directed trigger is observed and the paired latent closure realizes.

A dedicated CI workflow, `.github/workflows/history-gazebo-evidence.yml`, has been added on this audit branch to execute the frozen `tb3_history_execution_benchmark.launch.py`, build/test ROS 2 Jazzy/Nav2 first, retain environment/configuration provenance, validate paired latent events, and upload raw results. This workflow is execution evidence only when a completed valid artifact exists; its presence alone is not efficacy evidence.

## Physical-robot gate

No physical robot is connected to the current execution environment. Therefore physical execution is not claimed and no synthetic/Gazebo value may be relabeled as physical evidence. Physical-robot efficacy and deployment safety remain `UNSUPPORTED` unless real supervised hardware trials are performed and retained.

## Final claim table

| Claim | Evidence | Raw artifact reproduced/inspected? | Statistics | Limitation | Status |
|---|---|---|---|---|---|
| History can contain recoverability information missing from state-only geometric representation | proposition + information-gap experiment | YES | constructive gap; 5 frozen cases | controlled mechanism | SUPPORTED |
| Exact history-aware planner is implemented | Python planner + tests | source audited | deterministic regression evidence | bounded hazard enumeration | SUPPORTED |
| History conditioning reduces irreversible failure in repeated-module family | 1000-seed homogeneous + 500-seed held-out | YES | paired risk differences, bootstrap, exact McNemar | synthetic procedural family | SUPPORTED |
| Result appears in three frozen geometric worlds | Fork/L-room/Chamber | YES | paired bootstrap + exact McNemar | only three hand-built worlds | SUPPORTED |
| Exact state-only fixed-field control isolates representation from estimator quality | retained Reviewer-P0 artifact | YES | exact equality with shortest in all retained benchmark families | fixed-field representation ablation only | SUPPORTED |
| Soft objective universally beats hard safe-return | Pareto sweep | YES | direct retained comparison | hard baseline matches safe routes | UNSUPPORTED / FALSIFIED |
| Critical-cut is exact generally | joint-cut counterexample | YES | 9/9 disagreement | joint cutsets | UNSUPPORTED / FALSIFIED |
| Critical-cut is faster in retained series-critical timing run | scaling artifact | YES | representative timing | environment-specific timing | PARTIALLY SUPPORTED |
| ROS 2/Nav2 history integration exists | C++ plugin + benchmark contracts | source/tests audited | integration tests | not efficacy | SUPPORTED |
| Action-triggered Gazebo efficacy | frozen execution workflow/protocol | ACTIVE: exact-head workflow running | paired analysis required | simulation only | PENDING GATE |
| Physical robot efficacy | none | NO | none | no connected hardware | UNSUPPORTED |

## Current decision

**CONDITIONAL GO FOR A SIMULATION-SCOPED SUBMISSION** once the final exact-head CI/paper build and release freeze are green.

The core representation paper is supported by traceable retained computational evidence, and the principal publication numbers listed above have now been checked against downloaded raw artifacts rather than trusted from documentation. The core representation claim now has retained same-oracle and unavoidable-hazard evidence. Remaining gates are: obtain and audit a valid completed action-triggered Gazebo artifact only if Gazebo efficacy is to appear in the paper; perform the final manuscript-number/citation consistency check; execute final exact-head CI and paper build; and freeze the release/tag. Physical-robot evidence is optional for a simulation-scoped paper but cannot be claimed without real hardware trials.


## Expanded measurement gate

A retained reviewer-measurement workflow now adds two measurements that were previously weak or single-shot:

- **96 frozen unavoidable-hazard scenarios**, 250 paired execution seeds per scenario (24,000 trials per planner). State-only exact return-infeasibility is 0.74425 and history exact is 0.66604. The scenario-level history-minus-state-only mean difference is -0.07821 with 95% bootstrap CI [-0.1090, -0.04983]. History exact improves 36/96 scenarios and is nonworse in 96/96.
- **Repeated timing distributions**, 100 measured repetitions after 10 warm-ups. On the retained GitHub Actions runner, the 12-hazard exact oracle has median 38.47 ms (IQR 0.181 ms, p95 38.75 ms) and critical-cut has median 0.192 ms (IQR 0.0064 ms, p95 0.204 ms), a median ratio of 200.7x. At six modules, median online planning latency is 0.114 ms for shortest augmented, 4.06 ms for history-cut, and 5.79 ms for history-exact.

The timing distributions are descriptive for the retained runner environment and must not be presented as hardware-independent real-time guarantees. The 96-scenario family remains a structured synthetic generator and does not establish arbitrary-map or deployment generalization.
