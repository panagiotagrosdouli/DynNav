# C01 Scientific Upgrade Notes — Learned A* Heuristics

## Current Strength

Contribution 01 is already one of the strongest DynNav modules because it separates raw learned heuristic behavior from admissible Manhattan-clipped behavior.

This distinction is scientifically important:

- a raw neural heuristic may reduce expansions,
- but it does not automatically preserve optimality,
- while a Manhattan-clipped heuristic is admissible on 4-neighbour unit-cost grids,
- but may become too conservative to outperform Manhattan A*.

## Main Scientific Risk

The current result should not be framed as "learning makes A* faster" in a broad sense.

A more precise claim is:

> A learned heuristic can reduce node expansions in easier grid regimes, but its benefit depends on admissibility policy, obstacle density, and inference overhead.

This is stronger because it is honest, falsifiable, and reviewer-safe.

## What Makes C01 PhD-Level

C01 becomes much more serious if it answers three questions:

1. **Efficiency:** Does the learned heuristic reduce node expansions?
2. **Correctness:** Does it preserve optimal path cost?
3. **Admissibility:** Does it avoid overestimating true cost-to-go?

The first two are partly covered by the existing statistical validation benchmark. The third requires an explicit admissibility/consistency audit.

## Added Upgrade

The new script:

```bash
python contributions/01_learned_astar/experiments/admissibility_audit.py
```

checks heuristic behavior against exact shortest-path cost-to-go values computed by reverse BFS from the goal.

It reports:

- number of sampled states,
- number of admissibility violations,
- maximum overestimation,
- mean overestimation among violations,
- number of consistency violations,
- maximum consistency gap.

## Reviewer-Safe Claims After This Upgrade

Allowed:

> Raw learned A* is empirically evaluated for expansion reduction and path-cost preservation.

Allowed:

> Manhattan-clipped learned A* is admissible on 4-neighbour unit-cost grids because it upper-bounds the learned estimate by the Manhattan heuristic.

Allowed after audit:

> On the audited benchmark states, the learned heuristic produced X admissibility violations and Y consistency violations.

Avoid:

> The raw learned heuristic is guaranteed optimal.

Avoid:

> Learned A* is faster than classical A*.

The current evidence shows lower expansions in some regimes, but neural inference can increase wall-clock runtime.

## Next Research Step

The most valuable next extension is not another neural model. It is an **admissibility-repair layer**:

1. learn an informative heuristic,
2. audit violations against exact cost-to-go on sampled maps,
3. calibrate or repair the heuristic,
4. prove or empirically bound overestimation,
5. compare expansion reduction versus admissibility loss.

This would make C01 a strong learning-augmented planning contribution rather than a simple demo.