# Frozen geometric Pareto protocol

This protocol is committed before inspecting any Pareto-sweep outcomes. It uses the three geometries already frozen in `dynnav.experiments.geometric_heldout_benchmark` and does not modify their cells, triggers, closure probabilities, starts, goals, or safe sets.

## Question

How does the soft history-conditioned objective trade geometric path length against post-closure safe-return failure, compared with a hard safe-return constraint, when both are evaluated over the same action-triggered topology hazards?

The experiment is descriptive rather than a winner-selection exercise. No single weight or threshold is designated as the preferred operating point before execution.

## Frozen parameter grid

- Soft history-aware recoverability weights: `lambda in {0, 1, 2, 4, 8, 16}`.
- Hard safe-return thresholds: `tau in {0.50, 0.70, 0.80, 0.90, 0.95, 0.99}`.
- Execution seeds: integers `0..499` for every scenario/configuration.
- Common random numbers: each declared closure event receives the same seed-indexed latent draw across planners; only events activated by the selected route are realized.
- Exact return oracle cap: 16 active hazards, which exceeds the number present in the frozen geometric worlds.

## Outcomes

For each scenario/configuration, retain:

- planner feasibility (`planner_success`), reported separately from execution outcomes;
- geometric path length for feasible plans;
- activated closure count;
- final and minimum history-conditioned return probability when available;
- planning latency and expanded nodes as implementation-cost diagnostics;
- post-closure irreversible-failure rate across the 500 common-random-number seeds for feasible plans.

A planner that returns no path is **not** coded as an irreversible failure. It is reported as infeasible for that configuration, and stochastic execution metrics are undefined for that row. This preserves the existing operational definition of irreversible failure as post-closure inability to return to the designated safe set.

## Interpretation rules

- Report the complete sweep, not only nondominated or favorable operating points.
- Pareto/nondominance summaries may be added only after the full table is retained.
- Do not change the frozen geometries or parameter grid after inspecting outcomes.
- Do not infer geometric-domain generalization beyond these three hand-built held-out topologies.
- Do not claim universal superiority over hard safe-return constraints; hard constraints and soft penalties express different operating objectives.
