# Fragile Commitment Benchmark

This benchmark constructs controlled navigation counterexamples in which routes have similar immediate traversal risk but different retained recovery freedom.

The first scenario contains two homotopy classes:

- a short, narrow corridor that is vulnerable to a dynamic closure;
- a longer, open detour that preserves alternative motion options.

The benchmark is deliberately lightweight and reproducible. It uses only the Python standard library and NumPy.

## Controlled benchmark

First validate that the generated scenarios preserve the intended counterexample across the requested seeds:

```bash
python benchmarks/fragile_commitment/validate_counterexample.py --seeds 100
```

Generate paired per-seed results:

```bash
python benchmarks/fragile_commitment/benchmark.py --seeds 100 --output results.csv
```

Create a per-planner summary CSV and a paper-ready Markdown table:

```bash
python benchmarks/fragile_commitment/statistical_analysis.py results.csv \
  --summary-csv summary.csv \
  --markdown summary.md
```

## Randomized topology families

The randomized benchmark expands the controlled counterexample into four reproducible map families:

- `open`: weak bottleneck contrast for a near-neutral baseline;
- `bottleneck`: a long one-cell commitment corridor;
- `culdesac`: deceptive side pockets attached to the fragile class;
- `multiroute`: extra cross-links and local escape alternatives.

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

Every `(family, seed)` pair is evaluated by the same four policies:

- `shortest`
- `risk_only`
- `safe_return`
- `recoverability_aware`

The raw CSV records topology family, seed, selected route, route length, route risk, recoverability-profile statistics, fragility penalty, event exposure, and mission success. Paired observations should be retained for paired hypothesis tests and effect-size estimation.

`configs/randomized_default.yaml` records the intended default experimental settings. The current runner exposes the active settings through command-line arguments; configuration-file loading will be added only when it can be done without introducing an unnecessary dependency.

## Scientific purpose

The benchmark tests the falsifiable claim that collision risk and recoverability are not interchangeable. A useful counterexample has near-equal route risk but a large recoverability gap and different mission outcomes after the same dynamic event.

This is an experimental instrument, not a formal safety certificate.
