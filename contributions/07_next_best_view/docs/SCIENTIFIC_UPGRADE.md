# C07 Scientific Upgrade Notes — Returnability-Aware Next-Best-View

## What was already strong

Contribution 07 already addressed a central active-exploration problem:

> Which viewpoint should the robot visit next to reduce map uncertainty efficiently?

The original formulation used information gain divided by travel cost. This is the standard greedy idea behind many next-best-view and frontier-exploration methods.

## Main weakness before this upgrade

A purely information-gain-driven viewpoint can be operationally unsafe.

A frontier may reveal many unknown cells while also requiring the robot to:

- cross a high-risk region,
- enter a bottleneck,
- lose communication,
- reduce returnability,
- commit to a cul-de-sac.

A reviewer could ask:

> Does the robot select informative views that it can still safely recover from?

## New contribution added

C07 now includes:

```text
code/nbv_scoring.py
experiments/eval_returnability_aware_nbv.py
```

The upgraded scoring layer compares:

- classic NBV score: information gain / travel cost,
- safe NBV score: information gain with risk, returnability, and connectivity terms.

## Why this matters scientifically

Exploration is not only about reducing entropy.

In unknown environments, a robot should preserve future decision freedom while gaining information. This connects C07 directly to:

- C03 risk-aware planning,
- C04 recoverability and returnability,
- C06 connectivity-aware navigation,
- C24 uncertainty-aware neural mapping.

## New benchmark

Run:

```bash
python contributions/07_next_best_view/experiments/eval_returnability_aware_nbv.py
```

Output:

```text
contributions/07_next_best_view/results/c07_returnability_aware_nbv.csv
```

The benchmark compares candidate frontiers such as:

- near low-gain viewpoint,
- far high-gain viewpoint,
- bottleneck frontier,
- balanced safe frontier,
- relay-supported frontier.

## Reviewer-safe claim

A stronger claim after this upgrade is:

> Contribution 07 evaluates next-best-view selection not only by information gain and travel cost, but also by whether the selected viewpoint preserves returnability, avoids risk, and maintains connectivity.

## Limitations

- The benchmark is synthetic and intentionally small for auditability.
- The scoring function is transparent but hand-weighted.
- Real exploration requires frontier extraction from occupancy grids or 3D maps.
- Information gain should eventually be estimated from sensor model visibility, not only provided as a candidate attribute.

## Next research step

The strongest extension is adaptive NBV weighting:

```text
score = f(information_gain, travel_cost, risk, returnability, connectivity, mission_phase)
```

The planner should become more conservative when recoverability is low and more exploratory when safety margins are high.
