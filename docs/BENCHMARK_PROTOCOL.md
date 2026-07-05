# DynNav Benchmark Protocol

This document defines the minimum benchmark standard for DynNav experiments.

The purpose is to make every result auditable, reproducible, and comparable across modules.

## Benchmark principle

A DynNav experiment should answer one precise question:

```text
Does the proposed navigation component improve a measurable safety, uncertainty, robustness, or efficiency outcome compared with a meaningful baseline?
```

A result is not considered sufficient if it only shows that the code runs.

## Required experiment metadata

Every benchmark should report:

| Field | Description |
|---|---|
| module_id | Contribution number or module name |
| experiment_name | Human-readable experiment name |
| seed | Random seed |
| scenario | Scenario name or generator configuration |
| baseline | Baseline method |
| method | Proposed method |
| n_trials | Number of independent trials |
| runtime_s | Wall-clock runtime |
| output_path | CSV/JSON result path |

## Required navigation metrics

Use these whenever applicable.

| Metric | Meaning |
|---|---|
| success_rate | Fraction of trials that reached the goal |
| collision_rate | Fraction of trials with collision |
| path_length | Total path distance |
| time_to_goal | Simulated or real execution time |
| replans | Number of replanning events |
| min_obstacle_distance | Closest distance to any obstacle |
| mean_risk | Average risk along the path |
| max_risk | Maximum risk along the path |
| cvar_risk | Tail risk above a chosen quantile |
| uncertainty_integral | Accumulated uncertainty along the path |
| intervention_rate | Fraction of commands modified by a safety layer |
| correction_cost | Cost introduced by safety corrections |
| compute_time_ms | Planning or inference time |

## Required uncertainty metrics

Use these when a module emits probabilities, confidence values, uncertainty estimates, risk maps, or future occupancy predictions.

| Metric | Meaning |
|---|---|
| brier_score | Proper score for probabilistic binary predictions |
| nll | Negative log likelihood |
| ece | Expected calibration error |
| auroc_ood | Out-of-distribution discrimination |
| high_risk_precision | Precision for high-risk classification |
| high_risk_recall | Recall for high-risk classification |
| prediction_error | Error between predicted and observed future state |

## Baseline requirements

Each benchmark must include at least one baseline.

Recommended baselines:

- shortest-path planner,
- risk-unaware planner,
- uncertainty-disabled planner,
- uncalibrated uncertainty planner,
- no-shield controller,
- reactive-only dynamic obstacle avoidance,
- greedy exploration,
- random policy,
- classical Nav2-style configuration where applicable.

## Ablation requirements

For publication-oriented modules, include ablations that remove one design choice at a time.

Examples:

| Module type | Recommended ablation |
|---|---|
| risk-aware planner | no risk term, expected risk only, CVaR risk |
| uncertainty planner | no uncertainty, raw uncertainty, calibrated uncertainty |
| learned heuristic | classical heuristic, learned heuristic, admissible-clipped learned heuristic |
| safety shield | unshielded, shielded, shielded with different thresholds |
| dynamic prediction | current obstacle only, constant-velocity prediction, probabilistic prediction |
| multi-robot | no coordination, conflict-only coordination, risk-aware coordination |

## Reporting standard

Every experiment should produce both:

1. a machine-readable output file, preferably CSV or JSON;
2. a short Markdown summary explaining what the result means.

The Markdown summary should include:

- command used,
- environment assumptions,
- baseline,
- metric table,
- interpretation,
- limitations.

## Statistical reporting

When possible, report:

- mean,
- standard deviation,
- median,
- worst-case value,
- number of trials,
- confidence interval or bootstrap interval for important metrics.

Single-run demonstrations should be labeled as demonstrations, not evidence of performance.

## Failure-case reporting

DynNav should explicitly document failures.

For each failed trial, log:

- failure type,
- final robot state,
- nearest obstacle distance,
- whether a safety intervention occurred,
- whether the failure was caused by perception, planning, control, communication, or model error.

## Suggested output schema

```csv
module_id,experiment_name,seed,scenario,method,baseline,n_trials,success_rate,collision_rate,path_length,time_to_goal,replans,mean_risk,max_risk,cvar_risk,uncertainty_integral,intervention_rate,compute_time_ms
```

Modules may add columns, but should not remove the shared core fields when they are applicable.

## Minimum bar for a credible result

A credible benchmark result must include:

- at least one baseline,
- at least 10 trials for stochastic experiments,
- deterministic seed control,
- explicit metric definitions,
- saved raw result file,
- limitations statement.

## Minimum bar for a publication-style result

A publication-style result should include:

- multiple baselines,
- ablation study,
- sensitivity analysis,
- failure analysis,
- statistical uncertainty,
- reproducible command,
- generated table or figure,
- discussion of assumptions and external validity.
