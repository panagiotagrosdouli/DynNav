# C00 Core Research Audit

**Source:** `b626d6e9b5bf8b8cf1ec87906597d767224f5f37`. C00 is the history-conditioned safe-return research platform, not another numbered module.

## Implemented formulation found

`dynnav/recoverability_belief.py` defines an exact oracle for the probability of remaining connected to a designated safe set after future closure events. It enumerates Bernoulli closure realizations independently; exact enumeration is exponential and guarded by `max_hazard_cells` (default 16). The robot's current cell is conditioned usable at the decision instant. These probabilities describe future topology invalidation, not occupancy probability.

`dynnav/planners/commitment_safe_return_astar.py` searches augmented states `(cell, active_closure_indices)`. Executed transitions activate hazards; each successor is rejected when its exact safe-return probability is below the configured hard threshold. Its Manhattan heuristic is admissible for geometric step cost when `heuristic_weight <= 1`; values above 1 can make weighted A* non-optimal, so optimality needs that condition.

`dynnav/recoverability_cut.py` scores individually critical hazards and multiplies survival probabilities. Under independent closures, each individually critical cell must remain open, so the result is an **upper bound**; joint multi-cell cutsets can make it optimistic. It is an estimator, not an exact oracle.

## C04 relationship

C04's graph-based returnability/irreversibility profiles capture structural bottlenecks and return options. C00's hazard-conditioned probability additionally models stochastic future closures activated by action history. Deterministic connectivity is a special case when there are no hazards or closure probabilities are deterministic. They are not numerically interchangeable when C04 uses a structural proxy or when C00 conditions on activated closure history.

## Evidence and limitations

The C01-C26 suite passed C04's structural smoke experiment (4 rows), but it does not execute the central C00 planner. No fresh C00 Gazebo or hardware test was run here. Separately, the C27 finite counterexample runner exercised the shared exact closure oracle on a four-hazard graph. Existing C00 experiment modules, prior result folders, ROS 2 workspace/configuration and tests exist, but stored artifacts are not re-labelled as fresh evidence.

Independence of future closure events is an explicit modeling assumption; correlated closures need a joint belief. Exact enumeration scales as `2^m`; approximation error and runtime should be checked against the oracle on exhaustive small worlds. The safe set, closure timing, and observation semantics must match the target robot task. Re-run targeted recoverability tests and the frozen ROS 2/Gazebo action-trigger protocol in an environment with pytest, ROS 2 and Gazebo.
