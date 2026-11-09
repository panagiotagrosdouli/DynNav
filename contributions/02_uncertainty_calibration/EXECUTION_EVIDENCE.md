# C02 — executable evidence and honest validation boundary

**Status:** One actual registered **synthetic** experiment executed and passed in [GitHub Actions run #42702357587](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42702357587). This does not mean the scientific hypothesis, all historical scripts or a physical robot have been fully validated.

## Registered hypothesis

Post-hoc calibration improves absolute-error calibration and empirical interval coverage relative to raw uncertainty estimates.

## Exact executable experiment

Experiment ID: `c02_uncertainty_calibration`. Source: `contributions/02_uncertainty_calibration/experiments/eval_uncertainty_calibration.py`.

```bash
python scripts/run_contribution_suite.py --only C02 --fail-on-skip --output-dir results/contribution_audit/C02
```

The runner produces `manifest.json`, `summary.md` and a non-empty experimental CSV with content SHA-256. The joint [C02–C26 workflow](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/c02-c26-exhaustive.yml) runs the 25 modules **one by one** and retains independent artifacts for each.

## Baselines, primary metrics and boundaries

- **Baselines:** [Raw uncertainty, Affine calibration].
- **Registered metrics:** [ece_abs_error, coverage_1sigma, coverage_2sigma, pearson_uncertainty_error, spearman_uncertainty_error].
- **Evidence level:** `synthetic`.
- **Specific limitation:** The default generator is synthetic and cannot establish calibration under sensor drift or domain shift.

Full C02–C26 file-level integrity (SHA-256, AST compile, archived CSV/NPZ/PyTorch/PNG/SVG checks) is tracked in `scripts/audit_contributions_c02_c26.py` and reported in the CI artifact `c02-c26-per-file-and-per-contribution-execution`. Structural file checks do **not** mean all historic experiments, saved weights, training or physical-world claims have been reproduced.

## Additional held-out archived-data study
The independent C02 analysis ran on actual archived *generated grid-world samples*: 18 grid instance IDs used to fit calibration, 12 held out. ECE-style absolute-error metric: raw 3.13473, global 0.60325, quantile-bin 0.52399. Coverage at 1 sigma was 0.89631 raw, 0.50359 global and 0.54413 quantile-bin; lower ECE does **not** prove valid Gaussian confidence intervals. This is NOT physical sensor data. Source: [successful run #42702357587](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42702357587).

## What is still required for stronger scientific or hardware claims

Independently validate the data source and separation of training/calibration and held-out maps or sites; run appropriate real sensor/robot recordings where the algorithm actually consumes those observations; preserve failures and independently checked baseline measurements; and attach provenance (code commit, dataset hashes, fixed seeds, time, hardware and software). For claims about actual **onboard physical-robot execution**, obtain a new supervised ROS 2/Nav2 integration run on a named robot with an emergency stop, true synchronized motion/planner logs and explicit proof that this contribution was active.

**Physical robot C02 execution verified by this CI: 0 trials.** A synthetic fixture, historical bag playback, neural checkpoint file or ROS service success must never be relabelled as a physical-robot result.
