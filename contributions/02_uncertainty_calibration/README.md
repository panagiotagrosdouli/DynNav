# Contribution 02 — Uncertainty Estimation and Calibration

[Back to the repository README](../../README.md)

## Purpose

This contribution evaluates whether a model's uncertainty signal is informative and whether its numerical scale is calibrated well enough for downstream navigation decisions.

## Maturity

**Research Prototype / Synthetic Validation.** The repository contains deterministic Python evaluation code. The contribution is not a formal safety guarantee and has not been validated on hardware through this document.

## Concepts

- **Uncertainty estimation:** produce a sigma-like confidence value.
- **Informativeness:** larger uncertainty tends to coincide with larger error.
- **Calibration:** uncertainty intervals have reliable empirical coverage.

A useful ranking signal can still be poorly calibrated. Downstream planners should therefore distinguish raw uncertainty from calibrated uncertainty.

## Implementation

- [`code/uncertainty_calibrator.py`](code/uncertainty_calibrator.py)
- [`experiments/eval_uncertainty_calibration.py`](experiments/eval_uncertainty_calibration.py)
- [`docs/SCIENTIFIC_UPGRADE.md`](docs/SCIENTIFIC_UPGRADE.md)

## Synthetic benchmark

From the repository root:

```bash
python contributions/02_uncertainty_calibration/experiments/eval_uncertainty_calibration.py
```

The benchmark writes its generated CSV under this contribution's `results/` directory. Generated values should only be treated as evidence together with the exact configuration, seed, command, and raw output.

## External dataset interface

An external CSV must contain these columns:

```text
prediction,target,sigma
```

The input path is user supplied and is therefore shown as a template rather than an executable repository command:

```text
python contributions/02_uncertainty_calibration/experiments/eval_uncertainty_calibration.py --input /absolute/path/to/uncertainty_predictions.csv
```

## Metrics

- mean absolute error;
- Pearson and Spearman association between uncertainty and absolute error;
- calibration error;
- empirical coverage at selected uncertainty multiples;
- before/after calibration comparison.

## Limitations

- Correlation does not establish probabilistic calibration.
- Calibration can degrade under distribution shift.
- Synthetic data does not establish real-sensor performance.
- Calibrated uncertainty improves auditability but does not guarantee safe control.
