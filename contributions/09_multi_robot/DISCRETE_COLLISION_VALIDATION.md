# C09 — Executed discrete multi-robot collision guard, evidence and limits

## Verified software execution

[Successful CI run #42783322680](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42783322680) executed the actual repaired `code/decentralized_nav.py` simulator, **5 focused tests**, the registered `C09` coordination benchmark and two explicitly instrumented two-agent scenarios. JSON artifacts retain the outcomes.

| Scenario | Start | Destination | Goal completion | Blocked intents | Physical collisions |
|---|---|---|---|---:|---|
| Two-agent head-on swap in a 1×2 corridor | Adjacent opposite ends | Each other's start | **No** — agent movement refused | 30 across 15 ticks | Not measurable (simulated) |
| Two agents with independent 5×9 trajectories | Separate columns | Distinct nearby goals | **Yes** — both reached | 0 | Not measurable (simulated) |

A collision-free, non-progressing plan is possible (deadlock). This explicitly demonstrates a **safety–liveness tradeoff** rather than pretending the conservative rule solves general multi-agent navigation.

## Defect and implemented fix

The original C09 scheduler only reserved *future intended* cells, and could let a high-priority robot enter another agent's *currently occupied* cell. This does not prevent head-on edge swaps, and failed to validate duplicate start locations or IDs.

The revised scheduler:
- Rejects duplicate robot IDs, occupied identical starts and blocked/out-of-bounds endpoints.
- Conservatively forbids moving into **any other robot's start-of-tick occupied cell**, even if that robot intends to leave.
- Reserves each accepted future cell, rechecks uniqueness of every intent before motion and fails closed if invalid.
- Waits at its original cell after replanning; the new route is rechecked on the next tick.
- Marks agents already at their goals as reached before starting.
- Keeps `collision_events` as a historical compatibility field, but it measures **blocked/avoided intents**, not observed crashes.

Tests cover swaps, a feasible two-agent mission, duplicate initial positions/IDs, obstacle goals and initial-at-goal behavior.

## Replication

```bash
python -m pytest -q contributions/09_multi_robot/tests
python scripts/run_contribution_suite.py --only C09 --fail-on-skip --output-dir results/c09_validation/registered
```

[Dedicated workflow](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/c09-discrete-collision.yml) generates `results/c09_validation/discrete_safety_scenarios.json`, and the `c09-discrete-collision-simulation` artifact contains the exact results.

## Scientific limits

This is a **discrete in-process simulation on synthetic grids**, not real ROS 2 DDS exchange, multi-robot Nav2 control, on-hardware proximity sensing or collision safety certification. No sampled dynamic delay, asynchronous coordination, real robot footprint or kinodynamic state constraints are modeled. The conservative barrier explicitly sacrifices potential progress to avoid occupied-cell incursions. Further research needs actual 2–N robot ROS 2 controller integration, real-map scenarios, repeated randomized multi-agent benchmarks and hardware trials with onsite safety operators.

**Physically controlled C09 robots verified in this run: 0.**
