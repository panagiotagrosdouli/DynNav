# Contribution 18 — Formal Safety Shields

[![Module](https://img.shields.io/badge/Module-18-purple)](.) [![Type](https://img.shields.io/badge/Type-Formal%20Methods-blue)](.) [![Status](https://img.shields.io/badge/Status-Core%20Upgraded-brightgreen)](.)

## Plain-language summary

A robot planner can make mistakes.

A safety shield sits between the planner and the robot actuators and checks:

```text
Is this command safe to execute right now?
Will it violate obstacle-distance or temporal safety constraints?
If unsafe, how should the command be minimally corrected?
```

Contribution 18 implements runtime safety shielding with Signal Temporal Logic and Control Barrier Functions.

The upgraded version adds a stress-test benchmark comparing shielded and unshielded execution.

---

## Research Question

> **RQ18:** Do STL+CBF safety shields reduce runtime constraint violations without excessive correction cost or navigation-efficiency loss?

This contribution studies:

- Signal Temporal Logic monitoring,
- STL robustness values,
- Control Barrier Function command filtering,
- minimum-distance constraints,
- shield intervention rate,
- command correction cost,
- safety-efficiency trade-offs.

---

## Conceptual Pipeline

```text
planner command
      ↓
STL monitor evaluates trajectory safety
      ↓
CBF filter checks immediate obstacle safety
      ↓
unsafe command is minimally corrected
      ↓
safe command sent to robot
```

---

## Existing Components

The original C18 implementation includes:

- `STLFormula`,
- `STLAtom`,
- `STLAlways`,
- `STLEventually`,
- `STLAnd`,
- `STLOr`,
- `STLMonitor`,
- `CBFConfig`,
- `CBFSafetyFilter`,
- `SafetyShield`.

---

## CBF Condition

The implemented CBF condition is:

```text
∇h(x) · u + α h(x) ≥ 0
```

where:

```text
h(x) = ||robot - obstacle|| - safety_radius
```

If the condition is violated, the velocity command is corrected toward the safe set.

---

## New Upgrade Added

C18 now includes:

```text
shield_evaluator.py
```

This evaluator reports:

- minimum obstacle distance,
- safety violation count,
- mean correction norm,
- total path length,
- final goal distance,
- minimum STL robustness,
- shield intervention rate.

---

## Files

```text
18_formal_safety_shields/
├── README.md
├── formal_safety_shields.py
├── shield_evaluator.py
├── docs/
│   └── SCIENTIFIC_UPGRADE.md
├── experiments/
│   ├── eval_safety_shields.py
│   └── eval_shield_stress_test.py
└── results/
    ├── shield_eval.csv
    └── c18_shield_stress_test.csv
```

---

## Quick Start

Run the existing evaluation:

```bash
python contributions/18_formal_safety_shields/experiments/eval_safety_shields.py \
    --n_episodes 50 \
    --out_csv contributions/18_formal_safety_shields/results/shield_eval.csv
```

Run the new stress-test benchmark:

```bash
python contributions/18_formal_safety_shields/experiments/eval_shield_stress_test.py
```

This generates:

```text
contributions/18_formal_safety_shields/results/c18_shield_stress_test.csv
```

---

## Stress-Test Scenarios

| Scenario | Purpose |
|---|---|
| `single_obstacle_direct` | Planner command points directly through an obstacle |
| `narrow_gap` | Robot must pass between nearby obstacles |
| `offset_hazard` | Obstacle is near the nominal route |

Each scenario is evaluated with and without the safety shield.

---

## Metrics

| Metric | Meaning |
|---|---|
| Safety violations | Number of steps below safety radius |
| Minimum obstacle distance | Closest approach to any obstacle |
| Mean correction norm | Average magnitude of command modification |
| Total path length | Executed trajectory length |
| Final goal distance | Remaining distance to goal |
| Minimum STL robustness | Worst temporal-logic robustness margin |
| Intervention rate | Fraction of steps where the shield modified the command |

---

## Scientific Contribution

The upgraded C18 contribution is not simply:

> Add a safety filter to planner commands.

It is stronger:

> Evaluate the safety filter under stress-test scenarios using violation, robustness, correction-cost, and efficiency metrics.

This makes formal shielding experimentally auditable.

---

## Integration

- **Wraps:** any planner command from C01, C03, C07, C13, C21, or C22
- **Complements:** C05 safe mode for higher-level behavioural fallback
- **Uses:** C04 recoverability when deciding whether to continue or stop
- **Can tighten under:** C08 IDS alerts or low trust
- **Can consume:** C12 predicted future occupancy as dynamic obstacles

Recommended runtime interface:

```text
shield_input = {
    desired_velocity,
    robot_position,
    obstacles,
    robot_state,
    stl_specs,
    safety_radius
}
```

---

## Limitations

- The CBF filter uses a lightweight gradient-projection approximation, not a production QP solver.
- The robot is modeled as a point robot.
- Dynamics, actuator limits, latency, and perception uncertainty are simplified.
- Stress-test scenarios are synthetic.
- A software shield does not replace certified hardware emergency stop.

---

## Next Research Step

The strongest extension is risk-adaptive shielding:

```text
uncertainty / risk / IDS alert rises
      ↓
tighten safety radius and STL robustness margin
      ↓
more conservative runtime command filtering
```

This would connect C18 directly to C02, C03, C05, and C08.

---

## Conclusion

Contribution 18 establishes the formal runtime safety layer of DynNav.

The upgraded version makes the contribution more research-ready by evaluating shield effectiveness and cost under explicit stress-test conditions.
