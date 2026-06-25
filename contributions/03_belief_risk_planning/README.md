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
## Results

### Experimental Setup

A lambda-sweep experiment was conducted to evaluate the effect of risk weighting on path quality and safety.

The planner optimizes:

J = L + λR

where:

* L = geometric path length
* R = belief-aware risk metric
* λ = risk weighting coefficient

Six different λ values were evaluated.

---

### Quantitative Results

| Metric                  |  Value |
| ----------------------- | -----: |
| Lambda values tested    |      6 |
| Success Rate            |   100% |
| Baseline Risk (λ = 0)   |  0.400 |
| Best Risk (λ = 0.1)     |  0.229 |
| Relative Risk Reduction | 42.75% |
| Path Length Increase    |  0.00% |

---

### Interpretation

The belief-risk planner significantly reduced path risk compared to the risk-neutral baseline.

The lowest observed fused risk was achieved at λ = 0.1, reducing the average risk score from 0.400 to 0.229.

Importantly, this reduction was achieved without increasing geometric path length.

These results demonstrate that incorporating belief-aware risk terms into the planning objective can improve safety while preserving navigation efficiency.

---

### Key Findings

* 100% planning success rate.
* 42.75% reduction in fused path risk.
* No increase in geometric path length.
* Effective safety-efficiency trade-off through risk-aware planning.
* Supports the use of belief-space representations for autonomous navigation under uncertainty.

---

### Conclusion

Contribution 03 demonstrates that belief-aware risk planning can substantially improve navigation safety without sacrificing path efficiency.

The results support the hypothesis that explicitly incorporating uncertainty and risk into the planning objective leads to safer decision-making in dynamic and partially observable environments.



## Integration

- **Receives**: uncertainty from Contribution 02
- **Extended by**: Contribution 12 (diffusion risk maps)
- **Extended by**: Contribution 18 (CBF hard constraints)
