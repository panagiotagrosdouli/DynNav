# DynNav engineering and scientific checkpoint — 2026-11-12

## Decision and exact revisions

**PARTIALLY COMPLETE. This is an integration checkpoint, not acceptance of the full mission.**

- Inspected main: `1a0075452b2786e047f0b1f2d1962e7badbd977b` (confirmed against GitHub main).
- Code repair head: `43669a23c3395a21f3c49306184d4c5ea578f824`.
- Earlier web/ROS/paper execution head: `7579335d874f7523b6ebe1f327ed95369d39ad0f`.
- Branch: `integration/research-audit-2026-11-12`.
- Draft PR: https://github.com/panagiotagrosdouli/DynNav/pull/240 . No merge, release tag, publication submission, or production promotion was performed.
- Evidence files are new outputs; historical retained results and the paper evidence manifest were not overwritten.

Checkpoint finalized 2026-11-13. Evidence folders retain their execution date, 2026-11-12.

## Repairs implemented

1. Regenerated the 26-entry website catalog. Sixteen contribution entries had stale test-directory links. The generator now uses Git-tracked file presence rather than ignored/untracked files, and CI watches the contribution and renderer trees. Two regression tests cover committed-catalog consistency and untracked-directory contamination.
2. Static ROS/Gazebo CI now fails on partial APT index updates, uses bounded APT acquisition retries/timeouts, conditionally initializes rosdep without suppressing initialization errors, and uploads OS/repository/Nav2-candidate/rosdep diagnostics. This is infrastructure hardening, not a demonstrated diagnosis of the original APT failure.
3. Moved five dependency elements inside the historical TurtleBot3 bringup package's XML root. Its former document was malformed. This is format repair only; the legacy `gazebo_ros` dependency and launch compatibility still require runtime review before calling this a Jazzy SLAM implementation.
4. Repaired standalone/package imports in historical learned-uncertainty A*, training and evaluation. An unrelated local import error previously masqueraded as missing PyTorch and set `torch=None`. Installing CPU PyTorch exposed 13 failures; all 41 affected tests now pass. Added optional CPU learning CI.
5. Added a repository-wide format/hash inventory tool. It explicitly labels unvalidated formats and never equates parsing with semantic review.

6. Added prior executed-hazard inputs to the Python critical-cut and hard safe-return baselines. Previously both always initialized empty history on replanning. Six new regressions verify retained bridge risk, hard-threshold rejection and invalid hazard IDs. Existing default behavior is preserved; affected experiments and timing distributions were rerun separately in `final_reproduction/` and `final_timings/`. These remain new runner-specific measurements, not a replacement publication timing freeze.

## Inventory and architecture

`file_inventory.json` records 2,245 tracked paths at the code repair head, with SHA-256, byte counts, check names, errors and semantic-review status per file. Of these, 1,482 passed a format check and 763 received hashes only / remain format-unvalidated. The initial scan found one malformed XML file; the repaired scan has no format failures. **This does not mean every file was semantically reviewed.** The inventory covers code, tracked data and retained artifacts at the source revision; this checkpoint's newly added evidence is separately hashed in `artifact_index.json`.

`dependency_graph.json` records the tracked directory tree and approximate local Python import edges. Dynamic imports, JS/TS imports, ROS dependency resolution, CMake semantics, runtime calls and deployment topology are not certified by that graph.

Canonical paths remain `dynnav/`, `ros2_ws/src/dynnav_nav2_cpp`, `ros2_ws/src/dynnav_nav2_benchmark`, `paper/dynnav_r`, and their frozen protocols. Streamlit `app/` and `src/dynnav_dashboard`, FastAPI `apps/api`/`dynnav/researcher`, static researcher UI `apps/web`, public `website`, and standalone `vercel_app` remain preserved. Historical `contributions/learned_uncertainty_astar`, older ROS workspaces, broad experiments and prototypes were preserved. No module was deleted as supposedly redundant.

Python AST, JSON, YAML, TOML, XML/SDF/URDF/Xacro/SVG, image decoding, ZIP CRC and shell syntax checks were applied by supported file type. TS/JS were checked through three production builds. C++ was built/tested in ROS CI. SQL, other C/C++ trees, Dockerfiles, every binary/PDF, every LaTeX source and all configuration semantics have **not** received a complete dedicated audit.

## Test matrix and evidence levels

| Component | Result in this audit | Evidence boundary |
|---|---|---|
| Canonical install | editable install with dev/researcher/dashboard extras passed | host Python 3.12, not a full clean supported-OS matrix |
| Initial canonical pytest | 695 passed, 33 skipped | optional neural paths not exercised |
| PyTorch-enabled suite before repair | 13 failed, 717 passed | retained failure XML; failure was not suppressed |
| Repaired canonical pytest | 736 passed, zero skips | unit and ROS-independent integration contracts |
| Contribution tests with CPU PyTorch | 241 passed, zero skips | controlled implementation tests |
| C01–C26 experiments | 26 executed successfully (C01 separately after installing torch) | synthetic smoke contracts, not efficacy/generalization |
| Ruff | passed on canonical package/benchmark and new audit/catalog scripts | existing historical code not fully lint-clean certified |
| Mapping mypy | passed strict checks | mapping core only |
| Website / researcher workspace / standalone app | production builds passed; standalone typecheck passed | local build evidence |
| Browser -> local API -> planner artifacts -> UI | passed, four executions, no page errors | actual local synthetic experiment, no ROS execution |
| Streamlit | startup health endpoint returned `ok`; existing smoke tests passed in canonical suite | not all pages/interactions browser-tested |
| Paper checker | 22 unique citation keys and abstract/manifest checks passed | no independent verification of all bibliography metadata |
| Paper compile | GitHub workflow passed at 7579335d | artifact metadata retained; PDF bytes inaccessible here |
| Static Jazzy/Gazebo | build, colcon tests, planner-server benchmark and schema checks passed in GitHub run | simulation planner-server integration, not hardware or comparative navigation efficacy |
| Live SLAM/AMCL/localization errors | BLOCKED / NOT VERIFIED | no newly observed SLAM map or ground-truth localization-error experiment |
| Physical robot / production | NOT VERIFIED | no physical robot execution or verified deployed API |

Actual JUnit files retain failures and successful reruns. `python-freeze.txt` records the local installed dependency versions. One Starlette/httpx deprecation warning remains. Local host: Debian 13, Python 3.12.14, Node 24.22.1, CPU PyTorch 2.15.0+cpu. These differ from the target Ubuntu 24.04/Jazzy stack; ROS CI uses that supported container/runner. A local ROS image pulled successfully, but container creation exhausted the 7.9 GB filesystem under Docker's storage driver. Only the downloaded audit image was removed to recover space; local ROS build/simulation was not claimed.

## Scientific reproduction

The 96-scenario unavoidable-hazard generator was actually rerun with 250 paired seeds per scenario (24,000 trials/planner; four planner conditions). Its raw trials and summary are retained in `unavoidable_96/`. `publication-comparison.json` verifies agreement with the pinned manifest for both principal rates, scenario effect and paired bootstrap interval:

- state-only exact mean return-infeasibility: 0.74425;
- history exact: 0.6660416666666666;
- history minus state-only exact scenario mean difference: -0.07820833333333332;
- scenario bootstrap 95% interval: [-0.109, -0.04983333333333333];
- improved 36/96 scenarios; nonworse 96/96.

These are synthetic computational measurements, not physical-world rates or safety guarantees. The original paired binary analyses, exact McNemar tests and scenario bootstrap implementation were exercised by the suite. This checkpoint does not replace them with independent-observation tests or change metrics after outcomes.

Fresh raw outputs under `reproduced/` include same-state/different-history information gap, analytic phase boundary, stochastic commitment execution, exact-versus-cut scaling, 6/7/8-module held-out probability/horizon scenarios, joint-cut counterexample, three frozen geometric worlds (500 paired seeds), and soft-versus-hard safe-return Pareto experiments. The endpoint-only p/2 bound is mathematical, with existing executable coverage; no new theorem is claimed. In addition to the 96-scenario comparison, `expanded-publication-comparison.json` records 85 passing non-timing comparisons covering information gap, phase boundary, homogeneous/held-out/geometric rates, paired intervals, exact McNemar values, series cut error, joint-cut counterexamples and the hard-return negative result. `compare_publication.py` retains the comparison code. This is not every manuscript claim or a bibliography audit.

`repeated_timings/` contains 100 measured repetitions after 10 warm-ups. These timings differ from the pinned paper artifact, as expected on a different and concurrently loaded CPU. The manuscript timing freeze was not overwritten. Do not interpret the new ratio as a hardware-independent speed guarantee or statistically controlled performance improvement.

Core semantic review confirms the declared independent distinct-cell Bernoulli model, shared event semantics for multiple triggers at a cell, current-cell usability conditioning, exact enumeration's exponential cost, augmented-state search, and cut upper-bound/joint-cut failure rationale. Tests cover planned-versus-executed history separation. The code's admissible unit-weight Manhattan heuristic claim applies to its nonnegative additive objective; heuristic weights above one do not inherit that claim. This review is not a proof of every algorithm or a validation of correlated/partially observed closure models.

## C01–C26 implementation/evidence matrix

The registry's maturity labels are retained. TESTED below means the registered synthetic experiment ran; it does not mean every planned research feature exists or is scientifically validated. `contribution_matrix.json` records exact artifact hashes and per-track claim boundaries.

| ID | Track | Registered maturity | Current audit evidence |
|---|---|---|---|
| C01 | Learned A* Search | Research Prototype | TESTED: synthetic registered experiment |
| C02 | Uncertainty Calibration | Research Prototype | TESTED: synthetic registered experiment |
| C03 | Belief and Risk Planning | Research Prototype | TESTED: synthetic registered experiment |
| C04 | Irreversibility and Returnability | Research Prototype | TESTED: synthetic registered experiment |
| C05 | Safe-Mode Navigation | Research Prototype | TESTED: synthetic registered experiment |
| C06 | Energy and Connectivity | Research Prototype | TESTED: synthetic registered experiment |
| C07 | Next-Best View | Research Prototype | TESTED: synthetic registered experiment |
| C08 | Security IDS | Experimental | TESTED: synthetic registered experiment |
| C09 | Multi-Robot Navigation | Experimental | TESTED: synthetic registered experiment |
| C10 | Human, Language, and Ethics | Experimental | TESTED: synthetic registered experiment |
| C11 | VLM Navigation Agent | Experimental | TESTED: synthetic registered experiment |
| C12 | Diffusion Occupancy | Experimental | TESTED: synthetic registered experiment |
| C13 | Latent World Model | Experimental | TESTED: synthetic registered experiment |
| C14 | Causal Risk Attribution | Experimental | TESTED: synthetic registered experiment |
| C15 | Neuromorphic Sensing | Experimental | TESTED: synthetic registered experiment |
| C16 | Federated Navigation Learning | Experimental | TESTED: synthetic registered experiment |
| C17 | Topological Semantic Maps | Experimental | TESTED: synthetic registered experiment |
| C18 | Formal Safety Shields | Experimental | TESTED: synthetic registered experiment |
| C19 | LLM Mission Planner | Documentation Concept | TESTED: synthetic registered experiment |
| C20 | Multimodal Failure Explainer | Experimental | TESTED: synthetic registered experiment |
| C21 | PPO Navigation Agent | Experimental | TESTED: synthetic registered experiment |
| C22 | Curriculum RL | Experimental | TESTED: synthetic registered experiment |
| C23 | Gaussian Splatting Mapper | Documentation Concept | TESTED: synthetic registered experiment |
| C24 | NeRF Uncertainty | Documentation Concept | TESTED: synthetic registered experiment |
| C25 | Adversarial Attack Simulator | Experimental | TESTED: synthetic registered experiment |
| C26 | Swarm Consensus | Experimental | TESTED: synthetic registered experiment |

C01's 75-file audit includes 13 structurally checked checkpoints. C02–C26's 537-file integrity audit includes three C02 tensor/metadata checks. Structural checkpoint validation is not provenance verification, reproduced training, independent held-out performance or closed-loop ROS validation. C01's optional experiment was rerun after dependency installation; its initial skip remains in the first manifest.

The following limitations remain mandatory: C11's mock/provider-contract evidence does not establish a trained live VLM; C15's smoke run does not demonstrate an event-camera advantage; C16's pseudo-client evidence is not a real federated fleet; C17 placeholder semantics are not validated language embeddings. Newer C17/C16 main-branch enhancements exist but were not independently reproduced here. C21/C22 weak or negative learned-policy findings remain and are not promoted by a passing experiment contract. C19/C23/C24 retain concept-level registry maturity despite executable toy experiments. No new full-scale neural training/generalization programme was completed.

## Recorded dataset provenance

Downloaded `dynamics_0` poses again from the official University of Bonn LILocBench source. SHA-256: `606f9392c1a992c9acdb5e680a9108ef7647ba8943d747435c90dfa56feaa38f`. The official source page confirms global-frame ground truth from ceiling AprilTags and CC BY-NC-SA 4.0 distribution. See `dataset_provenance.json` for source/license URLs and page checksum, and `lilocbench-summary.json` for exact derived metrics.

Actual rerun: 3,194 poses, 159.951338768 s duration, 53.966714850 m XY path, 0.337394581 m/s mean XY speed; sample intervals range about 0.05–0.15 s. Parser enforces increasing finite timestamps/positions and eight columns. It does not independently validate quaternion orientation, all frame transforms, absolute time conventions or units beyond the published dataset conventions. This is descriptive recorded-data analysis without training/test separation because no model was fit. No navigation improvement, localization accuracy, genuine sensor attack, online SLAM or hardware efficacy follows from these statistics. Raw poses are excluded from committed evidence; obtain them from the official source and respect the license/citation. Other bags/maps/Dingo studies and data splits still need independent full provenance/evaluation audit.

## Web, deployment and security

Website, researcher workspace and standalone app build. The actual Playwright interaction compiled a one-seed/four-planner protocol, created and ran the experiment through FastAPI, polled completion and displayed `Executed evidence`. `browser-results.json` records HTTP responses and zero page errors; `workspace-executed.png` is a screenshot of that executed local flow. The API contract test also verifies artifacts/report downloads. Local Streamlit health passed. Browser animation or grid execution remains separate from ROS/Gazebo.

Many workspace navigation/session controls remain placeholders; not every advertised module has a functional route. The default researcher browser API URL is loopback, so a public static deployment alone does not provide a remote research service. Complete public hosting topology, authenticated/resource-bounded API access, all route/error/accessibility cases and supported Streamlit interactions remain open. No unrelated account or project was deployed.

Production npm dependency audits for all three apps returned zero known vulnerabilities at execution time. This is neither a complete security review nor an audit of Python, containers, developer dependencies or runtime exposure. GitHub reported two moderate default-branch Dependabot advisories during push; their exact scope has not been reconciled with these npm results. The connected Vercel PR check reports **deployment rate limited, retry in 24 hours**. No preview deployment success or production readiness is claimed. GitHub Pages deployment was skipped by the manual gate.

## CI findings, access limits and remaining acceptance gates

The two original failed jobs at inspected main are confirmed through GitHub's jobs API: web run 42802575680 failed catalog verification; ROS run 42802560005 failed dependency installation before any build. Historical log and new artifact download redirects to GitHub's storage endpoint returned Forbidden in this environment. Therefore the precise original APT transport/package/version error is **UNRESOLVED**, not a planner defect. The repaired static workflow passed, but a single pass does not establish that transient infrastructure failures are eliminated. New setup diagnostics and APT candidate records are retained by GitHub for future diagnosis.

Run metadata and published artifact digests are retained, but inaccessible archive bytes were not inspected or relabeled locally generated. `ci_runs.json` records the latest observed conclusions and exact head revisions; use those revisions rather than assuming every workflow used the final evidence-only commit. A successful paper workflow proves compilation/checks ran, not publication acceptance or independently verified literature.

Remaining mission gates: full semantic review of every module and workflow; complete all 26 tracks beyond smoke contracts; reproduce all training and checkpoint/dataset provenance; independent statistical/baseline/ablation review; all-publication-number and bibliography metadata audit; genuine live SLAM map/AMCL/TF/LaserScan/odometry validation; localization errors; all frozen Gazebo scenarios and delayed-observation/dropout/controller/miscalibration stress tests; raw simulation artifact inspection; all browser routes and authenticated production API integration; resolve Vercel preview limit; full final-head CI/paper freeze; physical robot evidence if any such claim is desired. No acceptance checklist is marked fully complete.

## Additional static review and CI checkpoint

At code head `43669a23c3395a21f3c49306184d4c5ea578f824`, CI, web portal, documentation integrity, optional CPU learning, C01–C26 experiments and hazard-aware planner pilot all completed successfully. The action-triggered Gazebo run 43300981893 also completed successfully at earlier head 7579335d. Its workflow trial-validity assertions passed; raw archives remain inaccessible here, so trial metrics and comparative effects are not independently inspected or claimed. Artifact metadata is retained in `history-artifact-metadata.json`. Vercel preview remains separate from successful GitHub workflows.

Public website browser checks loaded the home page and all 26 contribution HTML routes with HTTP 200 and no page errors. At 390px width no horizontal overflow was observed, and initial Tab focus reached an anchor. This is a bounded check, not comprehensive accessibility certification.

`ros_slam_review.json` preserves targeted static findings: missing historical SLAM runtime dependencies; ambiguous combined SLAM/localization launch selection; Gazebo Classic dependencies under a Jazzy/Harmonic target; unchecked trailing text/narrowing in C++ cell parsing; potential geometry/costmap-copy resize inconsistency; and execution messages without freshness/frame/observation-quality metadata. These findings are not repaired or runtime-confirmed by this checkpoint.

Partial C11–C26 source review additionally identified: C11 resize/depth pixel-coordinate mismatch and approximate camera intrinsics; C12 public score model ignores conditioning and remains a random stub; C15 unseeded per-frame timestamp jitter; C16 privacy noise without a complete privacy accountant/sensitivity definition; C18 duplicated monitor updates in an evaluator branch; C20 synthetic/hardcoded cause attribution; C21 update routine without policy parameter learning; and C22 random-action curriculum training. These are static review observations requiring dedicated repair and tests. The source review agents hit a usage limit before completing their reports; a full per-file semantic review was not delivered. C21 actual PPO learning and C22 learned curriculum execution must therefore remain NOT IMPLEMENTED in those inspected paths despite smoke passage. Do not treat C20 output as measured episode causality or C16 noise as certified differential privacy.

## Reproduction and continuation

Run from repository root on the named integration branch. Keep reruns in a new output directory so retained evidence is preserved:

```bash
python -m venv .venv
.venv/bin/pip install -e '.[dev,researcher,dashboard]'
.venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest -q contributions
.venv/bin/python scripts/sync_website_contribution_catalog.py --check
.venv/bin/python scripts/audit_tracked_files.py --output work/rerun/inventory.json
.venv/bin/python scripts/audit_repository_dependencies.py --output work/rerun/dependencies.json
.venv/bin/python scripts/run_contribution_suite.py --fail-on-skip --output-dir work/rerun/contributions
.venv/bin/python -m dynnav.experiments.unavoidable_history_benchmark --output-dir work/rerun/unavoidable_96 --scenario-count 96 --seeds 250
.venv/bin/python -m dynnav.experiments.repeated_timing_benchmark --output-dir work/rerun/timings --repetitions 100 --warmups 10
.venv/bin/python scripts/run_history_information_gap_benchmark.py --out-dir work/rerun/gap
.venv/bin/python scripts/run_commitment_phase_benchmark.py --out-dir work/rerun/phase
.venv/bin/python scripts/run_commitment_execution_benchmark.py --out-dir work/rerun/execution
.venv/bin/python scripts/run_cut_scaling_benchmark.py --out-dir work/rerun/scaling
.venv/bin/python scripts/run_heldout_history_generalization.py --out-dir work/rerun/heldout
.venv/bin/python scripts/run_joint_cut_counterexample.py --out-dir work/rerun/joint_cut
.venv/bin/python scripts/run_geometric_heldout_benchmark.py --seeds 500 --output-dir work/rerun/geometric
.venv/bin/python scripts/run_geometric_pareto_benchmark.py --output-dir work/rerun/pareto
.venv/bin/python paper/dynnav_r/check_submission.py
npm --cache "$PWD/work/npm-cache" --prefix website ci --no-audit --no-fund
npm --prefix website run build
npm --cache "$PWD/work/npm-cache" --prefix apps/web ci --no-audit --no-fund
npm --prefix apps/web run build
npm --cache "$PWD/work/npm-cache" --prefix vercel_app ci --no-audit --no-fund
npm --prefix vercel_app run typecheck
npm --prefix vercel_app run build
```

For ROS/Gazebo reproduce the exact commands in `.github/workflows/ros2-simulation.yml` and `.github/workflows/history-gazebo-evidence.yml` on Ubuntu 24.04/Jazzy with sufficient disk. For the dataset, download the official source URL in `dataset_provenance.json`, verify the checksum and run `scripts/analyze_lilocbench_ground_truth.py INPUT --output work/rerun/lilocbench.json`. For browser reproduction install Playwright/Chromium into a writable project cache, run `uvicorn apps.api.main:app` on port 8000, serve `apps/web/out` on port 3000, then enter a one-seed comparison, compile and run four planners. These are synthetic research runs.

Continue by inspecting retained GitHub artifacts when storage access is available, completing remaining simulation/SLAM and source reviews, and updating this checkpoint with actual evidence. Do not copy previous results into rerun directories or promote smoke passage into scientific efficacy.
