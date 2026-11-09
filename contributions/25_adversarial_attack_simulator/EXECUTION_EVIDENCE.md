# C25 — executed synthetic experiment and reproducibility limits

The registered `c25_attack_impact` experimental runner was **actually executed and passed** in [GitHub Actions #42702357587](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42702357587). This is **controlled synthetic or proxy evidence**, not proof of a trained production model or physical robot.

## Research question

Attack-specific impact scoring distinguishes geometry, odometry, and sensor degradation and selects proportionate mitigations.

## Reproduction

```bash
python scripts/run_contribution_suite.py --only C25 --fail-on-skip --output-dir results/contribution_audit/C25
```

Original entry point: `contributions/25_adversarial_attack_simulator/experiments/eval_attack_impact.py`.

Generated outputs are a nonempty benchmark CSV, `manifest.json`, `summary.md`, logged environment/command, row count and content SHA-256. The [C02–C26 full audit workflow](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/c02-c26-exhaustive.yml) runs every contribution separately and includes its tracked Python scripts, data, models, plots and docs in the file-by-file SHA-256 manifest.

## Required baselines and primary metrics

- Baselines: [No-attack scenario].
- Metrics: [detected, severity_score, min_distance_degradation, geometry_change, odometry_error_m, mitigation].
- **Recorded evidence level:** synthetic.
- **Explicit limitation:** Injected numerical attacks are not an end-to-end ROS 2 penetration test.

## Scientific validation still required

Independent actual input datasets, disjoint training and evaluation sites, multiple seeds, error bars, ablations, validated model weights, externally comparable baselines, and (where relevant) physical ROS 2 integration are separate experiments. Synthetic policy curves are not PPO training, 2D mapping proxies are not trained 3D Gaussian Splatting/NeRF, and in-process multi-robot agents are not real DDS-connected robots. No physical robot controlled by C25 was connected or verified. **Verified physical C25 navigation experiments: 0.**
