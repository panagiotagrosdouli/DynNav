# Contribution Statistical Analysis

The canonical suite emitted 25 CSV files; C01 is skipped. Most rows are deterministic scenario variants, not independent samples from a target population. They do not justify inferential confidence intervals or population-level claims.

## Selected emitted observations

- **C02:** raw ECE 0.1701; global scaling 0.1496; quantile-bin calibration 0.1432. Empirical 1σ coverage fell from 0.690 to 0.480 for calibrated rows. Lower ECE alone does not establish interval calibration. `n=200`, synthetic, one seed.
- **C03:** the route remained the short risky option through λ=8. At λ=12, the balanced route had 69.5% lower CVaR and 11.4% longer path. Hand-authored candidates; no randomized evaluation.
- **C21:** fixture PPO and shielded PPO had 0 success; `greedy_goal` had 0.625 success and 0.375 collisions over 8 episodes. This contradicts any claim that the PPO label indicates successful trained policy evidence.
- **C22:** adaptive, fixed, reverse strategies all ended at easy stage with last success 0.525 and zero transitions; the fixture did not demonstrate curriculum progression.
- **C24:** synthetic AUROC was 1.0, while `safety_gain` was negative (-0.437 nominal; -0.717 OOD fixture). The runner does not train/render NeRF.
- **C25:** precision 1.0, recall 0.5, F1 0.667; scripted FGSM, PGD and odometry drift were missed. Preserve this negative result.
- **C26:** 12 in-process cases reported success; mean detection recall 0.465. No distributed network faults are modeled.

No registered smoke run here has multi-seed uncertainty intervals or held-out splits. Stronger comparisons need a predefined endpoint, paired/randomized scenario order, independent held-out topology, and confidence intervals. For binary success, use paired risk differences or appropriate clustered models; for latency/cost report distributions and robust intervals.
