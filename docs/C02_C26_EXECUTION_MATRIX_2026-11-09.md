# DynNav C02–C26 sequential execution and evidence matrix

**Date:** 2026-11-09. **Exact scope:** The 25 separately registered contributions C02, C03, …, C26. C07 includes two historical directories and counts once.

## 1. Actually executed experiments

[GitHub Actions run #42702357587](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42702357587) **passed** and executed each of the 25 registered contribution experiments **separately and in ascending ID order**, with `--fail-on-skip`. Each non-empty result artifact has a recorded row count, SHA-256 and exact command in its own `manifest.json`. No registered experiment was skipped.

The same workflow read and structurally inspected **444 source/model/dataset/result/documentation files** across C02–C26 at that revision, including both C07 directories, and retained one machine-readable SHA-256 record per file. These file checks are compilation / loading / parsing checks, not per-script full runtime validation.

## 2. Per-contribution overview

| Contribution | Research focus | Registered experiment | Scientific/evidence limit |
|---|---|---|---|
| C02 | Uncertainty calibration | PASS: registered synthetic | independent grid-instance calibration; target physical sensor coverage |
| C03 | Belief and risk planning | PASS: registered synthetic | CVaR/expected risk vs length; ethical-risk return repaired |
| C04 | Returnability and irreversibility | PASS: registered synthetic | bottleneck and safe-return metrics |
| C05 | Safe-mode navigation | PASS: registered synthetic | hysteresis transitions, velocity supervision |
| C06 | Energy and connectivity | PASS: registered synthetic | energy reserve, radio-link margins |
| C07 | Next-best view | PASS: registered synthetic | returnability-aware scoring; two historical directories |
| C08 | Security IDS | PASS: registered synthetic | severity-conditioned mitigation, no live ROS2 attack evidence |
| C09 | Multi-robot coordination | PASS: registered synthetic | predefined conflicts, no DDS communication evidence |
| C10 | Human/language/ethics | PASS: registered synthetic | human-zone restriction policy; not human-subject validation |
| C11 | VLM navigation agent | PASS: registered synthetic | deterministic goal validation; no actual VLM model execution |
| C12 | Diffusion occupancy | PASS: registered synthetic | probabilistic forecast proxy; not trained diffusion |
| C13 | Latent world model | PASS: registered synthetic | simulated latent rollouts; not trained model |
| C14 | Causal risk attribution | PASS: registered synthetic | hand-specified causal model; counterfactual rankings |
| C15 | Neuromorphic sensing | PASS: registered synthetic | simulated events, not event camera hardware |
| C16 | Federated nav learning | PASS: registered synthetic | synthetic aggregation, not distributed robot training |
| C17 | Topological-semantic mapping | PASS: registered synthetic | deterministic semantic embedding placeholder |
| C18 | Formal safety shields | PASS: registered synthetic | numerical stress suite; NOT a formal proof |
| C19 | LLM mission planner | PASS: registered synthetic | constrained plan validation; no real LLM reliability |
| C20 | Multimodal failure explainer | PASS: registered synthetic | rubric fixture; no blinded operator evaluation |
| C21 | PPO navigation agent | PASS: registered synthetic | fixture policy; NOT trained PPO performance |
| C22 | Curriculum RL | PASS: registered synthetic | synthetic learning curve; NOT learning-efficiency proof |
| C23 | Gaussian splatting mapping | PASS: registered synthetic | 2D Gaussian proxy; NOT trained 3DGS |
| C24 | NeRF uncertainty | PASS: registered synthetic | synthetic uncertainty field; NOT trained NeRF |
| C25 | Adversarial attacks | PASS: registered synthetic | numerical injection, no hardware penetration test |
| C26 | Swarm consensus | PASS: registered synthetic | in-process Byzantine simulation; no real DDS/robot swarm |

**The passing registered experiments are all labeled `synthetic`.** A passing file check is not proof that an old numerical result was reproduced. A passing PPO proxy is not actual PPO training. A Gaussian occupancy proxy is not trained 3D Gaussian Splatting. A synthetic NeRF uncertainty field is not a rendered/trained NeRF. A model label is not sufficient to establish scientifically supported model performance.

## 3. Actual stronger C02 evaluation and discovered C03 defect

**C02 archived neural uncertainty dataset:** On [run #42702357587](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42702357587), the real retained *synthetic grid-world* uncertainty data were evaluated with **18 map-instance IDs for calibration fitting and 12 entirely held-out map instances**. The ECE-style absolute-error metric was **3.13473** raw, **0.60325** global-scaled and **0.52399** quantile-bin. But empirical 1-sigma coverage was **89.631%** raw, **50.359%** scaled and **54.413%** quantile-bin. This is **not** a validated Gaussian posterior. In particular the ECE-style comparison of mean sigma and mean absolute error is not equivalent to nominal Gaussian interval coverage.

**C03 physical + ethical risk composition defect:** The historical `human_and_ethical_edge_cost` helper computed values but omitted its intended return (an unreachable return appeared after another function). The branch restores the full cost breakdown and imports C10 policy dependencies through repository-relative paths. Targeted tests verify physical risk weight and human-zone penalties. This is actual code repair, not merely narrative.

## 4. Where the evidence is

- Runner: `scripts/run_contribution_suite.py --only C02` through `--only C26`, each invoked separately in `.github/workflows/c02-c26-exhaustive.yml`.
- File audit: `scripts/audit_contributions_c02_c26.py`.
- CI artifact: `c02-c26-per-file-and-per-contribution-execution`, containing `file_manifest.json`, `summary.md`, 25 individual registered experiment suites and `individual_runs_summary.json`.
- Instance-separated C02 archive: `c02_real_archived_grid_instance_holdout.json`.
- Dedicated per-contribution report: `contributions/<registered-directory>/EXECUTION_EVIDENCE.md`; C07 has a companion note in its historical exploration directory.
- Re-run controls: `python scripts/validate_contribution_registry.py` and the C02/C03 and all-contribution auditor regression suites.

## 5. What is NOT complete

This work does **not** mean that every one of hundreds of historical scripts has run, that held-out real datasets exist for each contribution, that each model has been independently trained, that ROS2 Nav2 integration exists for each technique or that any of C02–C26 controlled a physical robot. Each requires contribution-specific work, real measurements, safety commissioning, baseline/ablation studies and independent review.

Real ROS 2 sensor replay and C01 simulated closed loop from prior contributions cannot be transferred automatically as proof of C02–C26 operation: the claimed algorithms must be instrumented and verified individually.

**Physical C02–C26 contribution-specific robot trials verified by this workflow: zero.**

## 6. Next scientific validation gates

Prioritize C02 real localization/uncertainty ground truth, C03 genuinely calibrated route-risk distributions and physical navigation outcomes, C04–C06 safety/returnability and energy/communication physical instrumentation, C07 sensor-derived frontiers, C08–C10 authenticated robot context, and C11–C26 real model training or real systems evidence corresponding to each hypothesis. For every result, preserve exact dataset provenance, mission context, baseline, random seeds, failure trials and physical robot identity when applicable.

This is a **successful exhaustive baseline audit and synthetic execution pass**, NOT final completion of all C02–C26 scientific research.
