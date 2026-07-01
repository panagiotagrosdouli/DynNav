# C02 Scientific Upgrade Notes — Uncertainty Calibration for Navigation

## What was already strong

Contribution 02 already contained a scientifically honest result: the predicted uncertainty was informative, but not fully calibrated.

The reported results showed:

- 25,235 evaluated states,
- MAE = 0.8986,
- Pearson correlation between uncertainty and absolute error = -0.0504,
- Spearman correlation = 0.4040,
- ECE-style calibration error = 3.0011,
- 1σ / 2σ / 3σ coverage far from ideal Gaussian coverage.

This is valuable because it does not overclaim. It recognizes that uncertainty can be useful for ranking unreliable predictions while still being unsafe to interpret as a probability-calibrated confidence interval.

## Main weakness before this upgrade

The original module identified miscalibration, but it did not yet provide a clear calibration repair mechanism.

That means downstream planning modules could use uncertainty as a risk signal, but they could not know whether a reported sigma value had a reliable probabilistic meaning.

## New contribution added

C02 now includes an explicit calibration layer:

```text
code/uncertainty_calibrator.py
```

and a benchmark:

```text
experiments/eval_uncertainty_calibration.py
```

The new code supports:

- absolute-error calibration metrics,
- Pearson and Spearman uncertainty-error correlation,
- 1σ / 2σ / 3σ coverage,
- ECE-style calibration error,
- global scale calibration,
- quantile-bin calibration.

## Why this matters scientifically

A planner should not blindly trust uncertainty estimates.

There are three distinct levels:

1. **Uncertainty is present** — the model outputs a sigma-like value.
2. **Uncertainty is informative** — larger sigma tends to correspond to larger error.
3. **Uncertainty is calibrated** — sigma has a reliable probabilistic interpretation.

C02 now explicitly separates these levels.

## Reviewer-safe claim

A strong claim after this upgrade is:

> Contribution 02 evaluates uncertainty not only as a model output, but as a calibrated planning signal. It distinguishes rank-informative uncertainty from probabilistically calibrated uncertainty and provides calibration methods that can be audited before uncertainty is passed to risk-aware planners.

## What the new benchmark does

Run:

```bash
python contributions/02_uncertainty_calibration/experiments/eval_uncertainty_calibration.py
```

The benchmark compares:

| Method | Meaning |
|---|---|
| raw_sigma | original predicted uncertainty |
| global_scale | one scalar correction fitted on training errors |
| quantile_bin_calibrated | piecewise calibration by uncertainty bins |

It outputs:

```text
contributions/02_uncertainty_calibration/results/c02_calibration_benchmark.csv
```

## Integration with planning

The calibrated sigma values can be passed to downstream risk-aware planning modules.

Recommended integration:

```text
model prediction → raw uncertainty → calibration layer → calibrated uncertainty → risk map → planner
```

This is more scientifically defensible than:

```text
model prediction → raw uncertainty → planner
```

## Remaining limitations

- Synthetic benchmark support is included for reproducibility, but real navigation datasets should be used for final claims.
- Calibration is currently scalar or piecewise scalar, not a full probabilistic distribution model.
- Calibration quality may shift under distribution shift, new maps, new sensors, or different robot dynamics.
- Correlation does not imply sufficient calibration for safety-critical control.

## Next research step

The strongest next extension is **online uncertainty recalibration**.

As the robot observes new prediction errors during deployment, it should update the calibration layer without retraining the whole model.

This would turn C02 from static uncertainty calibration into adaptive uncertainty reliability monitoring for dynamic navigation.