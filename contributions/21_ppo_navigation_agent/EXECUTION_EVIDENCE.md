# C21 — executed synthetic experiment and reproducibility limits

The registered `c21_policy_safety` experimental runner was **actually executed and passed** in [GitHub Actions #42702357587](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42702357587). This is **controlled synthetic or proxy evidence**, not proof of a trained production model or physical robot.

## Research question

Policy-level safety evaluation reveals reward-safety trade-offs that aggregate return alone would conceal.

## Reproduction

```bash
python scripts/run_contribution_suite.py --only C21 --fail-on-skip --output-dir results/contribution_audit/C21
```

Original entry point: `contributions/21_ppo_navigation_agent/experiments/eval_policy_safety.py`.

Generated outputs are a nonempty benchmark CSV, `manifest.json`, `summary.md`, logged environment/command, row count and content SHA-256. The [C02–C26 full audit workflow](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/c02-c26-exhaustive.yml) runs every contribution separately and includes its tracked Python scripts, data, models, plots and docs in the file-by-file SHA-256 manifest.

## Required baselines and primary metrics

- Baselines: [Unshielded policy, Heuristic policy].
- Metrics: [success_rate, collision_rate, mean_reward, mean_min_obstacle_distance, shield_intervention_rate].
- **Recorded evidence level:** synthetic.
- **Explicit limitation:** The policies and environment are lightweight fixtures, not trained PPO deployment evidence.

## Scientific validation still required

Independent actual input datasets, disjoint training and evaluation sites, multiple seeds, error bars, ablations, validated model weights, externally comparable baselines, and (where relevant) physical ROS 2 integration are separate experiments. Synthetic policy curves are not PPO training, 2D mapping proxies are not trained 3D Gaussian Splatting/NeRF, and in-process multi-robot agents are not real DDS-connected robots. No physical robot controlled by C21 was connected or verified. **Verified physical C21 navigation experiments: 0.**
