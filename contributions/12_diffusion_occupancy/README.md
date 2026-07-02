# Contribution 12 — Diffusion Occupancy Maps and Probabilistic Risk Evaluation

[![Module](https://img.shields.io/badge/Module-12-purple)](.) [![Type](https://img.shields.io/badge/Type-Probabilistic%20Planning-blue)](.) [![Status](https://img.shields.io/badge/Status-Core%20Upgraded-brightgreen)](.)

## Plain-language summary

A deterministic occupancy grid gives the robot one guess about the future.

A probabilistic occupancy model gives the robot multiple plausible futures.

Contribution 12 uses diffusion-style sampling to generate a distribution over future occupancy maps. From this ensemble, the planner can compute conservative risk maps such as CVaR-95 and avoid areas that may become occupied under plausible future scenarios.

The upgraded version adds evaluation metrics for the quality of the predicted risk maps.

The key idea is:

> A probabilistic map should be judged not only by whether it looks plausible, but by whether its probabilities match future occupancy outcomes.

---

## Research Question

> **RQ12:** Can diffusion-style occupancy prediction improve risk estimation for navigation compared with deterministic occupancy prediction?

This contribution studies:

- future occupancy prediction,
- generative sampling,
- ensemble uncertainty,
- CVaR risk maps,
- probabilistic calibration,
- high-risk detection,
- risk-map scoring rules.

---

## Conceptual Pipeline

```text
occupancy history
      ↓
diffusion-style sampling
      ↓
future occupancy ensemble
      ↓
mean / std / CVaR risk maps
      ↓
risk-weighted planner
      ↓
risk-map quality evaluation
```

---

## Existing Predictor

The existing `DiffusionOccupancyPredictor` generates multiple future occupancy samples and returns:

```text
{
    "mean": mean occupancy probability,
    "std": ensemble uncertainty,
    "cvar_95": conservative tail-risk map,
    "samples": sampled future occupancy maps
}
```

The planner can then compute a risk-weighted path cost using the CVaR map.

---

## New Upgrade Added

C12 now includes:

```text
risk_map_evaluator.py
```

This evaluates predicted risk maps using:

- Brier score,
- negative log likelihood,
- binary accuracy at threshold 0.5,
- high-risk precision,
- high-risk recall,
- CVaR conservatism gap,
- mean predicted risk,
- mean observed occupancy.

This makes the probabilistic claim measurable.

---

## Files

```text
12_diffusion_occupancy/
├── README.md
├── diffusion_occupancy.py
├── risk_map_evaluator.py
├── docs/
│   └── SCIENTIFIC_UPGRADE.md
├── experiments/
│   ├── eval_diffusion_occupancy.py
│   └── eval_risk_map_quality.py
└── results/
    ├── diffusion_eval.csv
    └── c12_risk_map_quality.csv
```

---

## Quick Start

Run the existing diffusion occupancy benchmark:

```bash
python contributions/12_diffusion_occupancy/experiments/eval_diffusion_occupancy.py \
    --n_scenarios 30 \
    --n_samples 10 \
    --out_csv contributions/12_diffusion_occupancy/results/diffusion_eval.csv
```

Run the new risk-map quality benchmark:

```bash
python contributions/12_diffusion_occupancy/experiments/eval_risk_map_quality.py
```

This generates:

```text
contributions/12_diffusion_occupancy/results/c12_risk_map_quality.csv
```

---

## Risk-Map Quality Metrics

| Metric | Meaning |
|---|---|
| Brier score | Mean squared error of predicted occupancy probabilities |
| Negative log likelihood | Penalizes confident wrong probabilities |
| Accuracy at 0.5 | Binary occupied/free accuracy after thresholding |
| High-risk precision | How many predicted high-risk cells were truly occupied |
| High-risk recall | How many truly occupied cells were captured as high risk |
| CVaR conservatism gap | Average CVaR risk minus average predicted risk |

---

## Scientific Contribution

The upgraded C12 contribution is not simply:

> Generate multiple occupancy maps.

It is stronger:

> Generate probabilistic occupancy maps and evaluate whether their predicted risk values match future occupancy outcomes using scoring rules and high-risk detection metrics.

This is necessary because a generative model can produce visually diverse samples without producing useful probabilities for planning.

---

## Integration

- **Feeds into:** C03 risk-aware planning through CVaR risk maps
- **Can trigger:** C05 safe mode if future occupancy risk rises
- **Supports:** C07 next-best-view exploration when future uncertainty affects viewpoint choice
- **Can combine with:** C24 NeRF uncertainty as an additional spatial prior
- **Should be calibrated with:** C02 uncertainty calibration methods

Recommended runtime interface:

```text
diffusion_output = {
    mean_risk_map,
    std_map,
    cvar_95_map,
    samples,
    quality_metrics
}
```

---

## Production Upgrade

The current implementation is intentionally lightweight and numpy-only.

A production model could replace the stub score network with a U-Net:

```python
from diffusers import UNet2DModel

score_net = UNet2DModel(
    sample_size=64,
    in_channels=1,
    out_channels=1,
)
```

The evaluation layer should remain, regardless of the model architecture.

---

## Limitations

- The current diffusion model is a lightweight stub, not a trained production diffusion model.
- The quality benchmark uses synthetic future occupancy outcomes for auditability.
- Real validation requires logged occupancy histories and future ground-truth occupancy.
- CVaR conservatism must be tuned; excessive conservatism can block useful paths.
- Probability calibration is not yet learned or post-calibrated.

---

## Next Research Step

The strongest extension is calibration-aware diffusion risk:

```text
sampled occupancy ensemble
      ↓
calibrated probability map
      ↓
CVaR planner input
```

This would connect C12 directly to C02 calibration and C03 risk-aware planning.

---

## Conclusion

Contribution 12 establishes the probabilistic future-occupancy layer of DynNav.

The upgraded version makes this layer scientifically stronger by evaluating whether predicted risk maps are probabilistically meaningful, not only visually plausible.
