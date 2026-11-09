# C17 — reproducible experiment and claim boundaries

**Evidence:** The registered `c17_topological_semantic_navigation` synthetic benchmark **executed successfully** in [run #42702357587](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42702357587). This is real software execution, not hardware or scientific generalization evidence.

## Hypothesis

Sparse semantic grounding and edge invalidation support correct goal retrieval and route adaptation on a topological map.

## Exact command and original source

```bash
python scripts/run_contribution_suite.py --only C17 --fail-on-skip --output-dir results/contribution_audit/C17
```

Entry point: `contributions/17_topological_semantic_maps/experiments/eval_topo_semantic_navigation.py`.

Independent per-contribution outputs include `manifest.json`, `summary.md`, a nonempty CSV and SHA-256; the [C02–C26 workflow](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/c02-c26-exhaustive.yml) and its artifact `c02-c26-per-file-and-per-contribution-execution` preserve all 25 reports. The file-level auditor additionally inspects each source script, binary model, data file, plot and document in this contribution.

## Baselines and metrics

- **Baselines:** [Nominal topological route].
- **Primary metrics:** [top1_correct, topk_correct, path_found, path_cost, blocked_edges].
- **Evidence level:** synthetic.
- **Specific research limitation:** Hash-based label embeddings are deterministic stubs, not open-vocabulary perception evidence.

## Not established

A successful controlled runner does not prove trained-model performance, held-out site generalization, robust actual sensor inputs, real ROS 2 integration, robot-controller safety, formal mathematical proof, or real physical-robot navigation. These are separate experiments requiring actual available data/hardware and appropriate baselines, authenticated provenance and independent review. **Verified physical C17 trials: 0.**
