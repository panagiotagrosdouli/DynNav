# C02 — Independent held-out map calibration, actual training and scientific audit

**Date:** 2026-11-09. **Evidence:** Archived neural uncertainty-error observations from generated 32x32 grid-world planning instances. No physical robot or physical localization ground-truth data are used.

## Verified executable evidence

[GitHub Actions run #42705974799](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42705974799) **passed**. It executed actual C02-specific tests; validated the original C02 files and saved nested-metadata PyTorch checkpoints; retrained the C02 drift uncertainty neural model for two epochs using its archived drift data and training-only normalization; ran the existing synthetic and archived group-split experiments; and ran a new 10-seed, three-way disjoint-map calibration study. Newly trained weights and normalization statistics were emitted as CI artifacts rather than overwriting the historical files.

### Independence / leakage controls

The 30 archived grid instances were partitioned **at the map-instance level**, never by randomly sampling neighboring cells within one map. Each seed independently shuffled the group IDs into approximately 50% fitting maps, 25% quantile calibration maps, and the remaining held-out evaluation maps. The fitting, calibration and evaluation groups do not overlap. The map-state samples are correlated within groups; **this is not a formal groupwise conformal coverage guarantee**.

For each method the absolute-error ratio to predicted uncertainty was calibrated using the finite-sample empirical quantile on the calibration subset. The held-out map instances were not used to choose the quantile.

### Ten-seed results (archived generated grid worlds)

| Method | Target empirical coverage | Mean held-out coverage | Min held-out coverage | Max held-out coverage | Mean interval half-width |
|---|---:|---:|---:|---:|---:|
| Raw uncertainty + conformal threshold | 90% | 91.410% | 88.651% | 95.177% | 15.603 units |
| Global magnitude scaling + conformal threshold | 90% | 91.417% | 88.651% | 95.177% | 15.603 units |

**Scientific interpretation:** Global positive multiplicative scaling cancels under independently re-estimated standardized-residual conformal thresholding, except for negligible rounding differences. Therefore nearly identical final interval widths and coverages here are expected and should not be represented as an effective improvement. Some seed-level held-out maps have coverage below the target; robust guarantee across independent map domains is not proven. These are scalar heuristic-error units, not localization meters or physical collision probabilities.

### Additional C02 engineering work

The historic `code/train_drift_uncertainty_net.py` calculated normalization statistics over all training **and validation** samples before the split. This leaks validation distribution into optimization. The revised training path selects reproducible indices first and computes all input and target normalizers **on training indices only**. New tests include a deliberately extreme held-out validation sample and a real one-epoch network training/checkpoint roundtrip. The fixed training job runs two epochs, preserving output model/state normalizer artifacts in GitHub Actions.

The new `experiments/eval_three_way_group_coverage.py` logs each split's map IDs, calibration multipliers, coverage and interval widths. The `tests/test_three_way_group_coverage.py` suite explicitly rejects map overlap and non-finite quantiles.

## Reproduction

```bash
python contributions/02_uncertainty_calibration/experiments/eval_three_way_group_coverage.py \
  --alpha 0.1 --seeds 10 \
  --output results/c02_deep_validation/three_way_10_seeds.json
```

```bash
python contributions/02_uncertainty_calibration/code/train_drift_uncertainty_net.py \
  --csv contributions/02_uncertainty_calibration/results/drift_dataset.csv \
  --epochs 2 --seed 2026 \
  --model-out results/c02_deep_validation/c02_retrained_2epochs.pt \
  --stats-out results/c02_deep_validation/c02_trainonly_norm.npz
```

Run the dedicated [C02 deep-validation workflow](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/c02-deep-validation.yml) to obtain all original and new C02 artifacts. Previous verified C02 baseline results in [run #42703777158](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42703777158) include ECE-style (raw 3.13473, global scale 0.60325, quantile 0.52399), but the respective empirical 1σ coverages (89.631%, 50.359%, 54.413%) explicitly indicate that a lower mean-sigma-vs-mean-error calibration metric does not ensure correct Gaussian intervals.

## Actual ROS 2 Jazzy topic-integration evidence

[Successful GitHub Actions run #42706526701](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42706526701) executed a genuine ROS 2 Jazzy DDS pub/sub sequence, `/c02/archived_grid_calibration`, with two separate rclpy nodes. It published **120** held-out archived uncertainty observations and **received all 120** in another ROS 2 node. The received values matched the source exactly (within 1e-12); the subscriber computed 95.0% sample coverage for those 120 messages, using a threshold estimated only on separate calibration maps (`q = 3.8305638550766425`).

This proves **real ROS 2 DDS message transmission and software-level uncertainty computation**, but the messages represent **generated grid-world archive values**, not actual Dingo LiDAR/Odometry, independent ground truth, robot localization or physical control. The ROS2 topic is read-only in the sense that no `/cmd_vel` or actuation topic was ever published. This separate 120-point replay result must not be confused with the 10-seed map-level calibration benchmark.

## What has NOT happened

No archived Dingo sensor bag supplies the ground-truth error/uncertainty triples needed to validate C02 directly. Merely reading ROS2 LiDAR/Odometry or running archived source trajectories through ROS2 does not validate calibrated localization uncertainty, physical robot control, or safety performance.

**Verified C02 physical robot navigation and uncertainty ground-truth trials: 0.**

Next scientific gates: a trusted real localization reference independent of the estimator (e.g. surveyed ground truth), independent robot/sensor sessions and sites, calibrated ROS2 diagnostics, coverage under drift and domain shifts, paired planning baselines, controlled physical trials and safety instrumentation.
