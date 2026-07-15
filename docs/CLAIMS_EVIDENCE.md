# Claims and Evidence Registry

This document records the evidence standard required for research claims in DynNav.

The previous generated version linked scripts, CSV files, and figures as though they were located beside this document. Those targets are not present at the referenced paths on the current branch. They are therefore listed below as **historical or pending artifacts**, not as clickable evidence.

## Evidence states

| State | Meaning |
|---|---|
| **Verified** | The implementation, command, configuration, raw result, and interpretation are present and traceable in the repository. |
| **Implemented** | Source code and deterministic tests exist, but the full experiment package required for a publication claim is incomplete. |
| **Experimental** | A prototype or limited synthetic evaluation exists. Generalization has not been established. |
| **Pending validation** | The claim requires missing or incomplete scripts, raw results, figures, statistical analysis, or external validation. |
| **Not claimed** | The repository explicitly does not assert the property. |

## Current claim registry

### Learned-heuristic planning

**Research hypothesis:** a learned admissible heuristic may reduce search effort without increasing solution cost.

**Current status:** Pending validation.

Historical artifact names referenced by an earlier generated report:

- `eval_astar_learned.py`
- `train_heuristic.py`
- `astar_learned_heuristic.py`
- `astar_eval_results.csv`
- `astar_learned_vs_classic.png`
- `autotune_expansions.png`
- `autotune_ratio.png`

A verified claim requires exact repository paths, admissibility checks, identical scenarios and seeds, raw per-run results, and a statistical comparison against classical A*.

### Irreversibility-threshold behavior

**Research hypothesis:** feasibility and planning effort may change nonlinearly as the irreversibility threshold varies.

**Current status:** Experimental / pending validation.

Historical artifact names:

- `run_irreversibility_tau_sweep.py`
- `plot_irreversibility_tau_sweep.py`
- `irreversibility_tau_sweep.csv`
- `irreversibility_bottleneck_tau_sweep.csv`
- `irreversibility_success_vs_tau.png`
- `irreversibility_expansions_vs_tau.png`
- `irreversibility_cost_vs_tau.png`
- `irreversibility_maxI_vs_tau.png`

A verified phase-transition claim requires a formally defined threshold variable, multiple scenario families, uncertainty analysis, confidence intervals, and sensitivity to grid resolution and obstacle geometry.

### Risk–cost trade-off

**Research hypothesis:** increasing risk aversion may reduce selected risk metrics while increasing geometric or computational cost.

**Current status:** Experimental / pending validation.

Historical artifact names:

- `run_risk_weighted_lambda_sweep.py`
- `plot_risk_weighted_lambda_sweep.py`
- `risk_weighted_lambda_sweep.csv`
- `risk_weighted_geocost_vs_lambda.png`
- `risk_weighted_expansions_vs_lambda.png`
- `risk_weighted_maxI_vs_lambda.png`
- `risk_weighted_meanI_vs_lambda.png`

A verified trade-off claim requires a mathematical risk definition, controlled sweeps, unchanged scenario information, multiple seeds, uncertainty estimates, and comparison with geometric and risk-aware baselines.

### Innovation-based attack detection

**Research hypothesis:** innovation statistics may identify some injected estimation attacks and provide planner-facing trust or alarm signals.

**Current status:** Experimental / pending validation.

Historical artifact names:

- `eval_ids_sweep.py`
- `eval_ids_replay.py`
- `attack_injector.py`
- `security_monitor.py`
- `security_monitor_cusum.py`
- `ids_roc.csv`
- `ids_pr.csv`
- `ids_replay_log.csv`
- `ids_methods_summary.csv`
- `attack_aware_ukf_demo_log.csv`
- `ids_to_planner_hook_log.csv`
- `ids_roc.png`
- `ids_pr.png`
- `ids_roc_compare.png`
- `attack_aware_nis.png`
- `attack_aware_trust.png`
- `ids_mitigation_outputs.png`
- `ids_alarm_safe_mode.png`

A verified detection claim requires an explicit threat model, attack families and magnitudes, train/test separation where applicable, ROC and precision–recall analysis, false-alarm reporting, detection delay, and comparison with documented baselines.

### Statistical navigation evaluation

**Research hypothesis:** risk-, uncertainty-, or recoverability-aware planning may improve selected mission metrics under controlled conditions.

**Current status:** Pending validation.

Historical artifact names:

- `batch_run_30_seeds.py`
- `batch_run_ablation_30_seeds.py`
- `run_ablation_t_tests.py`
- `analyze_statistical_validation.py`
- `ablation_results.csv`
- `ablation_t_test_results.csv`
- `t_test_results.csv`
- `statistical_summary.csv`
- `boxplot_total_cost.png`
- `boxplot_total_risk.png`
- `boxplot_total_distance.png`
- `boxplot_max_risk.png`

A reportable result requires raw per-seed data, exact configuration and commit, effect sizes, confidence intervals, appropriate multiplicity handling, failure accounting, and reproducible figure generation.

## Claims explicitly outside current evidence

DynNav currently does **not** claim:

- a formal or certified safety guarantee;
- state-of-the-art performance;
- complete probabilistic calibration;
- production-ready ROS2/Nav2 integration;
- validated Gazebo performance;
- real-robot or hardware validation;
- universal robustness to adversarial attacks.

## Adding evidence

For each new claim, commit all of the following:

1. the exact implementation and experiment entry point;
2. a versioned configuration and random seeds;
3. raw, machine-readable results;
4. a script that regenerates every reported table or figure;
5. metric definitions and statistical methodology;
6. environment and dependency information;
7. a concise statement of limitations and evidence boundaries.

Use relative links only after the target files exist on the same branch. See [Evaluation Protocol](EVALUATION_PROTOCOL.md), [Reproducibility](REPRODUCIBILITY.md), and [Repository Audit](REPOSITORY_AUDIT.md).
