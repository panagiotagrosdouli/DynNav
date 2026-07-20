# Fragile Commitment Benchmark

This benchmark constructs controlled navigation counterexamples in which routes have similar immediate traversal risk but different retained recovery freedom.

The first scenario contains two homotopy classes:

- a short, narrow corridor that is vulnerable to a dynamic closure;
- a longer, open detour that preserves alternative motion options.

The benchmark is deliberately lightweight and reproducible. It uses only the Python standard library and NumPy.

## Run

```bash
python benchmarks/fragile_commitment/benchmark.py --seeds 100 --output results.csv
```

Each seed evaluates the same generated scenario with four route-selection policies:

- `shortest`
- `risk_only`
- `safe_return`
- `recoverability_aware`

The exported CSV records route length, route risk, recoverability-profile statistics, fragility penalty, whether the injected closure blocks the chosen route, and mission success.

## Scientific purpose

The benchmark tests the falsifiable claim that collision risk and recoverability are not interchangeable. A useful counterexample has near-equal route risk but a large recoverability gap and different mission outcomes after the same dynamic event.

This is an experimental instrument, not a formal safety certificate.
