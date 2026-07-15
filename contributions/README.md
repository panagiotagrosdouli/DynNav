# DynNav Contributions

This directory contains the numbered research contributions of DynNav.

## Canonical structure

Each contribution should use one canonical directory and follow this structure where applicable:

```text
NN_module_name/
├── README.md
├── README_GR.md          # optional Greek version
├── code/                 # implementation specific to the contribution
├── experiments/          # reproducible experiment entry points
├── results/              # generated summaries and traceable artifacts
├── docs/                 # theory or extended technical notes
└── tests/                # module-local tests when appropriate
```

Use one primary English `README.md` and at most one Greek `README_GR.md`. Legacy names such as `readmegr.md` should not be added.

## Evidence maturity

Documentation must distinguish among:

- **Implemented** — code exists and is exercised by tests or reproducible commands.
- **Experimental** — prototype code or synthetic evaluation exists, but broader validation is incomplete.
- **Planned** — design documentation exists without a verified implementation.
- **Hardware validation required** — physical-robot evidence is not available.

Passing unit tests does not establish a formal safety guarantee, real-world robustness, or state-of-the-art performance.

## Numbering

One contribution number should map to one canonical directory. See [`CONTRIBUTION_NUMBERING.md`](CONTRIBUTION_NUMBERING.md).

Current consolidation notes:

- Contribution 02 is canonical under [`02_uncertainty_calibration/`](02_uncertainty_calibration/).
- Contribution 07 still spans a legacy implementation and an upgraded module; see [`07_next_best_view/MIGRATION.md`](07_next_best_view/MIGRATION.md) before moving or deleting files.

## Supporting research directories

Unnumbered directories such as ablation studies, benchmarking, hybrid planners, and realtime replanning are supporting experiments rather than standalone numbered contributions. They should remain clearly identified as support material until a later repository-wide move updates all code, tests, and links.
