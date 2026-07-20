# Fragile Commitment Benchmark

This benchmark constructs navigation counterexamples in which routes have similar immediate traversal risk but different retained recovery freedom.

The controlled scenario contains two homotopy classes:

- a short, narrow route vulnerable to a dynamic closure;
- a longer route that preserves recovery and escape options.

Randomized experiments extend this mechanism across `open`, `bottleneck`, `culdesac`, and `multiroute` topology families.

## End-to-end workflow

Generate randomized paired observations:

```bash
python benchmarks/fragile_commitment/random_benchmark.py \
  --seeds 100 \
  --output random_topology_results.csv
```

Run paired hypothesis tests:

```bash
python benchmarks/fragile_commitment/paired_tests.py \
  random_topology_results.csv \
  --baseline risk_only \
  --candidate recoverability_aware \
  --output-csv paired_tests.csv \
  --markdown paired_tests.md
```

Generate publication-oriented figures:

```bash
python benchmarks/fragile_commitment/paper_figures.py \
  random_topology_results.csv \
  --output-dir paper/figures/fragile_commitment \
  --format pdf
```

The figure command writes:

- mission success by topology family;
- minimum recoverability by topology family;
- cumulative recoverability loss by topology family;
- fragility penalty by topology family;
- route-risk versus minimum-recoverability scatter.

PDF is the default manuscript format. SVG is useful for editable vector graphics and PNG for previews.

## Compared policies

- `shortest`
- `risk_only`
- `safe_return`
- `recoverability_aware`

The raw CSV records topology family, seed, route selection, path length, route risk, recoverability-profile statistics, fragility penalty, event exposure, and mission success. Pairing is preserved by `(family, seed)`.

## Statistical boundary

Wilcoxon signed-rank tests are used for paired continuous metrics and exact McNemar tests for paired mission success. Reported p-values are uncorrected; multiplicity correction and confirmatory hypothesis selection must be declared in the manuscript analysis plan.

## Scientific purpose

The benchmark tests the falsifiable claim that collision risk and recoverability are not interchangeable. A useful counterexample has near-equal route risk but a large recoverability gap and different mission outcomes after the same dynamic event.

This is a synthetic experimental instrument, not a formal safety certificate or hardware-validation claim.
