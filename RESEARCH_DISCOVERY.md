# DynNav research discovery: uncertain trigger execution and observation

**Status: provisional research track; not a novelty claim or submission-ready study.**

## Decision

The strongest implementable question emerging from the current code is:

> When a trigger edge may or may not have been executed, how much does a noisy or miscalibrated crossing detector change safe-return risk estimates and false-safe decisions, compared with a Bayesian belief over trigger activation?

This is a narrow model-boundary and robustness study. It does **not** claim a new POMDP, belief update, safe-return planner, or Bayesian navigation algorithm. Existing work establishes each of those ingredients. The literature screen below does not establish that this exact combination is absent; it identifies a testable intersection that would need a broader, recorded review before any novelty statement.

## Literature map and claim boundaries

| Prior work | What it establishes | Consequence for DynNav |
|---|---|---|
| Kneebone & Dearden, *Navigation Planning in Probabilistic Roadmaps with Uncertainty*, ICAPS 2009, [DOI](https://doi.org/10.1609/icaps.v19i1.13359) | Noisy observations during traversal of uncertain roadmap edges can be planned as a POMDP using belief-state methods. | No claim that noisy edge sensing, belief states, or POMDP navigation is new. |
| Guo et al., *Hierarchical Motion Planning under Probabilistic Temporal Tasks and Safe-Return Constraints*, IEEE TAC 2023, [DOI](https://doi.org/10.1109/TAC.2023.3244884) | Probabilistic planning with explicit safe-return constraints and outbound/return policies. | No claim that safe-return planning under uncertainty is new. |
| Kameyama et al., AFADA, ICRA 2021, [DOI](https://doi.org/10.1109/ICRA48506.2021.9561111) | An active modular environment can alter topology and offload representation/planning in stochastic settings. | Dynamic topology is established; DynNav's trigger semantics are a different model detail, not a blanket novelty claim. |
| Xiao et al., *Robot Risk-Awareness by Formal Risk Reasoning and Planning*, RA-L 2020, [DOI](https://doi.org/10.1109/LRA.2020.2974434) | Formal treatment of robot risk in planning, including action-dependent risk. | Risk-aware planning is established. |
| Axelrod et al., *Provably Safe Robot Navigation with Obstacle Uncertainty*, RSS 2017, [DOI](https://doi.org/10.15607/RSS.2017.XIII.023) | Safety evaluation and planning from imperfect obstacle observations. | Uncertain-obstacle safety is established. |
| Zhou & Ceyhan, *Stochastic Path Planning in Correlated Obstacle Fields*, arXiv:2509.19559 (2025), [arXiv](https://arxiv.org/abs/2509.19559) | Correlated obstacle beliefs, noisy sensing, Bayesian updates, and navigation planning. | Generic correlated-obstacle belief planning is also not a defensible novelty claim. It is a preprint and should be treated as such. |
| Robotics POMDP survey, arXiv:2107.07599 (2021), [arXiv](https://arxiv.org/abs/2107.07599) | POMDPs model stochastic action effects and partial observation; belief-state planning carries substantial computational cost. | The proposed exact update is standard Bayes filtering over a deliberately small discrete state. |

Other nearby contingency-planning and dynamic-topology papers reinforce that the search space is active. This scan is selective rather than systematic: it lacks database-by-database query logs, title/abstract screening, backward/forward citation chaining, and exhaustive full-text review. Therefore no “first,” “unexplored,” or “no prior work” wording is supported.

### Candidate research questions considered

| Candidate | Potential contribution | Main overlap or weakness | Decision |
|---|---|---|---|
| A. Deterministic action-triggered closures require transition history | Show geometric-state-only returnability can alias two histories with different active hazards. | Markovization by augmenting the state with relevant history is standard; this is already the project's controlled substrate and has narrow scope alone. | Keep as motivating mechanism, not headline contribution. |
| B. Noisy trigger execution and crossing observation distort safe-return decisions | Separate physical execution, sensor report, and future closure; quantify calibration and false-safe consequences; compare posterior and point-estimate baselines. | Generic POMDP/Bayes filtering and uncertain navigation are established; the exact intersection remains unverified. | **Select provisionally** as a falsifiable robustness benchmark. |
| C. Correlated closure events and graph reliability | Extend exact return probability to correlated topology changes. | Correlated obstacle-field planning and Bayesian inference are already active; broad graph reliability also has mature literature. No clear algorithmic distinction yet. | Reject until a specific dependency model and advantage are shown. |
| D. Exact history compression or bisimulation | Reduce the state space of history-conditioned hazards. | State aggregation/bisimulation are standard, and no scale result currently motivates the added theory. | Reject for this iteration. |
| E. Multi-robot activation and recovery | Share observations and coordinate safe return. | Large scope expansion; current code has no multi-robot model or baselines. | Reject for this iteration. |

## Model and exact update

Let `A` be the random set of trigger hazards activated after a commanded transition. An attempted trigger `i` is physically crossed with probability `q_i`. Conditional on crossing, hazard `i` activates. A detector observation `Y` has sensitivity `s = P(Y=1 | crossed)` and specificity `c = P(Y=0 | not crossed)`. A later route closure has probability `p_i` conditional on activation; it is a separate random event from both execution and detection. The robot's current cell is observed and conditioned usable, consistent with the existing exact returnability oracle.

The implementation stores `b(A) = P(A | observation history)`. For a single trigger attempt and binary observation `y`, the exact update is

\[
b'(A') \propto \sum_A b(A)\sum_{e\in\{0,1\}}
P(e\mid q_i)\,P(y\mid e,s,c)\,
\mathbf{1}[A'=A\cup(\{i\}\text{ if }e=1)].
\]

For each candidate active set, the posterior-predictive returnability is

\[
P(\text{return}\mid y)=\sum_A b'(A)\,P(\text{return}\mid A),
\]

where `P(return | A)` is evaluated by the existing exact independent-closure enumerator. In a deployment using a risk budget `ε`, a policy could declare the current state return-safe only when `1 - P(return | y) ≤ ε`. This benchmark measures the simpler equivalent failure-risk threshold, and does not implement a route planner or runtime controller.

For one trigger, before any observation, true return-failure probability is `q_i p_i`. With detector report `y=1`, Bayes gives

\[
P(e=1\mid y=1)=\frac{q_i s}{q_i s+(1-q_i)(1-c)};
\]

with report `y=0`, replace the numerator by `q_i(1-s)` and the denominator by `q_i(1-s)+(1-q_i)c`. These expressions also make the key failure mode explicit: using incorrect `s,c` can make a mathematically valid posterior miscalibrated.

### Assumptions and scope

- Trigger crossings are Bernoulli and activate their associated hazards monotonically.
- Sensor detections are conditionally independent given the crossing state and use one fixed sensitivity/specificity pair.
- Future closures are independent conditional on the active hazards, matching the current exact closure oracle.
- The benchmark uses one trigger and one later closure event per trial; the code's belief supports multiple trigger indices but has no state-space approximation.
- Localization, detector delay, repeated crossings, unknown sensor parameters, correlated closures, and Nav2 execution uncertainty are not modeled.
- The “oracle” baseline sees physical crossing. It is an upper-information reference, not an implementable sensor method.

## Implemented experiment

Run from the repository root with `PYTHONPATH=. python scripts/run_noisy_activation_benchmark.py --trials 100000 --seed 20260924 --output-dir results/noisy_activation`. Every method is paired on the same generated activation, observation, and closure trial. The fixed safe-decision threshold is predicted failure probability `≤ 0.20`; the false-safe rate is the fraction of accepted decisions that actually failed. Brier score evaluates predicted failure probability against realized closure failure.

The six predeclared cases vary sensor quality, calibration, and trigger activation probability. Selected results from 100,000 trials per case:

| Scenario | Method | Empirical failure | Mean predicted failure | Brier | False-safe among safe decisions | Safe-decision rate |
|---|---|---:|---:|---:|---:|---:|
| Informative, correctly specified sensor | Bayesian posterior | 0.4007 | 0.4007 | 0.1374 | 0.0793 | 0.4988 |
|  | Prior only | 0.4007 | 0.4000 | 0.2401 | 0.0000 | 0.0000 |
|  | Detector treated as truth | 0.4007 | 0.4009 | 0.1437 | 0.0793 | 0.4988 |
| Weak, correctly specified sensor | Bayesian posterior | 0.4020 | 0.4002 | 0.2339 | 0.0000 | 0.0000 |
|  | Prior only | 0.4020 | 0.4000 | 0.2404 | 0.0000 | 0.0000 |
|  | Detector treated as truth | 0.4020 | 0.4009 | 0.3359 | 0.3212 | 0.4989 |
| Missed activation; assumed sensitivity 0.95, actual 0.60 | Bayesian posterior | 0.3996 | 0.2809 | 0.2256 | 0.2481 | 0.6498 |
|  | Prior only | 0.3996 | 0.4000 | 0.2399 | 0.0000 | 0.0000 |
| High activation (0.8), correctly specified sensor | Bayesian posterior | 0.6392 | 0.6408 | 0.2068 | 0.0000 | 0.0000 |
|  | Detector treated as truth | 0.6392 | 0.4659 | 0.2944 | 0.4567 | 0.4176 |

The informative calibrated detector improves Brier score over the prior; a weak detector gives only a small improvement. Treating the detector report as physical truth performs poorly, especially in the weak-sensor case. Most importantly, a sensor model with sensitivity overstated from 0.60 to 0.95 yields severe underprediction and a 24.8% false-safe rate among decisions called safe. The prior-only rule is conservative at the chosen threshold in the `q=0.5, p=0.8` cases because its predicted failure is 0.4, so its zero false-safe rate is achieved by making no safe decisions. That is a safety/availability tradeoff, not an overall win.

Outputs are committed as [`CSV`](results/noisy_activation/noisy_activation_summary.csv), [`summary JSON`](results/noisy_activation/noisy_activation_summary.json), and [`run metadata`](results/noisy_activation/run_metadata.json), which records trials, per-scenario seeds, threshold, methods, and metrics. These are Monte Carlo point estimates from one fixed seed; no confidence intervals or hardware claims are made. A complete paper protocol should repeat independent seeds, include uncertainty intervals, sweep the decision threshold, vary `q,p,s,c`, and pre-register primary metrics.

## Falsifiable claims for the next study

1. **Calibration benefit:** Under correctly specified sensitivity/specificity and informative observations, posterior estimates reduce Brier score against a prior-only activation estimate. Falsified if paired results show no robust reduction across the declared grid of `q,p,s,c` values.
2. **Detector-as-truth failure:** A point estimate that sets activation equal to the detector report increases false-safe decisions when the detector is imperfect. Falsified if this does not occur across predeclared sensor-quality sweeps at equal risk thresholds.
3. **Model-misspecification hazard:** An exact posterior using miscalibrated sensor parameters can be less reliable for safety decisions than the prior. Falsified if no parameter region exhibits elevated false-safe rate or calibration error under the predeclared sweep.
4. **Operational value:** Belief-aware decisions improve the safety/availability frontier, not merely Brier score. Evaluate false-safe rate against safe-decision coverage across thresholds and compare against prior-only and detector-as-truth policies.

The current simulator demonstrates examples for claims 1–3 but does not yet supply a threshold frontier, confidence intervals, held-out calibration fit, systematic sweep, or ROS 2 integration. Claim 4 therefore remains open.

## Implementation and computational limits

`dynnav/activation_belief.py` implements exact belief updates and posterior-predictive safe-return probability. With `m` independent binary activation hypotheses, an unrestricted categorical belief can contain up to `2^m` active sets. For each set, exact topology closure evaluation enumerates up to `2^h` future closure realizations (`h ≤ 16` under the existing oracle default). This is an auditable small-case reference implementation, not a scalable online planner. The benchmark runner is in `dynnav/experiments/noisy_activation_benchmark.py`; focused tests are in `tests/test_activation_belief.py`.

## Recommendation

Keep the original deterministic transition-history study as the controlled substrate and maintain this as a separate provisional robustness track. Do not rewrite the manuscript around it or claim novelty yet. The current evidence supports an implementation and a falsifiable small synthetic benchmark, not a publication-ready scientific contribution. The next useful research step is a systematic literature screen and an expanded parameter-sweep experiment with uncertainty intervals, followed by ROS 2/Nav2 integration only if the abstract model remains consequential under logged executed-transition data.
