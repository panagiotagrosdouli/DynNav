# C19 — reproducible experiment and claim boundaries

**Evidence:** The registered `c19_mission_plan_quality` synthetic benchmark **executed successfully** in [run #42702357587](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42702357587). This is real software execution, not hardware or scientific generalization evidence.

## Hypothesis

Schema-constrained mission planning improves waypoint order, constraint satisfaction, and execution readiness over unchecked language output.

## Exact command and original source

```bash
python scripts/run_contribution_suite.py --only C19 --fail-on-skip --output-dir results/contribution_audit/C19
```

Entry point: `contributions/19_llm_mission_planner/experiments/eval_mission_plan_quality.py`.

Independent per-contribution outputs include `manifest.json`, `summary.md`, a nonempty CSV and SHA-256; the [C02–C26 workflow](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/c02-c26-exhaustive.yml) and its artifact `c02-c26-per-file-and-per-contribution-execution` preserve all 25 reports. The file-level auditor additionally inspects each source script, binary model, data file, plot and document in this contribution.

## Baselines and metrics

- **Baselines:** [Unchecked mission sequence].
- **Primary metrics:** [ordering_accuracy, exact_sequence_match, unresolved_waypoints, forbidden_violations, execution_ready].
- **Evidence level:** synthetic.
- **Specific research limitation:** The benchmark uses deterministic fixtures and does not establish LLM reliability.

## Not established

A successful controlled runner does not prove trained-model performance, held-out site generalization, robust actual sensor inputs, real ROS 2 integration, robot-controller safety, formal mathematical proof, or real physical-robot navigation. These are separate experiments requiring actual available data/hardware and appropriate baselines, authenticated provenance and independent review. **Verified physical C19 trials: 0.**
