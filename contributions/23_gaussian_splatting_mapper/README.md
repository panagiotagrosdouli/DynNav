# Contribution 23 — Gaussian Splatting Mapper and Navigation-Map Evaluation

[![Module](https://img.shields.io/badge/Module-23-purple)](.) [![Type](https://img.shields.io/badge/Type-3D%20Mapping-blue)](.) [![Status](https://img.shields.io/badge/Status-Core%20Upgraded-brightgreen)](.)

## Plain-language summary

A 2D occupancy grid is useful for planning, but it can hide the 3D structure and uncertainty of the scene.

Contribution 23 builds an incremental 3D Gaussian Splatting-style map from RGB-D / point-cloud observations. Each Gaussian represents a local scene element with:

- 3D position,
- covariance / shape,
- opacity,
- colour,
- confidence.

The upgraded version adds a mapping-quality benchmark:

> The Gaussian map is evaluated as a navigation map using occupancy accuracy, uncertainty usefulness, frontier quality, and representation efficiency.

---

## Research Question

> **RQ23:** Does a Gaussian-Splatting-style 3D map provide useful occupancy, uncertainty, and frontier information for navigation compared with a simple 2D occupancy representation?

This contribution studies:

- incremental 3D Gaussian map updates,
- Gaussian merging and pruning,
- confidence decay,
- occupancy projection,
- uncertainty maps,
- frontier detection,
- mapping-quality evaluation.

---

## Conceptual Pipeline

```text
RGB-D / point cloud frames
      ↓
add or merge 3D Gaussians
      ↓
confidence decay and pruning
      ↓
project to 2D occupancy grid
      ↓
compute uncertainty map and frontiers
      ↓
planner or NBV exploration module
```

---

## Existing Components

The original C23 implementation includes:

- `Gaussian3D`,
- `GSMapConfig`,
- `GaussianSplattingMap`,
- Mahalanobis-distance merging,
- confidence decay,
- low-confidence pruning,
- 2D occupancy extraction,
- uncertainty-map extraction,
- frontier-cell detection.

---

## New Upgrade Added

C23 now includes:

```text
gs_mapping_evaluator.py
```

This evaluator measures:

- occupancy IoU,
- occupancy precision,
- occupancy recall,
- uncertainty unknown gap,
- frontier count,
- frontier precision proxy,
- Gaussians per observed cell.

---

## Files

```text
23_gaussian_splatting_mapper/
├── README.md
├── gaussian_splatting_map.py
├── gs_mapping_evaluator.py
├── docs/
│   └── SCIENTIFIC_UPGRADE.md
├── experiments/
│   └── eval_gs_mapping_quality.py
└── results/
    └── c23_gs_mapping_quality.csv
```

---

## Quick Start

Create a Gaussian map from synthetic points:

```python
from contributions.23_gaussian_splatting_mapper.gaussian_splatting_map import GaussianSplattingMap
import numpy as np

gsmap = GaussianSplattingMap()

for i in range(20):
    points = np.random.rand(50, 3)
    points[:, 2] = 0.5
    gsmap.add_frame(points)

occ_grid = gsmap.to_occupancy_grid()
unc_map = gsmap.uncertainty_map()
frontiers = gsmap.frontier_cells()
print(gsmap.stats())
```

Run the new mapping-quality benchmark:

```bash
python contributions/23_gaussian_splatting_mapper/experiments/eval_gs_mapping_quality.py
```

This generates:

```text
contributions/23_gaussian_splatting_mapper/results/c23_gs_mapping_quality.csv
```

---

## Mapping Quality Metrics

| Metric | Meaning |
|---|---|
| Occupancy IoU | Overlap between projected occupancy and synthetic ground truth |
| Occupancy precision | Fraction of predicted occupied cells that are correct |
| Occupancy recall | Fraction of true occupied cells recovered by projection |
| Uncertainty unknown gap | Whether unknown cells have higher uncertainty than known occupied cells |
| Frontier count | Number of detected exploration frontier cells |
| Frontier precision proxy | Fraction of frontiers located in non-occupied cells |
| Gaussians per observed cell | Representation-efficiency proxy |

---

## Scientific Contribution

The upgraded C23 contribution is not simply:

> Store 3D Gaussians and project them to a grid.

It is stronger:

> Evaluate whether the Gaussian map produces useful navigation layers: occupancy, uncertainty, and frontiers.

This makes the mapping contribution measurable.

---

## Integration

- **Feeds into:** C03 risk-aware planning through occupancy projection
- **Feeds into:** C07 next-best-view exploration through frontier detection
- **Can combine with:** C12 diffusion occupancy for predicted future occupancy
- **Can combine with:** C24 NeRF uncertainty for implicit-scene uncertainty
- **Can trigger:** C05 safe mode when map uncertainty rises

Recommended runtime interface:

```text
gs_mapping_output = {
    gaussian_primitives,
    occupancy_grid,
    uncertainty_map,
    frontier_cells,
    mapping_quality_metrics
}
```

---

## Limitations

- This is a lightweight numpy abstraction, not a production 3DGS renderer.
- The benchmark uses synthetic point clouds and synthetic ground truth.
- Frontier precision is a proxy, not a direct information-gain measurement.
- Real deployment requires RGB-D calibration, pose tracking, loop closure, and dynamic-scene handling.

---

## Next Research Step

The strongest extension is uncertainty-aware active mapping:

```text
Gaussian map uncertainty + frontier quality
      ↓
next-best-view target
      ↓
new RGB-D frame
      ↓
map update and uncertainty reduction
```

This would connect C23 directly to C07 and C24.

---

## Conclusion

Contribution 23 establishes the Gaussian-splatting-style mapping layer of DynNav.

The upgraded version makes the module stronger by evaluating the navigation usefulness of the projected occupancy, uncertainty, and frontier layers.
