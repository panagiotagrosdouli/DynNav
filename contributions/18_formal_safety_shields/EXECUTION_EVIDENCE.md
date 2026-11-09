# C18 — reproducible experiment and claim boundaries

**Evidence:** The registered `c18_shield_stress_test` synthetic benchmark **executed successfully** in [run #42702357587](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42702357587). This is real software execution, not hardware or scientific generalization evidence.

## Hypothesis

Runtime shielding reduces safety violations and minimum-distance breaches relative to unshielded control under matched scenarios.

## Exact command and original source

```bash
python scripts/run_contribution_suite.py --only C18 --fail-on-skip --output-dir results/contribution_audit/C18
```

Entry point: `contributions/18_formal_safety_shields/experiments/eval_shield_stress_test.py`.

Independent per-contribution outputs include `manifest.json`, `summary.md`, a nonempty CSV and SHA-256; the [C02–C26 workflow](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/c02-c26-exhaustive.yml) and its artifact `c02-c26-per-file-and-per-contribution-execution` preserve all 25 reports. The file-level auditor additionally inspects each source script, binary model, data file, plot and document in this contribution.

## Baselines and metrics

- **Baselines:** [Unshielded controller].
- **Primary metrics:** [safety_violations, min_obstacle_distance, min_stl_robustness, intervention_rate, final_goal_distance].
- **Evidence level:** synthetic.
- **Specific research limitation:** Numerical stress tests are not a formal proof and do not cover full robot dynamics.

## Not established

A successful controlled runner does not prove trained-model performance, held-out site generalization, robust actual sensor inputs, real ROS 2 integration, robot-controller safety, formal mathematical proof, or real physical-robot navigation. These are separate experiments requiring actual available data/hardware and appropriate baselines, authenticated provenance and independent review. **Verified physical C18 trials: 0.**
