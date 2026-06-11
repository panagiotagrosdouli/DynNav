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

A threshold sweep was conducted to evaluate irreversibility-aware planning and safe-mode recovery.

### Experimental Setup

The planner was evaluated under different irreversibility thresholds `τ`.

Two modes were compared:

- Hard threshold mode: planning fails when no path satisfies the strict irreversibility bound.
- Safe mode: the planner relaxes `τ` to the smallest feasible threshold when the nominal bound is too strict.

### Quantitative Results

| Metric | Value |
|----------|----------:|
| Hard threshold success rate | 26.7% |
| Minimum feasible τ | 0.85 |
| Safe-mode success rate | 100% |
| Safe-mode relaxed cases | 15 / 26 |
| Mean τ relaxation gap | 0.080 |
| Safe-mode path length | 45 |
| Mean irreversibility on path | 0.480 |
| Max irreversibility on path | 0.850 |
| Returnability sweep success rate | 100% |

### Interpretation

The hard irreversibility threshold admitted paths only when `τ ≥ 0.85`, resulting in a success rate of 26.7%.

Safe mode preserved feasibility in all evaluated cases by relaxing the irreversibility threshold to the smallest viable value. This demonstrates that returnability-aware safe mode can avoid silent planning failure while still enforcing an explicit recoverability constraint.

Contribution 04 therefore supports safe navigation by identifying irreversible regions and providing a fallback mechanism when strict irreversibility constraints would otherwise make planning infeasible.
