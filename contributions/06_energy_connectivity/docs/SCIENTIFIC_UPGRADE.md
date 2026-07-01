# C06 Scientific Upgrade Notes — Resource Feasibility

## What was already strong

Contribution 06 already connected navigation with two practical constraints that are often ignored in simple planners:

- battery energy,
- communication connectivity.

The existing experiment compared a baseline path, an energy-limited setting, and a connectivity-aware setting. This is valuable because it demonstrates that a path can be geometrically feasible while still being operationally weak due to low link quality or insufficient energy.

## Main weakness before this upgrade

The original README explained the concept, but it did not yet provide a clear mission-level decision layer.

A reviewer could ask:

> If the direct route is not feasible, does the robot need recharge, a relay, both, or should the mission be rejected?

This distinction matters because resource-aware navigation is not only about assigning a larger cost to bad cells. It is about deciding whether the mission can be completed under real constraints.

## New contribution added

C06 now includes:

```text
code/resource_feasibility.py
experiments/eval_resource_feasibility.py
```

The new layer evaluates candidate routes using:

- energy required,
- usable energy after reserve,
- energy margin,
- minimum connectivity,
- connectivity margin,
- recharge requirement,
- relay requirement,
- final mission verdict.

## Mission verdicts

The benchmark can classify routes as:

| Verdict | Meaning |
|---|---|
| DIRECT_FEASIBLE | Route satisfies energy and connectivity constraints directly |
| NEEDS_RECHARGE | Route is acceptable only if a recharge stop is included |
| NEEDS_RELAY | Route is acceptable only if communication relay support is included |
| NEEDS_RECHARGE_AND_RELAY | Route needs both resource supports |
| INFEASIBLE | Route violates constraints without available mitigation |

## New benchmark

Run:

```bash
python contributions/06_energy_connectivity/experiments/eval_resource_feasibility.py
```

Output:

```text
contributions/06_energy_connectivity/results/c06_resource_feasibility.csv
```

The benchmark compares candidate routes such as:

- short low-connectivity route,
- longer high-connectivity route,
- route via recharge,
- route via relay,
- route requiring both recharge and relay.

## Reviewer-safe claim

A stronger claim after this upgrade is:

> Contribution 06 evaluates navigation feasibility under energy and communication constraints, producing explicit mission verdicts rather than only adding resource penalties to path cost.

## Relationship to other contributions

C06 supports:

- C05 safe mode when battery or connectivity margins become unsafe,
- C09 multi-robot coordination when robots act as relays,
- C22 reinforcement learning when energy/connectivity become reward terms,
- C26 swarm consensus when communication reliability affects shared decisions.

## Limitations

- Energy is currently modeled as distance times a scalar cost.
- Connectivity is summarized by minimum and mean route quality.
- Real systems should include terrain, velocity, payload, localization quality, packet loss, and ROS 2 QoS effects.
- Recharge and relay are modeled as route attributes rather than full scheduling problems.

## Next research step

The strongest extension is joint resource-aware replanning:

```text
route = f(goal, battery, relay availability, connectivity map, safe-mode state)
```

This would allow the robot to replan toward chargers or relay-preserving corridors before mission failure becomes unavoidable.
