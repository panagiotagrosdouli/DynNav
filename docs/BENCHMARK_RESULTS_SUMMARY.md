# DynNav Benchmark Results Summary

This file was generated from CSV benchmark outputs.

The table reports grouped averages by module, experiment, method, and baseline.

| module_id | experiment_name | method | baseline | n_trials | success_rate | collision_rate | path_length | mean_risk | max_risk | cvar_risk | compute_time_ms | source_files |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C03 | risk_aware_grid_planning_demo | expected_plus_cvar_risk_planner | shortest_path | 10 | 0.95 | 0.05 | 43 | 0.17 | 0.405 | 0.355 | 12.75 | results/example_benchmark_results.csv |
| C05 | safe_mode_threshold_demo | hysteretic_safe_mode_controller | no_safe_mode | 10 | 1 | 0 | 48.5 | 0.12 | 0.31 | 0.28 | 8.6 | results/example_benchmark_results.csv |
| C18 | shield_stress_test_demo | shielded_controller | unshielded_controller | 10 | 1 | 0 | 46.1 | 0.14 | 0.27 | 0.25 | 9.2 | results/example_benchmark_results.csv |


## Interpretation notes

- A generated table is only as credible as the benchmark design that produced the CSV files.
- Single-run rows should be treated as demonstrations, not strong evidence.
- Missing values mean that the source CSV did not provide that metric.

## Regeneration command

```bash
python tools/generate_benchmark_summary.py \
  --results 'results/**/*.csv' \
  --output docs/BENCHMARK_RESULTS_SUMMARY.md
```

## Important limitation

The current CSV file is an example artifact that documents the expected format. It should be replaced or extended with real benchmark outputs from the module scripts before being used as scientific evidence.
