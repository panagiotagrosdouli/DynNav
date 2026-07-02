# C12 Scientific Upgrade Notes — Probabilistic Risk-Map Quality

## What was already strong

Contribution 12 already introduced a forward-looking idea:

> Use diffusion-style generative sampling to produce a distribution over possible future occupancy maps, then derive conservative risk maps for planning.

The existing module includes:

- diffusion-style occupancy sampling,
- ensemble mean and standard deviation maps,
- CVaR-95 risk maps,
- risk-weighted path cost.

This is important because deterministic occupancy prediction hides uncertainty.

## Main weakness before this upgrade

A probabilistic risk map is only useful if the probabilities are meaningful.

A reviewer could ask:

> Is the predicted occupancy distribution calibrated or only visually plausible?

or:

> Does the CVaR map improve risk estimation, or does it simply inflate everything?

## New contribution added

C12 now includes:

```text
risk_map_evaluator.py
experiments/eval_risk_map_quality.py
```

The new evaluator reports:

- Brier score,
- negative log likelihood,
- binary accuracy at threshold 0.5,
- high-risk precision,
- high-risk recall,
- CVaR conservatism gap,
- mean predicted risk,
- mean observed occupancy.

## New benchmark

Run:

```bash
python contributions/12_diffusion_occupancy/experiments/eval_risk_map_quality.py
```

Output:

```text
contributions/12_diffusion_occupancy/results/c12_risk_map_quality.csv
```

The benchmark compares deterministic and probabilistic risk maps against synthetic future occupancy outcomes.

## Reviewer-safe claim

A stronger claim after this upgrade is:

> Contribution 12 evaluates probabilistic occupancy risk maps using proper scoring rules and high-risk detection metrics, rather than relying only on visual samples or path-cost changes.

## Relationship to other contributions

C12 connects directly to:

- C03 risk-aware planning through CVaR risk maps,
- C05 safe mode when predicted future occupancy risk rises,
- C07 next-best-view exploration when future occupancy uncertainty affects viewpoint choice,
- C24 NeRF uncertainty as an additional spatial prior.

## Limitations

- The diffusion model is a lightweight numpy stub, not a trained production U-Net.
- The benchmark uses synthetic future occupancy for auditability.
- Proper real-world validation requires logged occupancy histories and future ground truth.
- CVaR conservatism must be tuned: too little misses hazards, too much blocks feasible paths.

## Next research step

The strongest extension is calibration-aware diffusion risk:

```text
sampled occupancy ensemble -> calibrated probability map -> CVaR planner input
```

This would connect C12 more tightly with C02 uncertainty calibration and C03 risk-aware planning.
