# Mathematical formulation

Robot state: `x_t=(i_t,j_t)`. Occupancy belief: `b_t(c) in {unknown, free, occupied}`. Planning minimizes `J(pi)=sum_{c in pi} [1 + lambda_r R(c) + lambda_u U(c) - lambda_q Q(c)]`, where `R` is risk, `U` is uncertainty, and `Q` is recoverability. Rerouting occurs when blockage, high risk, high uncertainty, or low recoverability violates thresholds. Mission success is reaching the goal without collision or abort.
