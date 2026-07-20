# Fragile Commitment Benchmark

This benchmark constructs navigation counterexamples in which routes have similar immediate traversal risk but different retained recovery freedom.

The controlled scenario contains two homotopy classes:

- a short, narrow route vulnerable to a dynamic closure;
- a longer route that preserves recovery and escape options.

Randomized experiments extend this mechanism across `open`, `bottleneck`, `culdesac`, and `multiroute` topology families.

## Controlled benchmark

First validate that the generated scenarios preserve the intended counterexample across the requested seeds:

```bash
python benchmarks/fragile_commitment/validate_counterexample.py --seeds 100
```

Generate paired per-seed benchmark results:

```bash
python benchmarks/fragile_commitment/benchmark.py \
  --seeds 100 \
  --output results.csv
```

Generate summary statistics:

```bash
python benchmarks/fragile_commitment/statistical_analysis.py \
  results.csv \
  --summary-csv summary.csv \
  --markdown summary.md
```

## Randomized topology families

The randomized benchmark expands the controlled counterexample into four reproducible map families:

- `open`
- `bottleneck`
- `culdesac`
- `multiroute`

Run all families:

```bash
python benchmarks/fragile_commitment/random_benchmark.py \
  --seeds 100 \
  --output random_topology_results.csv
```

Run a subset:

```bash
python benchmarks/fragile_commitment/random_benchmark.py \
  --families bottleneck culdesac \
  --seeds 250 \
  --output focused_results.csv
```

## Compared policies

- `shortest`
- `risk_only`
- `safe_return`
- `recoverability_aware`

The raw CSV records topology family, seed, selected route, path length, route risk, recoverability-profile statistics, fragility penalty, event exposure, and mission success. Pairing is preserved by `(family, seed)`.

## Paired hypothesis tests

Compare the recoverability-aware planner against the risk-only baseline:

```bash
python benchmarks/fragile_commitment/paired_tests.py \
  random_topology_results.csv \
  --baseline risk_only \
  --candidate recoverability_aware \
  --output-csv paired_tests.csv \
  --markdown paired_tests.md
```

The analysis includes:

- Wilcoxon signed-rank tests for continuous metrics;
- exact McNemar tests for mission success;
- rank-biserial effect sizes;
- normalized discordant-pair effect sizes.

Results are reported separately for every topology family. Reported p-values are uncorrected unless otherwise specified in the manuscript.

## Publication figures

Generate publication-ready figures:

```bash
python benchmarks/fragile_commitment/paper_figures.py \
  random_topology_results.csv \
  --output-dir paper/figures/fragile_commitment \
  --format pdf
```

Generated figures include:

- mission success by topology family;
- minimum recoverability by topology family;
- cumulative recoverability loss;
- fragility penalty;
- route-risk versus recoverability scatter plot.

Supported formats:

- PDF
- SVG
- PNG

## End-to-end workflow

```text
benchmark.py
        │
        ▼
results.csv
        │
        ▼
random_benchmark.py
        │
        ▼
random_topology_results.csv
        │
        ▼
paired_tests.py
        │
        ▼
paired_tests.csv
        │
        ▼
paper_figures.py
        │
        ▼
paper/figures/
```

## Scientific purpose

The benchmark tests the falsifiable hypothesis that collision risk and recoverability are distinct route properties. Routes with similar collision risk may retain substantially different recovery freedom, leading to different outcomes after identical dynamic changes.

This benchmark is a synthetic experimental research instrument and does not constitute a formal safety certificate or hardware-validation claim.