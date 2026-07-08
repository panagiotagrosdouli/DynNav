# Risk Estimation

DynNav estimates mission risk from occupancy probabilities along a planned path. The prototype combines cumulative collision probability with a CVaR-style tail-risk statistic.

## Objective

The planner minimizes an additive cost:

```text
step_cost = 1 + risk_weight * p(occupied) + returnability_penalty
```

This objective favors shorter paths when risk is low, but penalizes high-uncertainty or likely occupied cells.

## Scientific motivation

Expected path cost can underestimate rare but severe outcomes. Tail-risk summaries such as Conditional Value-at-Risk focus on the upper-cost region and are appropriate when safety violations are asymmetric.

## Engineering motivation

The implemented risk metric is deterministic, fast, and easy to log. It can be used in CI benchmarks and compared against classical shortest-path baselines.

## Limitations

The current implementation assumes independent cell probabilities when estimating cumulative collision probability. It should be treated as a conservative prototype rather than a calibrated safety guarantee.
