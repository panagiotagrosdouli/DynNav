# C16 — reproducible experiment and claim boundaries

**Evidence:** The registered `c16_federated_tradeoffs` synthetic benchmark **executed successfully** in [run #42702357587](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42702357587). This is real software execution, not hardware or scientific generalization evidence.

## Hypothesis

Robust or privacy-aware aggregation exposes measurable accuracy, fairness, privacy, and communication trade-offs across robot clients.

## Exact command and original source

```bash
python scripts/run_contribution_suite.py --only C16 --fail-on-skip --output-dir results/contribution_audit/C16
```

Entry point: `contributions/16_federated_nav_learning/experiments/eval_federated_tradeoffs.py`.

Independent per-contribution outputs include `manifest.json`, `summary.md`, a nonempty CSV and SHA-256; the [C02–C26 workflow](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/c02-c26-exhaustive.yml) and its artifact `c02-c26-per-file-and-per-contribution-execution` preserve all 25 reports. The file-level auditor additionally inspects each source script, binary model, data file, plot and document in this contribution.

## Baselines and metrics

- **Baselines:** [Centralized reference, FedAvg].
- **Primary metrics:** [mean_client_mse, worst_client_mse, fairness_gap, communication_floats, final_server_val_mse].
- **Evidence level:** synthetic.
- **Specific research limitation:** Synthetic client objectives do not establish performance on heterogeneous robot datasets.

## Not established

A successful controlled runner does not prove trained-model performance, held-out site generalization, robust actual sensor inputs, real ROS 2 integration, robot-controller safety, formal mathematical proof, or real physical-robot navigation. These are separate experiments requiring actual available data/hardware and appropriate baselines, authenticated provenance and independent review. **Verified physical C16 trials: 0.**
