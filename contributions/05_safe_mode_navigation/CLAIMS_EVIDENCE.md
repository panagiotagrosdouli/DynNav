# C05 — Safe Mode Navigation

## Claim

Safe-mode navigation reduces operational risk by switching to a conservative navigation strategy when elevated risk is detected.

## Evidence

Benchmark source:

results/safe_mode_threshold_ablation_results.csv

Observed averages:

* Normal total risk: 1.2

* Safe-mode total risk: 0.4

* Risk reduction: 66.7%

* Normal maximum risk: 0.9

* Safe-mode maximum risk: 0.2

* Maximum-risk reduction: 77.8%

Trade-off:

* Distance increase: 263.6%
* Cost increase: 112.2%

## Interpretation

Safe mode consistently reduced both cumulative and peak risk exposure.

The reduction was achieved by selecting longer and more conservative trajectories.

## Supported Conclusion

Contribution 05 successfully demonstrates risk reduction through adaptive safe-mode behavior.

The mechanism should be interpreted as a safety-efficiency trade-off rather than a universally superior navigation policy.
