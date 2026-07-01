# C04 Scientific Upgrade Notes — Recoverability Metrics

## What was already strong

Contribution 04 is one of the most important DynNav modules because it introduces a navigation idea that is different from ordinary path cost and ordinary risk:

> A robot should avoid entering states from which it cannot safely recover or return.

The existing results already showed that strict irreversibility thresholds can make planning infeasible, while returnability-aware safe mode can recover feasibility.

Reported result summary:

- hard-threshold success rate: 26.7%,
- minimum feasible τ: 0.85,
- safe-mode success rate: 100%,
- safe-mode relaxed cases: 15 / 26,
- mean τ relaxation gap: 0.080,
- returnability sweep success rate: 100%.

This is strong because it shows a real planning failure mode: a planner can be too strict and silently fail unless it has a feasibility-aware recovery mechanism.

## Main weakness before this upgrade

The existing README explained returnability conceptually, but the module needed a more explicit metric layer.

A reviewer could ask:

> What exactly makes one state more recoverable than another?

or:

> Is irreversibility only a threshold, or can it be measured continuously?

## New contribution added

C04 now includes:

```text
code/recoverability_metrics.py
experiments/eval_recoverability_metrics.py
```

The new metric layer reports:

- whether a candidate state is returnable,
- shortest return distance to a trusted base,
- number of local escape options,
- bottleneck score,
- local obstacle density,
- normalized recoverability score,
- irreversibility score,
- path-level minimum recoverability,
- path-level maximum irreversibility.

## Why this matters scientifically

Returnability should not be only a binary yes/no condition.

Two states may both be technically returnable, but one may be much more dangerous because it lies inside a bottleneck or has only one escape option.

The upgraded C04 therefore distinguishes:

1. **Returnability** — can the robot get back to base?
2. **Recoverability** — how much future recovery freedom remains?
3. **Irreversibility** — how close the robot is to losing recovery freedom.

This supports a stronger research framing than a simple hard-threshold planner.

## New benchmark

Run:

```bash
python contributions/04_irreversibility_returnability/experiments/eval_recoverability_metrics.py
```

Output:

```text
contributions/04_irreversibility_returnability/results/c04_recoverability_metrics.csv
```

The benchmark compares candidate routes through:

- open space,
- a narrow bottleneck,
- a cul-de-sac commitment,
- a route that preserves recovery.

## Reviewer-safe claim

A stronger claim after this upgrade is:

> Contribution 04 evaluates navigation commitments through both binary returnability and continuous recoverability metrics, making it possible to distinguish safe open-space motion from bottleneck or cul-de-sac commitments even when all states remain technically reachable.

## Relationship to C27

C04 is the practical precursor to C27 Recoverability Theory.

C04 provides concrete metrics and benchmarks. C27 can generalize these ideas into a broader theoretical framework covering recoverability, future decision freedom, information debt, and trust margin.

## Limitations

- The new recoverability score is an interpretable planning signal, not a formal safety guarantee.
- BFS returnability assumes a known grid and does not model dynamics.
- Local escape options do not capture full kinodynamic constraints.
- Real robots may require orientation, velocity, clearance, and control feasibility.
- Formal safety barriers should be handled by C18.

## Next research step

The strongest extension is dynamic recoverability:

```text
R(x_t) and dR/dt
```

The planner should not only avoid low-recoverability states. It should also react when recoverability is dropping quickly, even before failure becomes inevitable.
