# C11 — reproducible experiment and claim boundaries

**Evidence:** The registered `c11_vlm_goal_validation` synthetic benchmark **executed successfully** in [run #42702357587](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42702357587). This is real software execution, not hardware or scientific generalization evidence.

## Hypothesis

A deterministic safety validator rejects low-confidence, malformed, or out-of-bounds VLM goals before metric planning.

## Exact command and original source

```bash
python scripts/run_contribution_suite.py --only C11 --fail-on-skip --output-dir results/contribution_audit/C11
```

Entry point: `contributions/11_vlm_navigation_agent/experiments/eval_vlm_goal_validation.py`.

Independent per-contribution outputs include `manifest.json`, `summary.md`, a nonempty CSV and SHA-256; the [C02–C26 workflow](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/c02-c26-exhaustive.yml) and its artifact `c02-c26-per-file-and-per-contribution-execution` preserve all 25 reports. The file-level auditor additionally inspects each source script, binary model, data file, plot and document in this contribution.

## Baselines and metrics

- **Baselines:** [Unvalidated VLM output].
- **Primary metrics:** [decision, valid_confidence, valid_region, valid_pixel, valid_waypoint, reason].
- **Evidence level:** synthetic.
- **Specific research limitation:** This validates structured outputs only; it does not call or benchmark a real vision-language model.

## Not established

A successful controlled runner does not prove trained-model performance, held-out site generalization, robust actual sensor inputs, real ROS 2 integration, robot-controller safety, formal mathematical proof, or real physical-robot navigation. These are separate experiments requiring actual available data/hardware and appropriate baselines, authenticated provenance and independent review. **Verified physical C11 trials: 0.**
