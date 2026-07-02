# C09 Scientific Upgrade Notes — Team Coordination Metrics

## What was already strong

Contribution 09 already introduced decentralized multi-robot coordination under uncertainty.

The original concept included:

- local map sharing,
- gossip-style belief exchange,
- conflict-free path allocation,
- team-level risk budgeting,
- disagreement detection.

This is important because multi-robot navigation is not simply several independent single-robot planners running at the same time.

## Main weakness before this upgrade

The README described coordination conceptually, but it did not define measurable coordination quality.

A reviewer could ask:

> How do we know that a team plan is coordinated?

or:

> What counts as a failure: collision conflict, risk-budget violation, or belief disagreement?

## New contribution added

C09 now includes:

```text
code/team_coordination_metrics.py
experiments/eval_team_coordination.py
```

The new metric layer evaluates:

- vertex conflicts,
- edge-swap conflicts,
- total team risk,
- per-robot risk-budget violations,
- belief disagreement count,
- team-level feasibility.

## New benchmark

Run:

```bash
python contributions/09_multi_robot/experiments/eval_team_coordination.py
```

Output:

```text
contributions/09_multi_robot/results/c09_team_coordination.csv
```

The benchmark evaluates scenarios such as:

- conflicting paths,
- risk-budget violation,
- belief disagreement,
- coordinated feasible team plan.

## Reviewer-safe claim

A stronger claim after this upgrade is:

> Contribution 09 evaluates multi-robot coordination through explicit team metrics: spatial-temporal path conflicts, risk-budget violations, belief disagreement, and team-level feasibility.

## Relationship to other contributions

C09 connects directly to:

- C06 when robots act as communication relays,
- C07 when robots coordinate exploration frontiers,
- C08 when one robot's information becomes untrusted,
- C26 for fault-tolerant swarm consensus.

## Limitations

- Path conflict detection uses discrete time and grid positions.
- Belief disagreement is represented by compact hashes rather than full map distributions.
- Risk budgets are scalar and do not yet capture spatial or temporal risk allocation.
- Real deployment requires ROS 2 namespacing, communication delay, packet loss, and robot dynamics.

## Next research step

The strongest extension is decentralized repair:

```text
conflict or disagreement detected -> local negotiation -> revised team plan
```

This would turn C09 from a coordination evaluator into a decentralized team replanning module.
