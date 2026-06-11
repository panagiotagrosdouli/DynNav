# Contribution 03 — Belief-Space & Risk-Aware Planning

[![Module](https://img.shields.io/badge/Module-03-purple)](.) [![Type](https://img.shields.io/badge/Type-Risk--Aware%20Planning-blue)](.) [![Status](https://img.shields.io/badge/Status-Core-brightgreen)](.)

## Overview

Extends classical A* with **belief-space representations** and **risk-weighted cost functions**. The planner explicitly reasons about uncertainty and trades off path efficiency against collision risk using Conditional Value-at-Risk (CVaR) optimisation.

## Research Question

> **RQ3**: How should robots reason about risk and safety in dynamic environments?

## How It Works

```
Belief state (μ, Σ) + occupancy → risk map → CVaR cost → risk-weighted A* → safe path
```

- Risk cost: `c_risk(s) = CVaR_α(collision_prob_at_s)`
- Total cost: `f(s) = g(s) + λ·r(s) + h(s)`
- λ controls safety/efficiency trade-off

## Files

```
03_belief_risk_planning/
├── experiments/
└── results/
```

## Quick Start

```bash
python contributions/03_belief_risk_planning/experiments/eval_belief_risk.py
```

## Results

A lambda-sweep experiment was conducted to evaluate the trade-off between geometric path length and belief-aware risk cost.

### Experimental Setup

- 6 lambda values evaluated.
- Risk-aware objective:

J = L + λR

where:
- L = geometric path length
- R = fused belief-risk metric
- λ = risk weighting coefficient

### Results

| Metric | Value |
|----------|----------|
| Lambda values tested | 6 |
| Success rate | 100% |
| Baseline risk (λ=0) | 0.400 |
| Best risk (λ=0.1) | 0.229 |
| Risk reduction | 42.75% |
| Path length increase | 0.00% |

### Interpretation

The belief-risk planner successfully reduced fused path risk by 42.75% relative to the risk-neutral baseline while maintaining identical geometric path length.

This demonstrates that incorporating belief-aware risk terms into the planning objective can improve safety without sacrificing path efficiency in the evaluated benchmark.


## Risk Metrics

| Metric | Formula | Use |
|--------|---------|-----|
| Expected risk | E[collision] | Average-case planning |
| CVaR-95 | E[risk \| top 5%] | Conservative planning |
| Worst-case | max(risk) | Safety-critical |

## Integration

- **Receives**: uncertainty from Contribution 02
- **Extended by**: Contribution 12 (diffusion risk maps)
- **Extended by**: Contribution 18 (CBF hard constraints)
