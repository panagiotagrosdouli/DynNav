# Contribution 02: Uncertainty Calibration

## Claim

Contribution 02 introduces uncertainty estimation for learned heuristic predictions and evaluates whether predicted uncertainty correlates with actual prediction error.

## Evidence

Evaluation was performed on 25,235 planning states collected from 30 grid-world instances.

Observed metrics:

* Mean Absolute Error (MAE): 0.899
* Pearson correlation between uncertainty and absolute error: -0.050
* Spearman rank correlation between uncertainty and absolute error: 0.404

Coverage analysis:

* Coverage @ 1σ: 86.84%
* Coverage @ 2σ: 88.73%
* Coverage @ 3σ: 89.53%

## Interpretation

The uncertainty signal contains useful ranking information, as demonstrated by the positive Spearman correlation.

However, the variance estimates are not yet fully calibrated. Empirical coverage does not increase according to expected Gaussian confidence levels, indicating that the predicted standard deviations require additional calibration.

## Supported Conclusion

Contribution 02 successfully provides uncertainty-aware heuristic predictions and meaningful uncertainty ranking.

Contribution 02 does not yet provide fully calibrated probabilistic uncertainty estimates.

## Future Work

* Variance scaling
* Temperature calibration
* Conformal calibration
* Reliability-based post-processing
