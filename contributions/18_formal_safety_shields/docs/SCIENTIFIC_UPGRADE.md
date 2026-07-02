# C18 Scientific Upgrade Notes — Formal Shield Stress Test

## What was already strong

Contribution 18 already implemented a formal runtime-safety layer for DynNav:

- Signal Temporal Logic monitoring,
- Control Barrier Function command filtering,
- online safety diagnostics,
- CBF correction norms,
- STL robustness values.

This is important because learned or heuristic planners can propose unsafe commands. A formal shield can act as a runtime safety filter around any planner.

## Main weakness before this upgrade

The original module explained STL and CBF mechanics, but the evaluation claim needed more explicit stress testing.

A reviewer could ask:

> Does the shield actually reduce safety violations under difficult obstacle configurations?

or:

> What is the cost of the shield in terms of command correction and navigation efficiency?

## New contribution added

C18 now includes:

```text
shield_evaluator.py
experiments/eval_shield_stress_test.py
```

The new benchmark compares shielded and unshielded execution under:

- single obstacle direct path,
- narrow gap,
- offset hazard.

It reports:

- minimum obstacle distance,
- safety violation count,
- mean CBF correction norm,
- total path length,
- final goal distance,
- minimum STL robustness,
- intervention rate.

## New benchmark

Run:

```bash
python contributions/18_formal_safety_shields/experiments/eval_shield_stress_test.py
```

Output:

```text
contributions/18_formal_safety_shields/results/c18_shield_stress_test.csv
```

## Reviewer-safe claim

A stronger claim after this upgrade is:

> Contribution 18 evaluates STL+CBF safety shields under stress-test navigation scenarios, measuring violation reduction, robustness margin, correction cost, and navigation-efficiency impact.

## Relationship to other contributions

C18 connects directly to:

- C05 safe mode as a higher-level behavioural fallback,
- C03 risk-aware planning as a pre-filtered planner objective,
- C04 irreversibility/recoverability as a complementary safety signal,
- C08 IDS when compromised signals require stricter shielding,
- C21/C22 learned policies that require runtime safety wrappers.

## Limitations

- The CBF filter uses a lightweight gradient-projection approximation rather than a production QP solver.
- The robot is modeled as a point robot with simple velocity commands.
- Stress-test scenarios are synthetic and low-dimensional.
- Real deployment requires dynamics, actuator limits, sensor delay, and certified emergency-stop integration.

## Next research step

The strongest extension is risk-adaptive shielding:

```text
risk / trust / uncertainty rises -> tighten CBF radius and STL robustness margin
```

This would connect C18 with C02, C03, C05, and C08, making the shield more conservative when information is unreliable.
