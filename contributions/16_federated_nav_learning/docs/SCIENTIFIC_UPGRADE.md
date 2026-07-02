# C16 Scientific Upgrade Notes — Federated Trade-Off Evaluation

## What was already strong

Contribution 16 already implemented the core idea of privacy-preserving fleet learning:

> Multiple robots improve a shared navigation model without uploading raw maps, trajectories, or sensor logs.

The existing module includes:

- FedAvg aggregation,
- weighted and uniform aggregation options,
- local robot clients,
- a lightweight navigation model,
- optional Gaussian differential privacy noise.

This is important because robot fleets often collect sensitive spatial data.

## Main weakness before this upgrade

The original implementation could run federated rounds, but it did not evaluate the trade-offs that matter for robot fleets.

A reviewer could ask:

> Does weighted aggregation behave differently from uniform aggregation?

or:

> What is the cost of differential privacy on generalization and fairness across robots?

or:

> How much communication does this require?

## New contribution added

C16 now includes:

```text
federated_evaluator.py
experiments/eval_federated_tradeoffs.py
```

The new benchmark compares:

- weighted FedAvg without DP,
- uniform FedAvg without DP,
- weighted FedAvg with DP epsilon 2,
- weighted FedAvg with DP epsilon 1.

It reports:

- mean client MSE,
- best client MSE,
- worst client MSE,
- fairness gap,
- server validation MSE,
- communication cost in transmitted floats,
- privacy setting metadata.

## New benchmark

Run:

```bash
python contributions/16_federated_nav_learning/experiments/eval_federated_tradeoffs.py
```

Output:

```text
contributions/16_federated_nav_learning/results/c16_federated_tradeoffs.csv
```

## Reviewer-safe claim

A stronger claim after this upgrade is:

> Contribution 16 evaluates federated navigation learning through fleet-level trade-offs: generalization error, client fairness, differential-privacy noise, aggregation strategy, and communication cost.

## Relationship to other contributions

C16 connects directly to:

- C01 learned navigation heuristics as a distributed learning extension,
- C09 multi-robot coordination as the fleet communication layer,
- C26 swarm consensus for robust aggregation under unreliable robots,
- C08 security monitoring when client updates may be compromised.

## Limitations

- The navigation model is a lightweight linear policy.
- Client data is synthetic and heterogeneous by construction.
- Differential privacy is approximated by simple Gaussian noise injection.
- Real deployment requires secure aggregation, robust update filtering, communication scheduling, and real robot datasets.

## Next research step

The strongest extension is robust federated aggregation:

```text
client updates -> trust / anomaly filtering -> robust aggregation -> global navigation model
```

This would connect C16 with C08 and C26, making federated learning safer under compromised or unreliable clients.
