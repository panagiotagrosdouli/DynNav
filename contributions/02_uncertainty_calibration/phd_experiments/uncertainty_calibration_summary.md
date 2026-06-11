# Uncertainty Calibration Analysis

- Total samples: 25235
- Mean absolute error: 0.8986
- Pearson corr(sigma, |error|): -0.0504
- Spearman corr(sigma, |error|): 0.4040
- ECE-style |mean sigma - mean |error||: 3.0011
- Coverage @ 1 sigma: 0.8684
- Coverage @ 2 sigma: 0.8873
- Coverage @ 3 sigma: 0.8953

## Figures

1. Scatter: |error| vs sigma -> `uncertainty_plots/sigma_vs_abs_error.png`
2. Binned calibration plot -> `uncertainty_plots/binned_calibration.png`

## Machine-readable metrics

- `uncertainty_calibration_metrics.csv`