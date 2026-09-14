# Contribution 27 — Recoverability Theory for Autonomous Navigation

## One-sentence contribution

Contribution 27 is a **research proposal / theory track** that treats recoverability as a first-class navigation quantity: not merely whether the robot is currently collision-free, but how much feasible future ability to return, recover, or switch to an acceptable fallback remains after its decisions.

## Current maturity

**Status: Research proposal and future implementation.**

This directory currently contains conceptual documentation only. It is **not** part of the canonical C01–C26 experiment registry, does not currently have its own benchmark runner, and must not be cited as independently validated theory or as a formal safety guarantee.

The broader DynNav repository now contains a much more concrete, experimentally developed recoverability line under `dynnav/`, `ros2_ws/`, `results/`, and `paper/`. That work should not be retroactively treated as proof of every concept listed in this proposal. Instead, C27 should be read as an umbrella theory direction whose ideas may be instantiated by specific models and experiments elsewhere in the repository.

## Research motivation

Conventional path planning commonly optimizes geometric distance, traversal cost, or immediate collision/risk estimates. Those objectives can prefer a state that is locally attractive but leaves very few feasible future recovery options. In dynamic or partially observed environments this distinction matters because a robot can remain collision-free while becoming effectively committed: a route behind it may close, energy may become insufficient for return, communication may be lost, or a fallback corridor may disappear.

The motivating question is therefore:

> How should a navigation system represent and preserve the robot's ability to recover after future disturbances, model errors, or topology changes?

## Research questions

1. **Representation:** What state information is required for recoverability? Is geometric state sufficient, or must the planner include belief, resources, topology, and execution history?
2. **Measurement:** Can recoverability be expressed as a scalar, a vector of capabilities, a probability, or a reachable-set / viable-set object?
3. **Planning:** How should recoverability trade against path length, task progress, energy, and conventional risk?
4. **Prediction:** How far into the future must the planner reason before a loss of recoverability becomes visible?
5. **Control:** When should low recoverability trigger replanning, safe-mode behavior, retreat, or mission termination?
6. **Validation:** Which claims can be tested empirically, and which require formal assumptions and proofs?

## Core concepts

### Recoverability metric `R(x)`

A generic notation for the amount of acceptable recovery capability available from state `x`. The exact semantics must be declared by each implementation. Examples include:

- binary return feasibility;
- probability of reconnecting to a safe set under stochastic future closures;
- number or diversity of admissible fallback routes;
- minimum resource margin required for return;
- reachable-set volume under bounded disturbances.

A numerical value called `R(x)` is meaningful only together with its model, safe set, disturbance model, and estimator.

### Recoverability map

A spatial or state-space field showing how recoverability varies across candidate states. Such a map may be deterministic or probabilistic and may depend on belief, resources, or history.

### Recoverability gradient

A local sensitivity concept describing how quickly recoverability changes as the robot moves through state space. This can be useful for identifying commitment boundaries, but a gradient is only well-defined for recoverability representations with suitable smoothness or finite-difference semantics.

### Recoverability horizon

The planning horizon over which future disturbances or topology changes are considered. A short horizon can miss delayed commitment effects; a long horizon can become computationally expensive or model-sensitive.

### Recoverability budget

A mission-level constraint or resource interpretation in which a plan must retain at least a declared amount of recovery capability. The budget may be a hard threshold or a soft planning penalty.

### Recoverability barrier

A proposed boundary separating states that satisfy a declared recoverability condition from those that do not. Calling such a boundary a "barrier" does **not** by itself establish a control-barrier-function theorem or forward-invariance guarantee; those require explicit dynamics, assumptions, and proof obligations.

### Recoverability-aware planning

A planner that includes a recoverability quantity in its state, constraints, or objective. Possible formulations include:

```text
minimize    geometric_cost + λ_risk * risk + λ_rec * recoverability_loss
subject to  task / dynamics / resource constraints
```

or a hard-return condition such as:

```text
P(return to safe set | state, belief, history) >= τ
```

These are design patterns, not universal prescriptions.

## Relationship to the current DynNav-R line

The publication-focused DynNav-R work operationalizes one narrow version of the broader idea: **history-conditioned safe-return probability under action-triggered topology hazards**.

In that setting, robot actions can activate future closure hazards. Two trajectories may therefore reach the same geometric cell while inducing different future return probabilities. The planner augments geometric state with the set of hazards activated by executed transitions and evaluates safe-return connectivity conditioned on that history.

That result supports one specific lesson relevant to C27:

> recoverability can depend on information that is not contained in the current geometric position alone.

It does **not** prove that every proposed recoverability map, gradient, budget, horizon, or barrier in this document is correct or useful.

## Candidate mathematical formulations

### Deterministic return feasibility

For safe set `S` and feasible transition relation `F`, define:

```text
R_bin(x) = 1  if there exists a feasible path from x to S
           0  otherwise.
```

This captures structural returnability but ignores stochastic future changes.

### Probabilistic safe-return reliability

For uncertainty model `H` over future hazards:

```text
R_prob(x, h) = P(a feasible return path to S survives | x, executed history h).
```

The current action-triggered DynNav work uses this style of quantity for small hazard sets via exact enumeration.

### Redundancy-aware recoverability

A richer measure can account for multiple independent or partially independent return routes rather than only the best single route. Any approximation must state whether it is optimistic, conservative, or unbounded relative to the exact connectivity probability.

### Resource-aware recoverability

For remaining resource vector `b` (energy, time, communication budget, etc.), recoverability may be conditioned on both geometry and resources:

```text
R(x, b) = feasibility or probability of reaching S without violating b.
```

## Required evidence for a future C27 implementation

A mature implementation should include:

- a precise recoverability definition and safe set;
- explicit disturbance / uncertainty assumptions;
- exact or reference oracle on small instances;
- approximation-error evaluation for scalable estimators;
- state-only versus richer-state counterfactual tests;
- baseline planners using shortest path, risk-only, and hard safe-return constraints;
- paired stochastic trials with common random numbers where appropriate;
- held-out geometries rather than a single repeated synthetic template;
- runtime and scaling measurements;
- explicit negative results / counterexamples;
- ROS2/Nav2/Gazebo or hardware evidence before making robotics deployment claims;
- formal proofs only for statements that actually satisfy formal assumptions.

## Failure modes and falsification tests

The theory should be considered weakened or falsified in a proposed setting if, for example:

- recoverability adds no decision-relevant information beyond the chosen baseline state;
- a state-only model matches a history-conditioned model on all relevant counterfactuals;
- the estimator systematically overstates return probability near multi-cell cutsets;
- preserving recoverability causes unacceptable mission failure or path inflation without compensating benefit;
- a hard safe-return constraint dominates the proposed soft objective across the target operating regime;
- the assumed hazard model does not resemble the dynamics of the intended deployment environment.

## Planned implementation path

1. Define a minimal formal state and safe set.
2. Implement exact recoverability for small discrete worlds.
3. Add scalable graph / sampling approximations with measured error.
4. Add planning objectives and hard-constraint baselines.
5. Construct same-state / different-history counterfactuals.
6. Evaluate heterogeneous held-out topologies.
7. Integrate execution history into ROS2/Nav2.
8. Validate action-triggered closures in Gazebo with retained traces.
9. Extend only after the narrow mechanism is supported.

Several of these steps now exist elsewhere in DynNav for the current history-conditioned research line, but they remain separate from this proposal directory until C27 is formally promoted into the canonical contribution registry.

## Related DynNav modules

- [`04_irreversibility_returnability`](../04_irreversibility_returnability/) — structural returnability / irreversibility precursor.
- [`05_safe_mode_navigation`](../05_safe_mode_navigation/) — runtime fallback and supervision.
- [`06_energy_connectivity`](../06_energy_connectivity/) — resource/connectivity constraints.
- [`03_belief_risk_planning`](../03_belief_risk_planning/) — risk-sensitive planning baseline and comparison point.
- [`../README.md`](../README.md) — complete contribution map and evidence policy.
- [`../../paper/dynnav_r/main.tex`](../../paper/dynnav_r/main.tex) — publication-focused history-conditioned recoverability argument.

## Claim boundary

C27 currently contributes a structured research agenda, terminology, candidate formulations, and falsification criteria. It does not currently contribute an independently validated algorithm, benchmark result, hardware result, or formal theorem from this directory alone.
