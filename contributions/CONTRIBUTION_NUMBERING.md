# Contribution numbering policy

DynNav uses one canonical directory per numbered research contribution.

## Rules

1. Each number from `01` onward maps to exactly one canonical directory.
2. Extensions belong inside the existing contribution directory rather than in a second directory with the same number.
3. Historical or experimental variants should live under `experiments/`, `docs/`, or a clearly named subdirectory.
4. A numbered directory may be removed only after its code, tests, results, and inbound links have been migrated.
5. The canonical module must identify its maturity as `Implemented`, `Experimental`, `Planned`, or `Hardware validation required`.

## Current exceptions under consolidation

- Contribution 07 currently spans `07_nbv_exploration` and `07_next_best_view`. Both contain distinct active material and require a controlled migration.

Contribution 02 has been consolidated under `02_uncertainty_calibration`; the obsolete `02_uncertainty_estimation` placeholder is removed.
