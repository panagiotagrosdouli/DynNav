# C12 — reproducible experiment and claim boundaries

**Evidence:** The registered `c12_risk_map_quality` synthetic benchmark **executed successfully** in [run #42702357587](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42702357587). This is real software execution, not hardware or scientific generalization evidence.

## Hypothesis

Probabilistic occupancy forecasts improve calibration and high-risk recall relative to deterministic persistence baselines.

## Exact command and original source

```bash
python scripts/run_contribution_suite.py --only C12 --fail-on-skip --output-dir results/contribution_audit/C12
```

Entry point: `contributions/12_diffusion_occupancy/experiments/eval_risk_map_quality.py`.

Independent per-contribution outputs include `manifest.json`, `summary.md`, a nonempty CSV and SHA-256; the [C02–C26 workflow](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/c02-c26-exhaustive.yml) and its artifact `c02-c26-per-file-and-per-contribution-execution` preserve all 25 reports. The file-level auditor additionally inspects each source script, binary model, data file, plot and document in this contribution.

## Baselines and metrics

- **Baselines:** [Deterministic persistence, Frequency forecast].
- **Primary metrics:** [brier_score, nll, high_risk_precision, high_risk_recall, cvar_conservatism_gap].
- **Evidence level:** synthetic.
- **Specific research limitation:** The lightweight predictor is a controlled proxy and not evidence for a trained diffusion model.

## Not established

A successful controlled runner does not prove trained-model performance, held-out site generalization, robust actual sensor inputs, real ROS 2 integration, robot-controller safety, formal mathematical proof, or real physical-robot navigation. These are separate experiments requiring actual available data/hardware and appropriate baselines, authenticated provenance and independent review. **Verified physical C12 trials: 0.**
