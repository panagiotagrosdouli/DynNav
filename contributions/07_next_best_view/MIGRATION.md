# Contribution 07 consolidation plan

Contribution 07 currently spans two directories for historical reasons:

- `07_nbv_exploration`: original frontier and information-gain implementation used by existing tests.
- `07_next_best_view`: upgraded returnability-aware and connectivity-aware scoring module.

Both directories contain distinct active material, so neither should be deleted without a controlled file migration.

The target structure is one canonical directory:

```text
07_next_best_view/
├── README.md
├── code/
├── experiments/
├── results/
└── docs/
```

Before removing `07_nbv_exploration`, move its original implementation and results into the canonical directory and update:

- `tests/test_07_nbv_exploration.py`
- `tests/test_frontier_vs_infogain.py`
- repository documentation and maintenance scripts

This note prevents accidental deletion while the consolidation is pending.
