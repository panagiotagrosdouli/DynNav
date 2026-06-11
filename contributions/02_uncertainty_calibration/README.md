## Results

### Experimental Setup

The uncertainty model was evaluated on 25,235 states collected from 30 randomly generated grid-world planning instances.

For each state, the model produced:

* Predictive mean (`μ`)
* Predictive uncertainty (`σ`)

These predictions were compared against the true optimal cost-to-go (`h*`).

### Quantitative Results

| Metric                    |  Value |
| ------------------------- | -----: |
| Samples                   | 25,235 |
| Mean Absolute Error (MAE) |  0.899 |
| Pearson(σ, |error|)       | -0.050 |
| Spearman(σ, |error|)      |  0.404 |
| Coverage @ 1σ             | 86.84% |
| Coverage @ 2σ             | 88.73% |
| Coverage @ 3σ             | 89.53% |

### Interpretation

The uncertainty estimates exhibit a positive rank correlation with prediction error (Spearman = 0.404), indicating that higher predicted uncertainty generally corresponds to more difficult predictions.

However, the empirical coverage rates do not follow the expected Gaussian confidence behavior. Coverage remains relatively constant across 1σ, 2σ, and 3σ intervals, suggesting that the predicted variance is not yet properly calibrated.

The model therefore provides useful uncertainty ranking information but requires additional post-hoc calibration before uncertainty values can be interpreted as reliable confidence intervals.

