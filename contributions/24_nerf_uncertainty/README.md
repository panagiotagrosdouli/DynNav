# Contribution 24 — NeRF Uncertainty Maps and Navigation Evaluation

[![Module](https://img.shields.io/badge/Module-24-purple)](.) [![Type](https://img.shields.io/badge/Type-3D%20Mapping%20%2F%20Uncertainty-blue)](.) [![Status](https://img.shields.io/badge/Status-Core%20Upgraded-brightgreen)](.)

## Plain-language summary

A NeRF can reconstruct how a scene looks, but for robot navigation the more important question is often:

```text
Where is the robot uncertain about the scene?
```

Contribution 24 uses NeRF-style rendering uncertainty as a spatial uncertainty signal. High uncertainty can indicate poorly observed, novel-view, or out-of-distribution regions that should be explored carefully.

The upgraded version adds evaluation metrics for whether NeRF uncertainty is useful as a navigation signal.

---

## Research Question

> **RQ24:** Does NeRF-derived uncertainty provide useful exploration and safety information beyond ordinary occupancy entropy or visual reconstruction alone?

This contribution studies:

- TinyNeRF-style radiance-field querying,
- MC-dropout uncertainty,
- ray-level uncertainty aggregation,
- 2D uncertainty projection,
- uncertainty-guided exploration weighting,
- uncertainty calibration,
- OOD / poorly observed region detection,
- planning-safety gain.

---

## Conceptual Pipeline

```text
camera poses
      ↓
ray casting through TinyNeRF
      ↓
MC-dropout density uncertainty
      ↓
2D uncertainty map
      ↓
exploration priority weights
      ↓
NBV target or risk-aware planner
      ↓
uncertainty-quality evaluation
```

---

## Existing Components

The original C24 implementation includes:

- `NeRFConfig`,
- `PositionalEncoder`,
- `TinyNeRF`,
- MC-dropout uncertainty sampling,
- `render_ray`,
- `NeRFUncertaintyMapper`,
- uncertainty-map construction from camera poses,
- conversion from uncertainty maps to exploration weights.

---

## New Upgrade Added

C24 now includes:

```text
nerf_uncertainty_evaluator.py
```

This evaluator measures:

- Brier score,
- negative log likelihood,
- expected calibration error,
- OOD AUROC,
- novel-view uncertainty gap,
- exploration precision@k,
- planning safety gain proxy,
- mean uncertainty in known and unknown regions.

---

## Files

```text
24_nerf_uncertainty/
├── README.md
├── nerf_uncertainty.py
├── nerf_uncertainty_evaluator.py
├── docs/
│   └── SCIENTIFIC_UPGRADE.md
├── experiments/
│   └── eval_nerf_uncertainty.py
└── results/
    └── c24_nerf_uncertainty.csv
```

---

## Quick Start

Build an uncertainty map:

```python
from contributions.24_nerf_uncertainty.nerf_uncertainty import NeRFUncertaintyMapper, NeRFConfig
import numpy as np

mapper = NeRFUncertaintyMapper(cfg=NeRFConfig(grid_size=(64, 64)))
poses = [np.eye(4) for _ in range(10)]
unc_map = mapper.build_uncertainty_map(poses)
weights = mapper.uncertainty_to_exploration_weights(unc_map, occupancy=None)
next_frontier = np.unravel_index(weights.argmax(), weights.shape)
print(next_frontier)
```

Run the new uncertainty-quality benchmark:

```bash
python contributions/24_nerf_uncertainty/experiments/eval_nerf_uncertainty.py
```

This generates:

```text
contributions/24_nerf_uncertainty/results/c24_nerf_uncertainty.csv
```

---

## Benchmark Scenarios

| Scenario | Purpose |
|---|---|
| `nominal_scene` | Tests uncertainty quality in a normal partially observed scene |
| `ood_view_shift` | Tests whether uncertainty rises under shifted / poorly observed view coverage |

---

## Evaluation Metrics

| Metric | Meaning |
|---|---|
| Brier score | Probability-quality score for uncertainty-as-risk |
| Negative log likelihood | Penalizes overconfident wrong uncertainty estimates |
| Expected calibration error | Measures mismatch between predicted uncertainty and observed risk frequency |
| OOD AUROC | Ability of uncertainty to detect unknown / poorly observed cells |
| Novel-view uncertainty gap | Difference between novel unknown and known-region uncertainty |
| Exploration precision@k | Fraction of top uncertainty cells that are genuinely unknown |
| Planning safety gain | Risk-path cost improvement compared with entropy-style baseline |
| Known/unknown mean uncertainty | Whether unknown regions are assigned higher uncertainty |

---

## Scientific Contribution

The upgraded C24 contribution is not simply:

> Build a NeRF uncertainty heatmap.

It is stronger:

> Evaluate NeRF uncertainty as a navigation signal using calibration, OOD detection, exploration-priority, novel-view, and planning-safety metrics.

This makes the module scientifically testable and connects radiance-field uncertainty to robot decision-making.

---

## Integration

- **Uses:** C02 uncertainty calibration ideas for reliability checking
- **Feeds into:** C07 next-best-view exploration through uncertainty-weighted frontier selection
- **Combines with:** C12 diffusion occupancy as a future-risk prior
- **Combines with:** C23 Gaussian Splatting maps for explicit 3D mapping
- **Can trigger:** C05 safe mode when uncertainty is high along the planned route

Recommended runtime interface:

```text
nerf_uncertainty_output = {
    uncertainty_map,
    exploration_weights,
    ood_score,
    calibration_metrics,
    planning_safety_gain
}
```

---

## Limitations

- The current NeRF implementation is a lightweight numpy TinyNeRF, not a production nerfstudio or instant-NGP model.
- The benchmark uses synthetic uncertainty and risk fields for reproducibility.
- Planning safety gain is a proxy based on grid path risk, not physical robot execution.
- Real validation requires posed image sequences, trained radiance fields, held-out novel views, and measured rendering errors.

---

## Next Research Step

The strongest extension is active NeRF mapping:

```text
NeRF uncertainty
      ↓
next-best-view target
      ↓
new RGB-D or RGB observation
      ↓
NeRF update
      ↓
uncertainty reduction and safer planning
```

This would connect C24 directly to C07 and C23 in a closed-loop active perception system.

---

## Conclusion

Contribution 24 establishes the NeRF uncertainty layer of DynNav.

The upgraded version makes the contribution stronger by evaluating whether NeRF-derived uncertainty is calibrated, OOD-sensitive, useful for exploration, and beneficial for planning safety.
