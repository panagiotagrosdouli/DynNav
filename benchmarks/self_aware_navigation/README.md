# Self-Aware Active Navigation Demo

This benchmark is the first implementation step for issue #16: **Self-Aware Active Navigation under Uncertainty**.

## Research question

Can a navigation objective prefer an information-gathering, lower-risk route over a shorter but riskier route when the robot has uncertainty about the environment?

## What is implemented

The demo compares two candidate paths in a synthetic uncertain corridor:

1. `shortest_path` — shorter but crosses higher-risk cells.
2. `self_aware_active_path` — longer but sees more uncertain cells and preserves higher recoverability.

The planner scores each path using:

```text
J = alpha * path_length
  + beta  * expected_collision_risk
  + gamma * cvar_tail_risk
  + delta * localization_uncertainty
  + eta   * map_uncertainty
  + zeta  * irreversibility
  - kappa * information_gain
```

Lower cost is better.

## Run

From the repository root:

```bash
python benchmarks/self_aware_navigation/run_self_aware_demo.py
```

The script writes:

```text
results/self_aware_navigation_demo.csv
```

## Metrics

The CSV includes:

- path length,
- mean risk,
- max risk,
- CVaR risk,
- uncertainty integral,
- information gain,
- recoverability,
- compute time,
- selected candidate,
- self-aware cost.

## Scientific status

Readiness: **Prototype / Reproducible demo**

This is not yet a full benchmark or state-of-the-art claim. It is a controlled demonstration of the core objective that will later be extended with:

- multiple random seeds,
- generated maps,
- dynamic obstacles,
- localization uncertainty models,
- baselines and ablations,
- statistical result summaries.

## Main limitation

The current environment is synthetic and uses hand-defined candidate paths. The next step is to connect this cost function to an actual path search or replanning algorithm.
