# C13 — reproducible experiment and claim boundaries

**Evidence:** The registered `c13_rollout_audit` synthetic benchmark **executed successfully** in [run #42702357587](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42702357587). This is real software execution, not hardware or scientific generalization evidence.

## Hypothesis

Latent rollout auditing selects action sequences that balance predicted return with effort and recoverability penalties.

## Exact command and original source

```bash
python scripts/run_contribution_suite.py --only C13 --fail-on-skip --output-dir results/contribution_audit/C13
```

Entry point: `contributions/13_latent_world_model/experiments/eval_rollout_audit.py`.

Independent per-contribution outputs include `manifest.json`, `summary.md`, a nonempty CSV and SHA-256; the [C02–C26 workflow](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/c02-c26-exhaustive.yml) and its artifact `c02-c26-per-file-and-per-contribution-execution` preserve all 25 reports. The file-level auditor additionally inspects each source script, binary model, data file, plot and document in this contribution.

## Baselines and metrics

- **Baselines:** [Return-only rollout ranking].
- **Primary metrics:** [imagined_return, action_effort, terminal_latent_norm, recoverability_proxy, irreversible, final_score].
- **Evidence level:** synthetic.
- **Specific research limitation:** The latent dynamics are untrained fixtures and cannot support world-model accuracy claims.

## Not established

A successful controlled runner does not prove trained-model performance, held-out site generalization, robust actual sensor inputs, real ROS 2 integration, robot-controller safety, formal mathematical proof, or real physical-robot navigation. These are separate experiments requiring actual available data/hardware and appropriate baselines, authenticated provenance and independent review. **Verified physical C13 trials: 0.**
