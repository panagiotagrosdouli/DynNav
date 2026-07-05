# DynNav Benchmarks

This directory contains repository-level benchmark metadata and, over time, should become the central entry point for evaluating DynNav modules.

## Files

| File | Purpose |
|---|---|
| `dynnav_benchmark_manifest.yaml` | Machine-readable inventory of benchmark targets, baselines, metrics, ablations, and readiness goals. |

## Current workflow

1. Choose a module from `dynnav_benchmark_manifest.yaml`.
2. Run the module-specific experiment script.
3. Save CSV output using the shared schema from `docs/BENCHMARK_PROTOCOL.md`.
4. Generate a cross-module Markdown summary:

```bash
python tools/generate_benchmark_summary.py \
  --results 'results/**/*.csv' \
  --output docs/BENCHMARK_RESULTS_SUMMARY.md
```

## Shared result schema

The recommended common columns are:

```csv
module_id,experiment_name,seed,scenario,method,baseline,n_trials,success_rate,collision_rate,path_length,time_to_goal,replans,mean_risk,max_risk,cvar_risk,uncertainty_integral,intervention_rate,compute_time_ms
```

Modules may add extra columns when needed.

## Scientific rule

A benchmark should not only show that the code runs. It should compare a proposed method against a meaningful baseline using metrics that are relevant to navigation, safety, uncertainty, or robustness.
