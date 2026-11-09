# C23 — executed synthetic experiment and reproducibility limits

The registered `c23_gaussian_mapping_quality` experimental runner was **actually executed and passed** in [GitHub Actions #42702357587](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42702357587). This is **controlled synthetic or proxy evidence**, not proof of a trained production model or physical robot.

## Research question

Incremental Gaussian-map proxies expose occupancy quality, uncertainty separation, and frontier utility as observations accumulate.

## Reproduction

```bash
python scripts/run_contribution_suite.py --only C23 --fail-on-skip --output-dir results/contribution_audit/C23
```

Original entry point: `contributions/23_gaussian_splatting_mapper/experiments/eval_gs_mapping_quality.py`.

Generated outputs are a nonempty benchmark CSV, `manifest.json`, `summary.md`, logged environment/command, row count and content SHA-256. The [C02–C26 full audit workflow](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/c02-c26-exhaustive.yml) runs every contribution separately and includes its tracked Python scripts, data, models, plots and docs in the file-by-file SHA-256 manifest.

## Required baselines and primary metrics

- Baselines: [Sparse occupancy proxy].
- Metrics: [occupancy_iou, occupancy_precision, occupancy_recall, uncertainty_unknown_gap, frontier_precision_proxy].
- **Recorded evidence level:** synthetic.
- **Explicit limitation:** This is a 2D Gaussian proxy, not photorealistic 3D Gaussian Splatting reconstruction.

## Scientific validation still required

Independent actual input datasets, disjoint training and evaluation sites, multiple seeds, error bars, ablations, validated model weights, externally comparable baselines, and (where relevant) physical ROS 2 integration are separate experiments. Synthetic policy curves are not PPO training, 2D mapping proxies are not trained 3D Gaussian Splatting/NeRF, and in-process multi-robot agents are not real DDS-connected robots. No physical robot controlled by C23 was connected or verified. **Verified physical C23 navigation experiments: 0.**
