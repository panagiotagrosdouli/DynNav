# C24 Scientific Upgrade Notes — NeRF Uncertainty Evaluation

## What was already strong

Contribution 24 already introduced an important mapping idea:

> Use NeRF rendering uncertainty as a proxy for spatial uncertainty and exploration priority.

The existing module includes:

- positional encoding,
- a lightweight TinyNeRF,
- MC-dropout uncertainty estimation,
- ray rendering,
- 2D uncertainty-map projection,
- conversion from uncertainty maps to exploration weights.

This is useful because radiance-field uncertainty can indicate where the robot has poor scene knowledge.

## Main weakness before this upgrade

The original module generated uncertainty maps, but did not evaluate whether those maps were useful.

A reviewer could ask:

> Is NeRF uncertainty calibrated as a risk signal?

or:

> Does uncertainty detect out-of-distribution / poorly observed regions?

or:

> Does uncertainty improve exploration or planning safety compared with a naive entropy baseline?

## New contribution added

C24 now includes:

```text
nerf_uncertainty_evaluator.py
experiments/eval_nerf_uncertainty.py
```

The new benchmark evaluates:

- Brier score,
- negative log likelihood,
- expected calibration error,
- OOD AUROC,
- novel-view uncertainty gap,
- exploration precision@k,
- planning safety gain proxy,
- mean uncertainty in known vs unknown regions.

## New benchmark

Run:

```bash
python contributions/24_nerf_uncertainty/experiments/eval_nerf_uncertainty.py
```

Output:

```text
contributions/24_nerf_uncertainty/results/c24_nerf_uncertainty.csv
```

The benchmark evaluates:

- nominal scene uncertainty,
- OOD view-shift uncertainty.

## Reviewer-safe claim

A stronger claim after this upgrade is:

> Contribution 24 evaluates NeRF-derived uncertainty as a navigation signal using calibration, OOD detection, novel-view uncertainty, exploration-priority, and planning-safety metrics.

## Relationship to other contributions

C24 connects directly to:

- C02 uncertainty calibration,
- C07 next-best-view exploration,
- C12 diffusion occupancy risk,
- C23 Gaussian Splatting mapping,
- C05 safe mode when scene uncertainty is high.

## Limitations

- The NeRF implementation is a lightweight numpy TinyNeRF, not a production neural renderer.
- The benchmark uses synthetic uncertainty/risk fields for reproducibility.
- Planning safety gain is a proxy based on path-risk costs, not real robot execution.
- Real validation requires posed RGB-D images, trained NeRF/instant-NGP/nerfstudio models, and held-out view rendering error.

## Next research step

The strongest extension is active NeRF mapping:

```text
NeRF uncertainty -> NBV target -> new image -> NeRF update -> uncertainty reduction
```

This would connect C24 directly with C07 and C23 in a closed-loop active perception system.
