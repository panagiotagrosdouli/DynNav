# Mathematical Formulation

DynNav studies online navigation in an unknown, dynamic environment. The formulation below is a research model used to organize implementation and experiments; it is not a proof of robot safety.

## State and belief

Let the robot state at discrete time `t` be

```math
x_t = (p_t, \theta_t, v_t) \in \mathcal{X},
```

where `p_t` is the grid or metric position, `theta_t` is heading, and `v_t` is velocity. The robot maintains an occupancy-belief map

```math
b_t(m_i) = P(m_i = \mathrm{occupied} \mid z_{1:t}, u_{1:t}),
```

for cells `m_i` given observations `z` and controls `u`. A local costmap is a finite window

```math
C_t \subset b_t
```

around the robot, while a global plan is an ordered sequence

```math
\pi_t = (p_t, p_{t+1}, \ldots, p_T).
```

Dynamic obstacles are represented as a time-indexed set

```math
\mathcal{O}_t = \{o_t^1, \ldots, o_t^K\}.
```

## Uncertainty field

For each cell, DynNav uses Bernoulli entropy as a lightweight uncertainty signal:

```math
U_t(i) = -b_t(m_i)\log b_t(m_i) - (1-b_t(m_i))\log(1-b_t(m_i)).
```

The implementation normalizes this value to `[0, 1]`. Maximum uncertainty occurs near `b_t(m_i)=0.5`.

## Risk field

A risk field combines occupancy risk, obstacle-proximity risk, and dynamic-obstacle risk:

```math
R_t(i) = \mathrm{clip}_{[0,1]}\left(
  \lambda_o b_t(m_i) + \lambda_p \rho(i, \partial\mathcal{O}) + \lambda_d \rho(i, \mathcal{O}_t)
\right).
```

Here `rho` is a decaying proximity kernel. In the current implementation, this is a deterministic prototype using occupancy probabilities and Manhattan-distance decay.

## Recoverability

Recoverability estimates whether the robot can return to a safe origin or fallback set:

```math
\Gamma_t(p) = \mathbb{I}[\exists \pi_{p \rightarrow s}: J(\pi) < \infty] \cdot \frac{1}{1 + \kappa J(\pi_{p \rightarrow s})}.
```

High recoverability means the robot preserves escape routes. Low recoverability can trigger safe mode or rerouting.

## Risk-aware planning objective

For a candidate path `pi`, DynNav minimizes

```math
J(\pi) = \sum_{p_i \in \pi}
\left(
  \alpha \ell(p_i, p_{i+1}) +
  \beta R_t(p_i) +
  \gamma U_t(p_i) +
  \delta (1 - \Gamma_t(p_i))
\right),
```

subject to

```math
R_t(p_i) \leq R_{\max}, \quad
U_t(p_i) \leq U_{\max}, \quad
\Gamma_t(p_i) \geq \Gamma_{\min}
```

when strict safety thresholds are enabled. The default implementation uses soft costs plus a threshold-based supervisor.

## Mission-risk summary

For path cell collision probabilities `q_i`, a conservative mission-risk proxy is

```math
P_{\mathrm{coll}}(\pi) = 1 - \prod_i (1-q_i),
```

combined with a CVaR-style upper-tail summary:

```math
\mathrm{Risk}(\pi) = \max(P_{\mathrm{coll}}(\pi), \mathrm{CVaR}_\alpha(q_1,\ldots,q_n)).
```

## Dynamic rerouting rule

Rerouting is triggered when the active path becomes blocked or any monitored quantity crosses a threshold:

```math
\mathrm{reroute}_t =
\mathbb{I}\left[
\mathrm{blocked}(\pi_t) \lor
\mathrm{Risk}(\pi_t) > \tau_R \lor
U_t(p_t) > \tau_U \lor
\Gamma_t(p_t) < \tau_\Gamma
\right],
```

with a cooldown window to avoid oscillatory replanning.

## Safety supervisor

The safety supervisor maps risk, uncertainty, and recoverability to a mission mode:

```math
\mu_t = f_{\mathrm{sup}}(R_t, U_t, \Gamma_t) \in
\{\mathrm{NOMINAL}, \mathrm{REPLAN}, \mathrm{SAFE\_MODE}, \mathrm{SAFE\_STOP}\}.
```

This is a prototype policy. It is useful for reproducible experiments and transparent ablations, but it is not a certified safety controller.

## Why shortest-path planning is insufficient

A shortest path can be optimal in geometric length while being poor for mission safety. In unknown dynamic environments it can enter narrow passages with low recoverability, traverse uncertain map regions without information-gathering behavior, ignore dynamic-obstacle proximity, and postpone rerouting until a path is already blocked. DynNav therefore treats risk, uncertainty, and recoverability as first-class planning signals rather than post-hoc diagnostics.
