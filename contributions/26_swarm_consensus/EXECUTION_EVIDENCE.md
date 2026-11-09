# C26 — executed synthetic experiment and reproducibility limits

The registered `c26_swarm_consensus` experimental runner was **actually executed and passed** in [GitHub Actions #42702357587](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42702357587). This is **controlled synthetic or proxy evidence**, not proof of a trained production model or physical robot.

## Research question

Trust-aware robust consensus maintains agreement and mission success under Byzantine participants better than unweighted aggregation.

## Reproduction

```bash
python scripts/run_contribution_suite.py --only C26 --fail-on-skip --output-dir results/contribution_audit/C26
```

Original entry point: `contributions/26_swarm_consensus/experiments/eval_swarm_consensus.py`.

Generated outputs are a nonempty benchmark CSV, `manifest.json`, `summary.md`, logged environment/command, row count and content SHA-256. The [C02–C26 full audit workflow](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/c02-c26-exhaustive.yml) runs every contribution separately and includes its tracked Python scripts, data, models, plots and docs in the file-by-file SHA-256 manifest.

## Required baselines and primary metrics

- Baselines: [Mean consensus, Median consensus].
- Metrics: [consensus_accuracy, mission_success, byzantine_detection_recall, communication_messages, trust_weighted_agreement].
- **Recorded evidence level:** synthetic.
- **Explicit limitation:** In-process simulation does not model real network delays, packet ordering, or ROS 2 DDS failure modes.

## Scientific validation still required

Independent actual input datasets, disjoint training and evaluation sites, multiple seeds, error bars, ablations, validated model weights, externally comparable baselines, and (where relevant) physical ROS 2 integration are separate experiments. Synthetic policy curves are not PPO training, 2D mapping proxies are not trained 3D Gaussian Splatting/NeRF, and in-process multi-robot agents are not real DDS-connected robots. No physical robot controlled by C26 was connected or verified. **Verified physical C26 navigation experiments: 0.**
