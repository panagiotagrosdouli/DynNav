# DynNav Submission-Readiness Audit

This document is the publication gate for the current DynNav paper. It distinguishes evidence that is already traceable from evidence that still requires execution or independent reproduction. It must not be used to promote a claim beyond the evidence level defined in `CLAIM_EVIDENCE_MATRIX.md` and `EXPERIMENT_PROTOCOL_V3.md`.

## Central claim

The submission-facing claim is deliberately narrow:

> When executed robot actions can activate future topology hazards, activated-hazard history can contain safe-return-connectivity information that a state-only marginal environmental-risk representation cannot, in general, represent from geometric state alone.

This is a representation/mechanism claim. It is not a claim of universal planner superiority, certified safety, arbitrary-map generalization, calibrated real-world hazard probabilities, or physical-robot efficacy.

## Evidence audit

| Claim | Experiment / implementation | Retained provenance | Statistical / logical validation | Limitation | Submission status |
|---|---|---|---|---|---|
| Same geometric endpoint can have different return reliability under different activated histories | `history_information_gap_benchmark.py` and Proposition 1 | values recorded in `evidence_manifest.json` | constructive proof; maximum retained separation 0.9 | controlled construction | SUPPORTED |
| A deterministic state-only marginal representation cannot represent both same-endpoint histories exactly | information-gap construction | manifest + paper proposition | representational argument; same state maps to one state-only value | applies to stated state-only semantics | SUPPORTED |
| Exact augmented-state history-aware planner is implemented | `commitment_aware_astar.py` | source + regression tests | augmented `(cell, activated hazards)` state | exact oracle scales with active hazard count | SUPPORTED |
| History conditioning changes irreversible-failure outcomes in the repeated-module family | homogeneous stochastic execution | manifest records 1000 paired seeds per probability | paired CRN; retained rates include 0.992 shortest/state-only vs 0.000 history-exact at p=0.8 | constructed repeated-module family | SUPPORTED |
| Result transfers to frozen 6/7/8-module probability/horizon settings | held-out history generalization | manifest records 500 paired seeds/scenario | retained rates 0.992, 0.998, 1.000 vs 0.000 | same procedural topology family | SUPPORTED |
| Result replicates in three frozen hand-built geometric worlds | `geometric_heldout_benchmark.py` | workflow run 34823759539; artifact 10339442639; digest recorded in manifest | 500 paired seeds/scenario; paired bootstrap and exact McNemar implemented | three synthetic topologies only | SUPPORTED |
| Soft history objective universally dominates hard safe-return constraints | geometric Pareto sweep | retained workflow/artifact in manifest | falsified: every tested hard threshold selects a zero-hazard route in the three worlds | objective depends on operating regime | UNSUPPORTED / MUST NOT CLAIM |
| Critical-cut approximation can reduce exact-oracle cost in the series-critical construction | cut scaling benchmark | representative timing recorded in manifest | exact/cut comparison | timing is a representative retained CI run, not a universal speed claim | SUPPORTED WITH SCOPE |
| Critical-cut approximation is generally exact | joint-cut adversarial benchmark | 9/9 disagreement settings in manifest | explicit parallel joint-cut counterexample | multi-cell cuts violate the single-critical assumption | UNSUPPORTED / FALSIFIED |
| C++ history-conditioned planner integrates with ROS 2 Jazzy/Nav2 | `ros2_ws/src/dynnav_nav2_cpp` | build/discovery/regression evidence | persistent history updated from executed-transition input | integration is not execution efficacy | SUPPORTED |
| Planned paths do not mutate persistent hazard history | Python/ROS semantics and tests | source + protocol | activation is tied to executed transitions | execution observation must still satisfy protocol | SUPPORTED |
| Action-triggered Gazebo protocol is frozen | benchmark config + `ACTION_TRIGGER_PROTOCOL.md` + V3 protocol | trigger `(174,189)->(175,189)`, closure `(181,191)`, p=0.8 | predeclared validity and pairing rules | no comparative retained efficacy artifact yet | SUPPORTED AS PROTOCOL |
| History-aware planner improves action-triggered Gazebo execution outcomes | pending paired execution study | none currently authorized by manifest | not yet available | must satisfy trigger, blocker, costmap, recovery and validity contracts | UNSUPPORTED / SUBMISSION GATE |
| Physical-robot/deployment safety | none | none | none | outside current evidence | UNSUPPORTED / MUST NOT CLAIM |

## Numerical provenance checks completed

The publication-facing geometric evidence is not merely a README transcription. The repository contains a successful GitHub Actions run (`34823759539`) at SHA `8552a42466b598fcf12c9e20137eb4166b866cbd`, and its retained artifact (`10339442639`) is still available with digest `sha256:d8b59cfd6432d8ade1351b882cc29c6371e3437504346322817d41bb4b608e93`. The workflow explicitly executes the frozen benchmark with 500 seeds and recoverability weight 8.0 before uploading `results/geometric_heldout`.

The benchmark source fixes the three maps and probabilities before execution and computes paired binary effects against shortest using common seed identities. `dynnav/experiments/statistics.py` computes proposed-minus-baseline paired risk differences, paired bootstrap intervals, and a two-sided exact McNemar p-value from discordant pairs.

The following manifest values are therefore traceable to a retained workflow/artifact contract, but should still be regenerated in the final clean-room reproduction before release:

- Fork: shortest/state-only failure 0.810; history-exact 0.000; 500 paired seeds.
- L-room: shortest/state-only failure 0.756; history-exact 0.000; 500 paired seeds.
- Chamber/two-trigger: shortest/state-only failure 0.890; history-exact 0.000; 500 paired seeds.
- Held-out modules: 0.992, 0.998, and 1.000 shortest/state-only failure versus 0.000 history-exact for 6, 7, and 8 modules respectively, with 500 paired seeds per scenario.
- Homogeneous p=0.8: 0.992 shortest/state-only failure versus 0.000 history-exact, with 1000 paired seeds per probability.
- Joint-cut counterexample: approximation optimism in all 9 frozen settings; exact return values on the cut-selected route follow `1-p^2` for the retained p values.

These values are retained experimental/model results under the declared synthetic protocols. They are not real-world probabilities or safety guarantees.

## Statistical audit

The current publication protocol correctly requires pairing whenever planners share scenario/seed/event identity. Binary comparisons must retain protocol-valid failures in the denominator, report paired risk differences, and may use exact McNemar tests plus paired bootstrap intervals. The geometric benchmark implements this pairing by seed and calls `paired_binary_effect` rather than treating planner rows as independent samples.

Before submission, the final clean-room run must regenerate all reported intervals and p-values from raw per-trial artifacts and compare them mechanically against the manifest. Any mismatch is a release blocker until explained and recorded.

## Falsification requirements

The following negative/boundary results are part of the paper, not optional cleanup:

- same-state/same-history must produce agreement;
- reverse trigger traversal must not activate a directed trigger;
- planned-only paths must not activate persistent history;
- sampling gaps must remain unknown/invalid rather than be interpolated;
- unrealized latent events must not create closures;
- hard safe-return equivalence must remain visible;
- critical-cut joint-failure optimism must remain visible;
- probability miscalibration, correlated closures, delayed revelation, kinodynamic mismatch, localization/discretization sensitivity and narrow necessary passages remain limitations unless separately validated.

## Gazebo submission gate

Do not add a Gazebo efficacy number to the abstract, results, conclusion, README evidence table, or manifest until a retained paired artifact satisfies all V3 validity conditions.

The frozen first scenario is:

- trigger: `(174,189) -> (175,189)`;
- closure cell: `(181,191)`;
- activation-conditioned closure probability: `0.8`;
- planners: `NavFn`, `DynNavShortest`, `DynNavHistory`.

For each `(scenario, repetition, hazard_id)`, the latent event draw must be deterministic and reused across planners. Physical closure is injected only if that planner executes the trigger and the paired event realizes. Planned geometry never activates the event.

A trial enters efficacy analysis only if lifecycle, reset/start tolerance, executed-transition observation, required blocker injection, costmap observation, and post-event recovery assessment are valid. Invalid trials are reported separately with reasons.

Required retained output: raw per-trial CSV/JSON, seed/event identity, planner identity/parameters, trigger trace, blocker injection status, costmap observation, mission outcome, independent recovery label, validity/exclusion reason, Git SHA/dirty state, environment versions, summary statistics, and logs/rosbag metadata where feasible.

If the paired Gazebo result is neutral or negative, retain it and narrow the paper. Do not tune the frozen geometry/probability after seeing comparative outcomes without a new protocol version.

## Reproducibility gate

Before tagging a submission release, execute from a clean checkout/environment:

1. install the declared Python package/extras;
2. run Ruff;
3. run the full pytest suite;
4. rerun every publication-facing Python benchmark with frozen parameters/seeds;
5. regenerate machine-readable summaries and compare all manuscript numbers against them;
6. build and test the ROS 2 Jazzy/Nav2 packages;
7. verify plugin discovery and executed-history regression tests;
8. execute the frozen Gazebo study if execution efficacy is to be claimed;
9. build the IEEE manuscript from source;
10. verify bibliography, figures, tables, manifest provenance and claim matrix against the final paper commit.

Any manual dependency or unreproducible step must be documented rather than silently assumed.

## Paper structure gate

The final manuscript should preserve this argument order:

Problem -> state-only information loss -> proposition/construction -> augmented state -> exact recoverability -> planning methods/baselines -> controlled evidence -> held-out evidence -> objective/approximation falsification -> ROS/Nav2 integration -> Gazebo evidence only if valid -> limitations -> conclusion.

The abstract and conclusion must not outrun the claim matrix.

## Current go/no-go decision

**NO-GO for final submission package today.**

The central representation claim and the main synthetic/geometric evidence are sufficiently defined to support a paper. The remaining high-priority gate is execution-level Gazebo evidence if the manuscript intends to claim execution efficacy. Independently of whether Gazebo efficacy is ultimately included, a final clean-room numerical reproduction and manuscript/manifest consistency pass are required before tagging the submission version.

A valid path to GO is:

`clean-room reproduction -> resolve every numerical discrepancy -> valid paired Gazebo artifact (or explicitly omit efficacy claim) -> final paper rewrite/audit -> paper build -> frozen manifest/claim matrix -> submission tag/release`.
