# Route-Level Recoverability Metric

## Purpose

The metric separates **immediate route risk** from **retained future recovery freedom**. A route can have low collision risk while still making a fragile commitment through a bottleneck or cul-de-sac.

For a route

\[
\pi=(x_0,\ldots,x_T),
\]

let \(R_{\mathrm{rec}}(x_t)\in[0,1]\) be the auditable node-level recoverability estimate already produced by Contribution 04.

## Profile quantities

### Weakest recoverability

\[
R_{\min}(\pi)=\min_t R_{\mathrm{rec}}(x_t).
\]

This captures the weakest point of the route.

### Cumulative recoverability loss

\[
D_{\mathrm{loss}}(\pi)=
\sum_{t=1}^{T}
\left[R_{\mathrm{rec}}(x_{t-1})-R_{\mathrm{rec}}(x_t)\right]_+.
\]

This is intentionally different from endpoint loss. Repeated commitments into fragile regions remain visible even when a route later returns to a state with the same terminal recoverability.

### Maximum single-step loss

\[
D_{\max}(\pi)=
\max_t
\left[R_{\mathrm{rec}}(x_{t-1})-R_{\mathrm{rec}}(x_t)\right]_+.
\]

This identifies abrupt commitment transitions suitable for runtime-supervisor thresholds.

### Bottleneck exposure

For local bottleneck score \(b(x_t)\in[0,1]\),

\[
B(\pi)=\frac{1}{T+1}\sum_{t=0}^{T} b(x_t).
\]

## Route fragility penalty

The initial interpretable penalty is

\[
\Phi(\pi)=
w_{\min}(1-R_{\min}(\pi))
+w_D D_{\mathrm{loss}}(\pi)
+w_B B(\pi),
\]

with non-negative weights.

The integrated planner objective will be evaluated as

\[
J(\pi)=L(\pi)
+\lambda_r\operatorname{CVaR}_{\alpha}(r(\pi))
+\lambda_i\Phi(\pi).
\]

## Falsifiable hypotheses

1. Routes with similar risk can have significantly different \(\Phi(\pi)\).
2. Lower \(\Phi(\pi)\) predicts higher recovery success after controlled route invalidation.
3. Cumulative degradation predicts failure better than terminal recoverability alone.
4. Adding \(\Phi(\pi)\) improves recovery and mission success compared with risk-only planning, with measurable efficiency cost.

## Evidence boundary

The current score is a transparent grid-world planning signal. It is not a reachability certificate, viability guarantee, or proof of collision avoidance. The paper must preserve this distinction.
