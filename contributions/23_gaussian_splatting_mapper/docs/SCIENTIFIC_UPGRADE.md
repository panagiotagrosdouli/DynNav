# C23 Scientific Upgrade Notes — Gaussian-Splatting Mapping Quality

## What was already strong

Contribution 23 already introduced a 3D mapping direction for DynNav:

> Incrementally represent RGB-D observations as 3D Gaussian primitives, then project the map into navigation-ready occupancy and uncertainty layers.

The existing module includes:

- `Gaussian3D` primitives,
- incremental frame integration,
- Mahalanobis-based merging,
- confidence decay and pruning,
- 2D occupancy projection,
- uncertainty maps,
- frontier extraction.

This is valuable because navigation can benefit from richer 3D structure while still using 2D planner interfaces.

## Main weakness before this upgrade

The original module could build and project a Gaussian map, but did not evaluate map quality.

A reviewer could ask:

> Does the projected occupancy grid match ground truth?

or:

> Does the uncertainty map actually distinguish known and unknown regions?

or:

> Are frontiers useful for exploration?

## New contribution added

C23 now includes:

```text
gs_mapping_evaluator.py
experiments/eval_gs_mapping_quality.py
```

The new benchmark evaluates:

- occupancy IoU,
- occupancy precision,
- occupancy recall,
- uncertainty unknown gap,
- frontier count,
- frontier precision proxy,
- Gaussians per observed cell.

## New benchmark

Run:

```bash
python contributions/23_gaussian_splatting_mapper/experiments/eval_gs_mapping_quality.py
```

Output:

```text
contributions/23_gaussian_splatting_mapper/results/c23_gs_mapping_quality.csv
```

The benchmark evaluates:

- empty room mapping,
- cluttered room mapping.

## Reviewer-safe claim

A stronger claim after this upgrade is:

> Contribution 23 evaluates Gaussian-splatting maps as navigation maps using occupancy accuracy, uncertainty separation, frontier quality, and representation-efficiency metrics.

## Relationship to other contributions

C23 connects directly to:

- C03 risk-aware planning through occupancy/risk projection,
- C07 next-best-view exploration through frontier detection,
- C12 diffusion occupancy as a future-risk layer,
- C24 NeRF uncertainty as a complementary implicit map.

## Limitations

- The mapper is a lightweight numpy abstraction, not a production 3D Gaussian Splatting renderer.
- The benchmark uses synthetic point clouds and synthetic ground truth.
- Frontier precision is a proxy and should be validated against real exploration gain.
- Real deployment requires RGB-D calibration, pose tracking, loop closure, and dynamic-scene handling.

## Next research step

The strongest extension is uncertainty-aware active mapping:

```text
Gaussian map uncertainty + frontier quality -> NBV target -> new RGB-D frame -> map update
```

This would connect C23 directly to C07 and C24.
