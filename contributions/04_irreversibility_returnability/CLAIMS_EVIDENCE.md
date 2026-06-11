# C04 — Irreversibility & Returnability

## Claim

Returnability-aware safe mode improves planning feasibility under strict irreversibility constraints.

## Evidence

Benchmark file:

`results/c04_returnability_summary.csv`

Observed results:

- Hard threshold success rate: 26.7%
- Minimum feasible τ: 0.85
- Safe-mode success rate: 100%
- Safe-mode relaxed cases: 15 / 26
- Mean τ relaxation gap: 0.080
- Returnability sweep success rate: 100%

## Interpretation

The hard-threshold planner failed for most tested thresholds because no path satisfied the strict irreversibility constraint.

Safe mode recovered feasibility by relaxing the irreversibility threshold to the smallest viable value while still tracking mean and maximum irreversibility along the path.

## Supported Conclusion

Contribution 04 demonstrates that returnability-aware safe mode can prevent silent planning failure under overly strict irreversibility constraints.

It should be described as a feasibility-preserving safety mechanism, not as a guarantee that all irreversible states are avoided.
