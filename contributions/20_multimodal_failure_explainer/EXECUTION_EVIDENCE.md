# C20 — reproducible experiment and claim boundaries

**Evidence:** The registered `c20_failure_report_quality` synthetic benchmark **executed successfully** in [run #42702357587](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42702357587). This is real software execution, not hardware or scientific generalization evidence.

## Hypothesis

Structured multimodal failure reports increase root-cause coverage and operator-action relevance over minimal event summaries.

## Exact command and original source

```bash
python scripts/run_contribution_suite.py --only C20 --fail-on-skip --output-dir results/contribution_audit/C20
```

Entry point: `contributions/20_multimodal_failure_explainer/experiments/eval_failure_report_quality.py`.

Independent per-contribution outputs include `manifest.json`, `summary.md`, a nonempty CSV and SHA-256; the [C02–C26 workflow](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/c02-c26-exhaustive.yml) and its artifact `c02-c26-per-file-and-per-contribution-execution` preserve all 25 reports. The file-level auditor additionally inspects each source script, binary model, data file, plot and document in this contribution.

## Baselines and metrics

- **Baselines:** [Minimal event summary].
- **Primary metrics:** [completeness_score, root_cause_recall, action_relevance, stl_coverage, operator_readiness, total_score].
- **Evidence level:** synthetic.
- **Specific research limitation:** Automated rubric scores are not a substitute for blinded operator studies.

## Not established

A successful controlled runner does not prove trained-model performance, held-out site generalization, robust actual sensor inputs, real ROS 2 integration, robot-controller safety, formal mathematical proof, or real physical-robot navigation. These are separate experiments requiring actual available data/hardware and appropriate baselines, authenticated provenance and independent review. **Verified physical C20 trials: 0.**
