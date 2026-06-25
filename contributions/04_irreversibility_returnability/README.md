# Contribution 04 — Irreversibility & Returnability

[![Module](https://img.shields.io/badge/Module-04-purple)](.) [![Type](https://img.shields.io/badge/Type-Safety%20%2F%20Planning-blue)](.) [![Status](https://img.shields.io/badge/Status-Core-brightgreen)](.)

## Overview

Prevents the robot from entering **unrecoverable states** by checking returnability before committing to any action. A state is returnable if the robot can reach a safe base position from it under current uncertainty.

## Research Question

> **RQ4**: How can navigation systems avoid irreversible decisions?

## How It Works

```
Candidate action → simulate forward → check: can robot return to safe state? → allow/block
```

- **Returnability check**: backward reachability analysis from candidate state
- **Feasibility threshold**: minimum clearance required for U-turn / recovery
- **Integration**: pre-screens actions before A* commitment

## Files

```
04_irreversibility_returnability/
├── experiments/
└── results/
```

## Quick Start

```bash
python contributions/04_irreversibility_returnability/experiments/eval_returnability.py
```

## Key Concepts

- **Returnable state**: ∃ path back to safe zone under current map + uncertainty
- **Irreversibility penalty**: added to cost of states with low returnability
- **Dead-end detection**: graph pruning of states with no return path

## Integration

- **Pre-screens**: all candidate actions before execution
- **Extended by**: Contribution 13 (world model mental rollouts for pre-screening)
- **Extended by**: Contribution 18 (CBF as hard irreversibility barrier)

## Results

### Experimental Setup

Contribution 04 evaluates whether returnability-aware planning can maintain feasibility when strict irreversibility constraints would otherwise prevent path generation.

A threshold sweep was performed over the irreversibility parameter τ.

Two planning modes were compared:

* Hard-threshold planning
* Returnability-aware safe mode

---

### Quantitative Results

| Metric                           |   Value |
| -------------------------------- | ------: |
| Hard-threshold success rate      |   26.7% |
| Minimum feasible τ               |    0.85 |
| Safe-mode success rate           |    100% |
| Safe-mode relaxed cases          | 15 / 26 |
| Mean τ relaxation gap            |   0.080 |
| Safe-mode path length            |      45 |
| Mean irreversibility on path     |   0.480 |
| Maximum irreversibility on path  |   0.850 |
| Returnability sweep success rate |    100% |

---

### Interpretation

The hard-threshold planner frequently failed because no path satisfied the imposed irreversibility constraint.

Safe mode recovered feasibility by automatically relaxing τ to the smallest viable value whenever the nominal threshold produced no valid solution.

Importantly, the relaxation remained small on average (Δτ = 0.080), indicating that feasibility was restored without substantially weakening the safety requirement.

---

### Key Findings

* Hard-threshold planning succeeded in only 26.7% of evaluated cases.
* Returnability-aware safe mode achieved a 100% success rate.
* Feasibility was recovered in 15 of 26 evaluated threshold configurations.
* The required threshold relaxation remained small.
* Returnability analysis successfully prevented silent planning failure.

---

### Conclusion

Contribution 04 demonstrates that returnability-aware safe mode can preserve planning feasibility under strict irreversibility constraints.

Rather than guaranteeing avoidance of all irreversible states, the method provides a practical safety mechanism that identifies infeasible constraints and adapts them to the minimum viable level required for successful planning.


### Interpretation

The hard irreversibility threshold admitted paths only when `τ ≥ 0.85`, resulting in a success rate of 26.7%.

Safe mode preserved feasibility in all evaluated cases by relaxing the irreversibility threshold to the smallest viable value. This demonstrates that returnability-aware safe mode can avoid silent planning failure while still enforcing an explicit recoverability constraint.

Contribution 04 therefore supports safe navigation by identifying irreversible regions and providing a fallback mechanism when strict irreversibility constraints would otherwise make planning infeasible.
