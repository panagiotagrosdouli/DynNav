# C03 Scientific Upgrade Notes — Risk Trade-Off and Pareto Analysis

## What was already strong

Contribution 03 already captured a central idea of DynNav:

> A robot should not optimize only geometric path length. It should also account for uncertainty-driven risk.

The existing lambda-sweep result reported:

- 100% success rate,
- baseline risk at λ = 0 of 0.400,
- best risk of 0.229,
- relative risk reduction of 42.75%,
- no observed path-length increase in the evaluated benchmark.

This is a strong result because it directly supports uncertainty-aware planning.

## Main weakness before this upgrade

The README described CVaR and risk-aware planning, but the existing experiment did not fully separate:

1. expected risk,
2. tail risk / CVaR,
3. maximum risk,
4. path length cost,
5. Pareto dominance.

A reviewer could ask:

> Did the planner truly find a better safety-efficiency trade-off, or did it only optimize one hand-picked scalar objective?

## New contribution added

C03 now includes:

```text
code/risk_tradeoff_analyzer.py
experiments/eval_risk_tradeoff.py
```

The new utilities evaluate candidate plans using:

- expected risk,
- maximum risk,
- CVaR risk,
- total scalar objective,
- path-length increase,
- relative risk reduction,
- Pareto dominance.

## Why this matters scientifically

Risk-aware planning should not be reduced to a single number.

Two paths can have the same mean risk but very different safety profiles:

```text
Path A: many small risks
Path B: mostly safe, but one dangerous hotspot
```

Expected risk may consider them similar, while CVaR and maximum risk distinguish them.

This matters for autonomous navigation because rare high-risk segments can dominate mission safety.

## Reviewer-safe claim

A stronger claim after this upgrade is:

> Contribution 03 evaluates risk-aware planning as a safety-efficiency trade-off problem. It reports not only scalar objective values, but also expected risk, tail risk, maximum risk, path-length increase, and Pareto dominance.

## New benchmark

Run:

```bash
python contributions/03_belief_risk_planning/experiments/eval_risk_tradeoff.py
```

Output:

```text
contributions/03_belief_risk_planning/results/c03_risk_tradeoff_benchmark.csv
```

The benchmark compares candidate paths such as:

- short but risky corridor,
- medium balanced route,
- long safe route,
- detour with one high-risk hotspot.

## Important distinction

Risk-neutral planning asks:

> What is the shortest feasible route?

Risk-aware planning asks:

> Which route gives the best safety-efficiency trade-off under the selected risk measure?

CVaR-aware planning asks:

> Which route reduces exposure to the worst tail of the risk distribution?

These are not equivalent objectives.

## Limitations

- The new benchmark is synthetic and intentionally small for auditability.
- Real map-based risk fields should be used for final claims.
- CVaR depends on the quality of the underlying risk estimates from C02.
- A scalar lambda cannot express every safety preference.
- A low-risk path can still be unsafe if it violates hard constraints; C18 handles that layer.

## Next research step

The strongest extension is **adaptive lambda selection**.

Instead of choosing λ manually, the planner should adapt λ online based on:

- calibrated uncertainty from C02,
- irreversibility / returnability from C04,
- safe-mode state from C05,
- formal safety margin from C18.

This would make C03 a bridge between probabilistic uncertainty and runtime safety control.