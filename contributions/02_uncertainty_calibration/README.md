# Contribution 02 — Uncertainty Estimation

[![Module](https://img.shields.io/badge/Module-02-purple)](.) [![Type](https://img.shields.io/badge/Type-Probabilistic%20Sensing-blue)](.) [![Status](https://img.shields.io/badge/Status-Core-brightgreen)](.)

## Overview

Explicit **uncertainty modelling** for robot state estimation using Extended Kalman Filter (EKF) and Unscented Kalman Filter (UKF). Quantifies sensing uncertainty, localisation error, and map confidence for use in downstream risk-aware planning.

## Research Question

> **RQ2**: How can uncertainty be explicitly incorporated into navigation decisions?

## How It Works

```
Sensor readings → EKF/UKF → belief state (μ, Σ) → uncertainty metrics → planner
```

- **EKF**: linearised Kalman filter for Gaussian noise models
- **UKF**: sigma-point propagation for non-linear systems
- **Output**: per-cell uncertainty estimates fed to risk planner (Contribution 03)

## Files

```
02_uncertainty_estimation/
├── experiments/
└── results/
```

## Quick Start

```bash
python contributions/02_uncertainty_estimation/experiments/eval_uncertainty.py
```

## Key Concepts

| Method | Use Case | Complexity |
|--------|----------|------------|
| EKF | Linear/mildly non-linear systems | O(n²) |
| UKF | Strongly non-linear systems | O(n³) |
| Particle Filter | Multimodal distributions | O(N particles) |


# Results

## Experimental Setup

Contribution 02 evaluates whether the predicted uncertainty of a learned navigation model correlates with its actual prediction error.

The evaluation was performed on:

* 25,235 navigation states
* 30 randomly generated grid-world planning tasks
* A dedicated uncertainty-error benchmark dataset
* A drift-aware navigation dataset

The objective was not only to measure prediction accuracy, but also to assess whether uncertainty estimates provide meaningful information about model reliability.

---

## Quantitative Results

| Metric                            |   Value |
| --------------------------------- | ------: |
| Total Samples                     |  25,235 |
| Mean Absolute Error (MAE)         |  0.8986 |
| Pearson Correlation (σ, |error|)  | -0.0504 |
| Spearman Correlation (σ, |error|) |  0.4040 |
| ECE-style Calibration Error       |  3.0011 |
| Coverage @ 1σ                     |  86.84% |
| Coverage @ 2σ                     |  88.73% |
| Coverage @ 3σ                     |  89.53% |

---

## Interpretation

### Prediction Accuracy

The uncertainty model achieved a mean absolute error of 0.8986 across 25,235 evaluated states, indicating reasonably accurate predictions on the benchmark dataset.

### Uncertainty–Error Relationship

The Pearson correlation between predicted uncertainty and absolute prediction error was close to zero (-0.0504), indicating weak linear dependence.

However, the Spearman correlation reached 0.4040, suggesting a moderate monotonic relationship between uncertainty and prediction error.

This result indicates that larger uncertainty values are generally associated with larger prediction errors, although the relationship is not strong enough to consider the model fully calibrated.

### Coverage Analysis

The observed uncertainty coverage was:

* 86.84% within 1σ
* 88.73% within 2σ
* 89.53% within 3σ

For a perfectly calibrated Gaussian uncertainty model, the expected values would be approximately:

* 68.3% within 1σ
* 95.4% within 2σ
* 99.7% within 3σ

The discrepancy between expected and observed coverage indicates that the predicted uncertainty does not yet follow a well-calibrated probabilistic interpretation.

### Calibration Error

The ECE-style calibration error reached 3.0011, showing a substantial mismatch between predicted uncertainty magnitude and observed prediction error.

This suggests that while uncertainty estimates contain useful information, they should not yet be interpreted as fully reliable confidence intervals.

---

## Key Findings

* The uncertainty estimator successfully captures part of the model's prediction uncertainty.
* Predicted uncertainty is positively associated with prediction error.
* The uncertainty estimates are informative but not fully calibrated.
* Coverage statistics indicate significant deviation from ideal Gaussian calibration.
* Additional calibration techniques are required before uncertainty can be used as a trustworthy probabilistic confidence measure.

---

## Conclusion

Contribution 02 introduces an uncertainty-aware prediction framework for navigation planning and demonstrates that uncertainty estimates contain meaningful information about model reliability.

The results show that uncertainty is correlated with prediction error and can therefore support risk-aware planning decisions. However, the calibration analysis reveals that the current uncertainty estimates are not yet probabilistically well-calibrated.

This contribution establishes the foundation for future uncertainty-aware planning, exploration, and safety modules within DynNav.

## Integration

- **Feeds into**: Contribution 03 (belief-space planning)
- **Extended by**: Contribution 12 (diffusion maps) for occupancy uncertainty
- **Extended by**: Contribution 24 (NeRF uncertainty) for exploration
