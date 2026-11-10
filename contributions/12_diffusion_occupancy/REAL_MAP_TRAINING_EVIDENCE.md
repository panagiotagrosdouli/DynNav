# C12 — Actual trained denoiser on physically mapped office geometry

**Date:** 2026-11-10. **Experiment verified:** [GitHub Actions #42789633619](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42789633619), 5 unit/regression tests passed, original source map SHA verified, training completed and checkpoint structurally inspected.

## What really ran

We acquired the original LILocBench ROS occupancy map of the real indoor office environment, with original archive SHA-256 `941f96bf90d7d89dddf76fb4864f45212318d39f2b4f1220318786e53f48f6b0`. The original map image SHA-256 was `8a9ff6aa0d954e7743ed7dd1801d9df2a44a4d023cfda8de6ef12daa39cd57bf`.

From the original static occupancy raster, 32×32 **non-overlapping spatial tiles** were created. The left geographic columns were allocated to training, a one-column gap was held out, and the right geographic columns used for evaluation. This yielded **558 training tiles** and **372 held-out testing tiles**. The training target is authentic physical-world static occupancy, whereas the partially observed conditioning image and noise in diffusion are **synthetically generated**. No images of moving people or ground-truth future obstacle motion are included.

An actual PyTorch three-layer convolutional noise-estimator network, rather than the repository's original untrained NumPy ScoreNetwork, was trained with a diffusion schedule for 2 epochs on CPU, seed 2026, and evaluated once on held-out spatial tiles. Checkpoint state tensors, code parameters, data source identities and the trial metrics were retained in `c12-realmap-static-denoiser.pt` within the workflow artifact (file name in code: `c12_realmap_static_denoiser.pt`).

## Genuine measured results

| Held-out measurement | Synthetic corrupted-observation baseline | Newly trained conditional denoiser |
|---|---:|---:|
| Brier score | 0.128327 | **0.095290** |
| Negative log likelihood | 0.824218 | **0.378362** |

Training noise-prediction MSE, per epoch: **0.619745** → **0.176102**. This confirms actual parameter training and better scoring than the chosen noisy observation baseline in this controlled single-seed study.

**Do not interpret the score improvement as physical robot navigation benefit, dynamic occupancy prediction or held-out-building generalization.** Both training and test regions came from different parts of the *same* physical-world map. Noise and occlusion are simulated. The assessment is about static occupancy restoration under synthetic corruptions; it is not a future-conditioned occupancy-movement model, a calibrated collision probability or learned ROS 2 navigation behavior. The test is single seed, two epochs and one domain.

## Fixes to pre-existing C12 proxy

The historical `diffusion_occupancy.py` uses untrained NumPy weights; this path remains a **synthetic proxy**, distinct from the new trained PyTorch model. Existing `predict_risk` now checks occupancy shape/range/finite values and requires a valid sampling configuration. Empirical per-cell CVaR at alpha 0.95 now uses **fractional upper-tail mass** rather than arbitrarily selecting one sample at small ensemble sizes; risk-weighted path costing refuses invalid map probabilities, negative risk weight and out-of-bounds cells rather than silently ignoring them. Five regression tests exercise these mathematical and safety invariants.

## Reproduction

```bash
python contributions/12_diffusion_occupancy/experiments/train_real_map_static_denoiser.py \
  /path/to/original/map_office.yaml \
  --output-dir results/c12_real_map_static \
  --epochs 2 --steps 20 --tile-size 32 --seed 2026
```

Dedicated CI: [`.github/workflows/c12-real-map-denoiser.yml`](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/c12-real-map-denoiser.yml).

The workflow downloads the original map, checks its SHA-256, executes tests, actual training and blind-tile evaluation, and uploads `report.json` plus actual PyTorch weights. The source occupancy image is not redistributed in the artifact.

## Still required for complete C12 validation

True synchronized occupancy histories and later ground-truth maps from independent physical scenes, trained conditional temporal diffusion model with explicitly tracked model weights and future-prediction horizons, matched baselines (constant velocity occupancy, Bayesian filtering, temporal CNN, a deterministic inflation model), proper calibration and navigation-mission safety metrics, and ROS 2 integration with actual future occupancy messages. For a hardware claim, a new physical robot must actually run the active C12 predictor with reviewed safety gating and authentic synchronized motion logs.

**Verified physical robot C12 navigation trials: zero.** Existing physical Dingo recordings and the earlier C01 simulated navigation do not demonstrate C12 was onboard.
