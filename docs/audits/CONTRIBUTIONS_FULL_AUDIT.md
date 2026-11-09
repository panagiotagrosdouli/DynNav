# DynNav Contributions Full Audit

**Repository base:** `b626d6e9b5bf8b8cf1ec87906597d767224f5f37` (main base); audit code commit: `dd80146672d7330a57bfabbf51ea8e25caff12b1` (main HEAD, 2026-11-09). **Audit branch:** `audit/contributions-complete-2026-11-09`.

## Repository state verified

- Main HEAD is merge commit `b626d6e9b5bf8b8cf1ec87906597d767224f5f37` (main base); audit code commit: `dd80146672d7330a57bfabbf51ea8e25caff12b1`, merging PR #210 (`c150df741a2fd08a14e77da89fb45cf3388d45a5`) at 2026-11-09 13:27:15 UTC.
- PR #210 is closed and merged. It adds real LILocBench `dynamics_0` descriptive analysis and map/trajectory evidence tools.
- At inspection, 12 PRs were open. Relevant open research PRs include #205, #195, #194, #193, #189, #187; ROS/Gazebo runner fixes #180, #177 and #176 remain open. They are not silently treated as merged work.
- Current main CI runs associated with the merge were green for CI, documentation integrity, C01-C26 suite, web portal, Streamlit dashboard, Pages, and Vercel status. Local canonical execution differs: one optional skip and an initial C11 failure were reproduced, repaired, and rerun.
- Registry contains exactly 26 canonical entries C01-C26 and exactly 26 matching experiments. C00 is the core programme; the two C07 folders are one contribution; support folders are not numbered contributions. C27 is an independent theory proposal with one finite counterexample runner added in this audit; it is not registered.

## Evidence boundary

The default registry suite is explicitly a synthetic/controlled smoke suite. “Passed” means the command returned success and emitted a nonempty artifact. It does not establish real data performance, trained-model validity, ROS 2/Gazebo execution, physical-robot behavior, or formal safety.

## Contribution-to-evidence matrix

| ID | Canonical implementation | Experiment result | Evidence actually present | Key limitation |
|---|---|---|---|---|
| C01 | `contributions/01_learned_astar` | **skipped_optional_dependency** | No CSV (dependency skip); `synthetic` | Requires the repository's local trained checkpoint and PyTorch; synthetic grids do not establish transfer to Nav2 or a physical robot. |
| C02 | `contributions/02_uncertainty_calibration` | **passed** | CSV rows: 3; `synthetic` | The default generator is synthetic and cannot establish calibration under sensor drift or domain shift. |
| C03 | `contributions/03_belief_risk_planning` | **passed** | CSV rows: 9; `synthetic` | Route candidates and beliefs are controlled fixtures rather than live occupancy estimates. |
| C04 | `contributions/04_irreversibility_returnability` | **passed** | CSV rows: 4; `synthetic` | Recoverability is evaluated on discrete graph fixtures and is not yet a calibrated real-world failure probability. |
| C05 | `contributions/05_safe_mode_navigation` | **passed** | CSV rows: 12; `synthetic` | Controller outputs are policy decisions on scripted traces, not closed-loop velocity validation. |
| C06 | `contributions/06_energy_connectivity` | **passed** | CSV rows: 5; `synthetic` | Energy and radio models are analytical proxies without hardware characterization. |
| C07 | `contributions/07_next_best_view` | **passed** | CSV rows: 5; `synthetic` | Candidate views are hand-authored fixtures rather than sensor-derived frontiers. |
| C08 | `contributions/08_security_ids` | **passed** | CSV rows: 5; `synthetic` | Synthetic detector scores do not demonstrate detection performance against real ROS 2 attacks. |
| C09 | `contributions/09_multi_robot` | **passed** | CSV rows: 4; `synthetic` | The benchmark audits predefined plans and does not exercise distributed ROS 2 communication. |
| C10 | `contributions/10_human_language_ethics` | **passed** | CSV rows: 9; `synthetic` | Policy fixtures do not constitute human-subject validation or normative proof. |
| C11 | `contributions/11_vlm_navigation_agent` | **passed** | CSV rows: 6; `synthetic` | This validates structured outputs only; it does not call or benchmark a real vision-language model. |
| C12 | `contributions/12_diffusion_occupancy` | **passed** | CSV rows: 8; `synthetic` | The lightweight predictor is a controlled proxy and not evidence for a trained diffusion model. |
| C13 | `contributions/13_latent_world_model` | **passed** | CSV rows: 5; `synthetic` | The latent dynamics are untrained fixtures and cannot support world-model accuracy claims. |
| C14 | `contributions/14_causal_risk_attribution` | **passed** | CSV rows: 5; `synthetic` | Correctness is relative to a hand-specified structural causal model. |
| C15 | `contributions/15_neuromorphic_sensing` | **passed** | CSV rows: 6; `synthetic` | Simulated events and Python timing do not establish hardware event-camera latency. |
| C16 | `contributions/16_federated_nav_learning` | **passed** | CSV rows: 4; `synthetic` | Synthetic client objectives do not establish performance on heterogeneous robot datasets. |
| C17 | `contributions/17_topological_semantic_maps` | **passed** | CSV rows: 8; `synthetic` | Hash-based label embeddings are deterministic stubs, not open-vocabulary perception evidence. |
| C18 | `contributions/18_formal_safety_shields` | **passed** | CSV rows: 6; `synthetic` | Numerical stress tests are not a formal proof and do not cover full robot dynamics. |
| C19 | `contributions/19_llm_mission_planner` | **passed** | CSV rows: 5; `synthetic` | The benchmark uses deterministic fixtures and does not establish LLM reliability. |
| C20 | `contributions/20_multimodal_failure_explainer` | **passed** | CSV rows: 3; `synthetic` | Automated rubric scores are not a substitute for blinded operator studies. |
| C21 | `contributions/21_ppo_navigation_agent` | **passed** | CSV rows: 3; `synthetic` | The policies and environment are lightweight fixtures, not trained PPO deployment evidence. |
| C22 | `contributions/22_curriculum_rl` | **passed** | CSV rows: 3; `synthetic` | Synthetic learning curves do not demonstrate sample efficiency for a trained navigation agent. |
| C23 | `contributions/23_gaussian_splatting_mapper` | **passed** | CSV rows: 2; `synthetic` | This is a 2D Gaussian proxy, not photorealistic 3D Gaussian Splatting reconstruction. |
| C24 | `contributions/24_nerf_uncertainty` | **passed** | CSV rows: 2; `synthetic` | The evaluator uses synthetic uncertainty fields and does not train or render a NeRF. |
| C25 | `contributions/25_adversarial_attack_simulator` | **passed** | CSV rows: 6; `synthetic` | Injected numerical attacks are not an end-to-end ROS 2 penetration test. |
| C26 | `contributions/26_swarm_consensus` | **passed** | CSV rows: 12; `synthetic` | In-process simulation does not model real network delays, packet ordering, or ROS 2 DDS failure modes. |

## Implementation work in this audit

- Fixed C11 standalone evaluation path so the runner can import the root `dynnav` package when launched exactly as registered. The full suite, first-eleven batch, and C26-only batch were rerun.
- Updated the website contribution explorer so each C01-C26 card links directly to its canonical contribution directory and registered experiment runner; added a separate C27 theory card and an evidence-review link.
- Added the evidence manifest and the requested audit reports under `docs/audits/`.

## Test environment limits

- `pytest -q` could not run because `pytest` is not installed; `python -m pytest -q` confirmed `No module named pytest`. No pytest outcome is claimed.
- `torch` is not installed in the selected Python runtime. Existing `.pt` files are present, but this audit could not inspect checkpoint contents or establish their training provenance.
- No ROS 2 / Gazebo execution is claimed in this audit. Existing repository CI and stored artifacts are described separately from fresh local execution.
- The LILocBench raw pose file was not present as a local input, so the documented 3,194-pose summary was not independently recomputed here.

See the execution, C00, C27, real-data, ROS/Gazebo, statistics, website, and publication-readiness reports linked in this audit directory.
