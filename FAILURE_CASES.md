# Failure Cases and Falsification Suite

The current suite is designed to expose where history-conditioned safe-return reasoning helps, where it is unnecessary, and where its approximations or assumptions fail. Negative cases are retained even when they favor a baseline.

| Case | Construction | Required interpretation / falsification signal |
|---|---|---|
| Same state, same history | two executions reach the same cell with identical activated hazards | history-aware and state-only models should agree; a difference indicates an implementation bug |
| Same state, different history | one path traverses the trigger and one avoids it before reaching the same endpoint | exact history-conditioned return values must differ when the trigger probability is nonzero |
| No trigger traversed | risky trigger exists but the executed path never crosses it | persistent history must remain unchanged; planned-path activations are invalid |
| Reverse traversal only | robot crosses the configured edge in the opposite direction | directed trigger must not activate unless explicitly modeled bidirectionally |
| Sampling gap | consecutive robot observations skip one or more grid cells around the trigger | benchmark must mark the interval invalid/unknown rather than inventing an executed transition |
| State-only marginal alias | same-endpoint safe/risky histories are scored using one marginal future-risk field | state-only model should be unable to represent both exact values simultaneously |
| Event not realized | trigger is traversed but paired latent draw exceeds closure probability | no physical closure is applied; planner receives no automatic failure/benefit credit |
| Event off selected route | closure hazard belongs to a trigger not traversed by this planner | event is inactive for this condition even if paired latent draw would close it |
| Series-critical hazards | every declared closure cell is individually critical to return | critical-cut estimate should match the exact independent-closure oracle in this construction |
| Parallel joint cut | no single closure disconnects return, but a combination does | critical-cut approximation may be optimistic; disagreement with exact is expected and must be reported |
| Hard safe-return equivalence | a zero-hazard route satisfies all tested hard probability thresholds | hard constraint may match the history-aware soft route; soft-objective superiority is falsified here |
| Soft objective underweighted | recoverability weight is below the analytic route-switch boundary | planner may rationally accept the risky shortcut; do not label this an algorithm bug |
| False conservatism | trigger probability is zero or the hazardous shortcut is actually harmless | unnecessary detour/path cost is method harm |
| Forward failure, return open | goal route becomes blocked while safe return remains feasible | mission failure must not be labeled irreversible |
| Return cut closes behind robot | executed trigger activates a critical closure after commitment | intended positive mechanism; failure to distinguish history weakens the central claim |
| Probability miscalibration | planner uses nominal `p_hat` while simulator realizes a different frozen `p_true` | measure decision sensitivity; do not reinterpret model probability as calibrated truth |
| Correlated closures | joint closure distribution violates independent Bernoulli assumptions | exact independent oracle is misspecified; robustness requires a correlated model/baseline |
| Delayed revelation | hazard is activated before the robot observes evidence of the closure | separates latent history from robot information and tests partial-observability assumptions |
| Current-cell closure | closure model includes the cell occupied at evaluation time | oracle must respect the protocol convention that the current cell is usable at the evaluation instant |
| Trigger duplication | multiple declarations share a trigger or closure cell | activation/event indexing must remain deterministic and avoid double-counting probability mass |
| Fork held-out | frozen hand-authored geometry with shorter trigger-activating branch and longer safe branch | tests replication outside repeated-module geometry |
| L-room held-out | frozen non-module topology where route lengths can tie despite different history | tests whether representation, not just length, drives the decision |
| Chamber/two-trigger held-out | frozen geometry with multiple trigger opportunities | tests multi-hazard history without claiming broad domain generalization |
| Narrow necessary passage | only mission-feasible route crosses a risky commitment | safe-return reasoning may sacrifice mission feasibility; report the trade-off rather than hiding it |
| Latency scaling | increase number of activated/potential hazards while holding geometry family controlled | exact planner overhead may grow sharply; approximation benefit must be measured with full planning cost |
| Costmap/geometry discretization | vary resolution/inflation while preserving metric-world intent | rank changes reveal representation sensitivity and must be reported |
| Kinodynamic mismatch | grid return path exists but controller/robot cannot execute it | grid connectivity is not a formal viability or hardware-safety guarantee |
| Localization error | robot-belief trigger cell differs from simulator truth | separate robot-observed history from ground-truth scoring; avoid hidden truth leakage |

## Rules

1. **No outcome-based exclusion.** A trial is excluded from efficacy only for a frozen protocol-validity reason, never because a planner performs poorly.
2. **No invented history.** Missing executed transitions, sampling gaps, or planned-path geometry cannot be converted into trigger activations.
3. **No approximation laundering.** Critical-cut results must be labeled as approximation results and accompanied by the known joint-cut failure boundary.
4. **No probability laundering.** Declared closure probabilities are model inputs unless a separate calibration experiment supports a calibration claim.
5. **No universal-winner narrative.** Hard constraints, shortest paths, or state-only models are expected to win or tie in some regimes; those regimes are evidence, not nuisance cases.
6. **Retain negative cases.** Counterexamples and harmful regimes are part of the research artifact set and should remain reproducible.

See `EXPERIMENT_PROTOCOL_V3.md` for current validation semantics and `docs/archive/EXPERIMENT_PROTOCOL_V2_J0J3.md` for the earlier J0–J3 protocol.


---

## V4 partial-observation failure boundaries

These cases apply only to the belief-conditioned research track.

### V4-F1 — Belief does not automatically dominate a conservative prior

The retained development-only two-corridor benchmark gives a deliberate counterexample to a universal belief-planner superiority claim.

Under the medium correctly specified detector:

- belief: mean path 2.286, return-infeasible 0.0696;
- detector-as-truth: mean path 2.286, return-infeasible 0.0696;
- prior-only: mean path 3.000, return-infeasible 0.0000.

The belief improves Brier score relative to the point estimate but does not improve the operational failure rate in this world. The conservative prior avoids the downstream trigger entirely.

**Consequence:** V4 must report a risk/path-cost frontier rather than a single “winner.”

### V4-F2 — Correct Bayes can become conservatively indistinguishable from the prior

Under the miss-heavy development regime:

- belief: mean path 3.000, return-infeasible 0.0000;
- prior-only: mean path 3.000, return-infeasible 0.0000;
- detector-as-truth: mean path 2.004, return-infeasible 0.1378.

The posterior prevents false-safe point-estimate decisions, but in this topology it obtains that protection by making the same route decision as the prior-only rule.

**Consequence:** a safety advantage over detector-as-truth is not enough to establish value over a conservative uncertainty representation.

### V4-F3 — Sensor/model misspecification can invalidate calibration

The V4 protocol explicitly requires overconfident, pessimistic, miss-rate and false-alarm likelihood misspecification. A mathematically exact posterior is only exact for its assumed model.

**Required falsification:** retain cases in which wrong likelihood or arming parameters increase Brier loss, calibration error or false-safe decisions.

### V4-F4 — Exact categorical belief is not a scalable default

With (m) binary latent arming variables, unrestricted belief support can contain (2^m) states. Exact safe-return evaluation can additionally enumerate future closure configurations.

**Consequence:** V4 exact belief planning is a small-hazard reference until scaling evidence establishes otherwise.

### V4-F5 — Receding-horizon predictive belief is not an optimal POMDP policy

The V4 reference A* marginalizes observations that have not yet occurred and replans after real observations. It does not branch over future observations during search.

**Consequence:** compare against an exact finite-horizon observation-contingent policy on small worlds before making policy-quality claims.

### V4-F6 — Equal marginals do not identify joint return risk

In a two-corridor topology with marginal closure probability (p) on each return corridor:

- independent closures give return probability (1-p^2);
- perfectly common-cause closures with the same marginals give (1-p).

**Consequence:** an independent marginal closure model can be systematically optimistic or pessimistic depending on topology/dependence. The correlation study is a model-boundary test, not evidence of arbitrary correlation robustness.
