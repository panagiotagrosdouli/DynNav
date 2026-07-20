# Fragile Commitment Benchmark

This benchmark constructs controlled navigation counterexamples in which routes have similar immediate traversal risk but different retained recovery freedom.

The first scenario contains two homotopy classes:

- a short, narrow corridor that is vulnerable to a dynamic closure;
- a longer, open detour that preserves alternative motion options.

The benchmark is deliberately lightweight and reproducible. It uses only the Python standard library and NumPy.

## Run

First validate that the generated scenarios preserve the intended counterexample across the requested seeds:

```bash
python benchmarks/fragile_commitment/validate_counterexample.py --seeds 100
```

The validation gate checks that route risk remains close, the recoverability and fragility gaps remain large enough, and the injected event blocks only the fragile route. Thresholds are explicit command-line options rather than hidden tuning constants.

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

Each seed evaluates the same generated scenario with four route-selection policies:

- `shortest`
- `risk_only`
- `safe_return`
- `recoverability_aware`

The raw CSV records route length, route risk, recoverability-profile statistics, fragility penalty, whether the injected closure blocks the chosen route, and mission success. The summary CSV reports per-planner means and descriptive 95% confidence intervals. Raw paired observations should be retained for subsequent paired hypothesis tests when randomized topology families are added.

## Scientific purpose

The benchmark tests the falsifiable claim that collision risk and recoverability are not interchangeable. A useful counterexample has near-equal route risk but a large recoverability gap and different mission outcomes after the same dynamic event.

This is an experimental instrument, not a formal safety certificate.
