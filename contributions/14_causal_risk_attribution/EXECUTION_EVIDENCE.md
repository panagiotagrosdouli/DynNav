# C14 — reproducible experiment and claim boundaries

**Evidence:** The registered `c14_root_cause_attribution` synthetic benchmark **executed successfully** in [run #42702357587](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42702357587). This is real software execution, not hardware or scientific generalization evidence.

## Hypothesis

Counterfactual intervention ranking recovers the injected navigation failure cause more reliably than outcome magnitude alone.

## Exact command and original source

```bash
python scripts/run_contribution_suite.py --only C14 --fail-on-skip --output-dir results/contribution_audit/C14
```

Entry point: `contributions/14_causal_risk_attribution/experiments/eval_root_cause_attribution.py`.

Independent per-contribution outputs include `manifest.json`, `summary.md`, a nonempty CSV and SHA-256; the [C02–C26 workflow](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/c02-c26-exhaustive.yml) and its artifact `c02-c26-per-file-and-per-contribution-execution` preserve all 25 reports. The file-level auditor additionally inspects each source script, binary model, data file, plot and document in this contribution.

## Baselines and metrics

- **Baselines:** [Outcome-magnitude ranking].
- **Primary metrics:** [top1_correct, true_cause_rank, counterfactual_reduction, predicted_root_cause].
- **Evidence level:** synthetic.
- **Specific research limitation:** Correctness is relative to a hand-specified structural causal model.

## Not established

A successful controlled runner does not prove trained-model performance, held-out site generalization, robust actual sensor inputs, real ROS 2 integration, robot-controller safety, formal mathematical proof, or real physical-robot navigation. These are separate experiments requiring actual available data/hardware and appropriate baselines, authenticated provenance and independent review. **Verified physical C14 trials: 0.**
