# C24 — executed synthetic experiment and reproducibility limits

The registered `c24_nerf_uncertainty` experimental runner was **actually executed and passed** in [GitHub Actions #42702357587](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42702357587). This is **controlled synthetic or proxy evidence**, not proof of a trained production model or physical robot.

## Research question

Rendering-uncertainty proxies separate novel views from known space and improve risk-aware exploration decisions.

## Reproduction

```bash
python scripts/run_contribution_suite.py --only C24 --fail-on-skip --output-dir results/contribution_audit/C24
```

Original entry point: `contributions/24_nerf_uncertainty/experiments/eval_nerf_uncertainty.py`.

Generated outputs are a nonempty benchmark CSV, `manifest.json`, `summary.md`, logged environment/command, row count and content SHA-256. The [C02–C26 full audit workflow](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/c02-c26-exhaustive.yml) runs every contribution separately and includes its tracked Python scripts, data, models, plots and docs in the file-by-file SHA-256 manifest.

## Required baselines and primary metrics

- Baselines: [Uniform uncertainty, Uncertainty-agnostic planning].
- Metrics: [brier_score, ece, ood_auroc, novel_view_uncertainty_gap, exploration_precision_at_k, planning_safety_gain].
- **Recorded evidence level:** synthetic.
- **Explicit limitation:** The evaluator uses synthetic uncertainty fields and does not train or render a NeRF.

## Scientific validation still required

Independent actual input datasets, disjoint training and evaluation sites, multiple seeds, error bars, ablations, validated model weights, externally comparable baselines, and (where relevant) physical ROS 2 integration are separate experiments. Synthetic policy curves are not PPO training, 2D mapping proxies are not trained 3D Gaussian Splatting/NeRF, and in-process multi-robot agents are not real DDS-connected robots. No physical robot controlled by C24 was connected or verified. **Verified physical C24 navigation experiments: 0.**
