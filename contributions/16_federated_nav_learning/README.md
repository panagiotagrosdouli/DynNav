# Contribution 16 — Federated Navigation Learning

[![Module](https://img.shields.io/badge/Module-16-purple)](.) [![Type](https://img.shields.io/badge/Type-Federated%20Learning-blue)](.) [![Status](https://img.shields.io/badge/Status-Synthetic%20DP%20Simulation-orange)](.)

## Plain-language summary

A robot fleet can learn from many environments, but raw maps and trajectories may be private or sensitive.

Contribution 16 simulates federated multi-robot learning using federated averaging. Clients train locally on synthetic data and share model parameters with a central aggregation server. Optional server-side Gaussian noise implements a client-level central-DP mechanism under explicit fixed-cohort assumptions; the server still observes individual unnoised updates.

The upgraded version adds a trade-off benchmark:

> Does federated learning still work when clients are heterogeneous, aggregation changes, privacy noise is added, and communication cost matters?

---

## Research Question

> **RQ16:** Can federated learning improve navigation generalization across a robot fleet without sharing private map or trajectory data?

This contribution studies:

- FedAvg aggregation,
- weighted vs uniform aggregation,
- local robot training,
- clipped client-level update noise (central DP simulation),
- heterogeneous client data,
- fleet-level fairness,
- communication cost.

---

## Conceptual Pipeline

```text
global model
      ↓
broadcast to robots
      ↓
local training on private robot data
      ↓
model update / DP-noised update
      ↓
FedAvg aggregation
      ↓
new global model
      ↓
fleet-level evaluation
```

---

## Existing Components

The original C16 implementation includes:

- `FedNavConfig`,
- `NavModel`,
- `FederatedRobotClient`,
- `FederatedServer`,
- FedAvg aggregation,
- optional server-side clipping and Gaussian noise on client deltas (not local DP),
- weighted or uniform aggregation.

---

## New Upgrade Added

C16 now includes:

```text
federated_evaluator.py
```

This evaluator measures:

- mean client MSE,
- worst client MSE,
- best client MSE,
- fairness gap,
- final server validation MSE,
- communication floats,
- whether DP was enabled,
- DP epsilon.

---

## Files

```text
16_federated_nav_learning/
├── README.md
├── federated_nav.py
├── federated_evaluator.py
├── docs/
│   └── SCIENTIFIC_UPGRADE.md
├── experiments/
│   └── eval_federated_tradeoffs.py
└── results/
    └── c16_federated_tradeoffs.csv
```

---

## Quick Start

Run the federated trade-off benchmark:

```bash
python contributions/16_federated_nav_learning/experiments/eval_federated_tradeoffs.py
```

This generates:

```text
contributions/16_federated_nav_learning/results/c16_federated_tradeoffs.csv
```

---

## Benchmark Scenarios

The new benchmark compares:

| Scenario | Aggregation | Privacy |
|---|---|---|
| `weighted_no_dp` | sample-weighted FedAvg | none |
| `uniform_no_dp` | equal client weights | none |
| `uniform_dp_eps_2` | uniform FedAvg | client-level Gaussian mechanism, epsilon 2 |
| `uniform_dp_eps_1` | uniform FedAvg | client-level Gaussian mechanism, epsilon 1 |

---

## Metrics

| Metric | Meaning |
|---|---|
| Mean client MSE | Average model error across robot-specific validation sets |
| Worst client MSE | Error on the most poorly served robot |
| Best client MSE | Error on the best-served robot |
| Fairness gap | Worst client MSE minus best client MSE |
| Server validation MSE | Global synthetic validation error |
| Communication floats | Approximate transmitted parameter count |
| DP epsilon | Privacy setting used for noised updates |

---

## Scientific Contribution

The upgraded C16 contribution is not simply:

> Run FedAvg for robot clients.

It is stronger:

> Evaluate federated navigation learning as a fleet-level trade-off between generalization, privacy, fairness, aggregation strategy, and communication cost.

This makes the module more relevant to real multi-robot systems.

---

## Integration

- **Distributed extension of:** C01 learned navigation heuristics
- **Uses:** C09 multi-robot communication and coordination concepts
- **Can be protected by:** C08 IDS when client updates are suspicious
- **Can be made robust by:** C26 swarm consensus / Byzantine fault tolerance
- **Can support:** fleet-wide adaptation for C22 curriculum RL policies

Recommended runtime interface:

```text
federated_update = {
    robot_id,
    model_delta,
    n_samples,
    dp_epsilon,
    validation_summary,
    trust_score
}
```

---

## Limitations

- The navigation model is a lightweight linear policy.
- Client datasets are synthetic.
- DP uses fixed full-cohort participation, replace-one client adjacency, uniform aggregation, and basic composition across rounds; it is not local DP and has no secure aggregation.
- The central server observes individual client updates before clipping. Treat privacy claims as a mathematical mechanism under these assumptions, not a deployed privacy guarantee.
- Secure aggregation is not implemented.
- Robust aggregation against poisoned updates is left for future work.

---

## Next Research Step

The strongest extension is robust federated aggregation:

```text
client updates
      ↓
trust / anomaly filtering
      ↓
robust aggregation
      ↓
global navigation model
```

This would connect C16 with C08 and C26.

---

## Conclusion

Contribution 16 provides a synthetic federated-learning simulation and an explicitly scoped central-DP mechanism.

The upgraded version makes the module scientifically stronger by evaluating privacy, fairness, communication, and aggregation trade-offs instead of only demonstrating FedAvg mechanics.
