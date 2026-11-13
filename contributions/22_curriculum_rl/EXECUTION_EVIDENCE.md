# C22 — executed synthetic experiment and reproducibility limits

The registered `c22_curriculum_strategies` experimental runner was **actually executed and passed** in [GitHub Actions #42702357587](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42702357587). This is **controlled synthetic or proxy evidence**, not proof of a trained production model or physical robot.

## Research question

Adaptive curriculum schedules reach hard scenarios with better stability and sample efficiency than fixed difficulty schedules.

## Reproduction

```bash
python scripts/run_contribution_suite.py --only C22 --fail-on-skip --output-dir results/contribution_audit/C22
```

Original entry point: `contributions/22_curriculum_rl/experiments/eval_curriculum_strategies.py`.

Generated outputs are a nonempty benchmark CSV, `manifest.json`, `summary.md`, logged environment/command, row count and content SHA-256. The [C02–C26 full audit workflow](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/c02-c26-exhaustive.yml) runs every contribution separately and includes its tracked Python scripts, data, models, plots and docs in the file-by-file SHA-256 manifest.

## Required baselines and primary metrics

- Baselines: [Fixed curriculum, Linear curriculum].
- Metrics: [episodes_to_hard, success_trend, stability_score, heldout_transfer_success, sample_efficiency_score].
- **Recorded evidence level:** synthetic.
- **Explicit limitation:** Synthetic learning curves do not demonstrate sample efficiency for a trained navigation agent.

## Scientific validation still required

Independent actual input datasets, disjoint training and evaluation sites, multiple seeds, error bars, ablations, validated model weights, externally comparable baselines, and (where relevant) physical ROS 2 integration are separate experiments. Synthetic policy curves are not PPO training, 2D mapping proxies are not trained 3D Gaussian Splatting/NeRF, and in-process multi-robot agents are not real DDS-connected robots. No physical robot controlled by C22 was connected or verified. **Verified physical C22 navigation experiments: 0.**
