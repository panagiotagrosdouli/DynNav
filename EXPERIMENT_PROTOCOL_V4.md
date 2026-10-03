# Experiment Protocol V4 — Belief-Conditioned Safe Return

**Protocol status:** pre-outcome research protocol  
**Freeze date:** 2026-10-03  
**Branch:** \`research/belief-conditioned-v4\`

V4 extends the V3 known-history study. It does not invalidate V3 retained evidence. V4 introduces latent hazard arming, noisy observations of that latent state, belief-conditioned planning, and a separate correlated-closure study.

No publication-facing V4 outcome may be used unless it is generated after the relevant implementation, scenario manifest, analysis code, and configuration are frozen and retained with raw artifacts.

## 1. Scientific questions

**RQ1 — Representation:** when hazard arming is hidden, does a posterior over armed hazards carry safe-return information lost by geometric/fixed-marginal state?

**RQ2 — Decision value:** does belief-conditioned information change route selection and improve the return-risk/path-cost trade-off?

**RQ3 — Calibration:** are posterior-predictive return probabilities calibrated under correct specification, and how do they degrade under misspecification?

**RQ4 — Correlation:** how much error arises when the planner assumes independent closures while the true future topology is correlated?

**RQ5 — Boundaries:** when does belief tracking add no value or become computationally impractical?

## 2. Causal semantics

For hazard \(i\):

\[
h_i=(e_i,q_i,c_i,p_i),
\]

where \(e_i\) is a directed trigger, \(q_i\) is the conditional probability of arming after trigger execution, \(c_i\) is the future closure event/cell, and \(p_i\) is the closure probability conditional on arming.

The event order is:

1. the robot executes a known trigger transition \(e_i\);
2. latent arming is sampled using \(q_i\);
3. the planner receives a noisy arming observation;
4. planning continues using its permitted information state;
5. future closure realization is sampled using \(p_i\);
6. post-closure return feasibility is evaluated.

A planned-but-unexecuted trigger never changes persistent truth or belief.

## 3. Latent-state dynamics

Let \(A_{i,t}\in\{0,1\}\) be monotone armed state.

After executing trigger \(e_i\):

\[
A_{i,t+1}=A_{i,t}\lor B_{i,t},
\qquad
B_{i,t}\sim \operatorname{Bernoulli}(q_i).
\]

If the trigger is not executed:

\[
A_{i,t+1}=A_{i,t}.
\]

The V3 model is the special case \(q_i=1\) with perfect knowledge of \(A\).

## 4. Observation model

For observation \(Y_i\in\{0,1\}\):

\[
P(Y_i=1\mid A_i=1)=s,
\]

\[
P(Y_i=0\mid A_i=0)=c,
\]

where \(s\) is sensitivity and \(c\) is specificity.

The planner updates

\[
b_t(A)=P(A_t=A\mid u_{0:t-1},Y_{0:t}).
\]

For the exact small-hazard reference method, posterior support is categorical over armed-hazard sets.

## 5. Future-closure model

### 5.1 Primary model

Conditional on armed state, closure events are independent Bernoulli variables with probabilities \(p_i\).

### 5.2 Separate correlated model

Correlation is studied separately. Do not mix closure-correlation conclusions with activation-observation conclusions.

## 6. Planner conditions

### P0 — shortest path

Geometric shortest path. No hazard information.

### P1 — state-only fixed marginal

Uses the exact return-connectivity oracle but applies a fixed marginal hazard field independent of executed arming observations.

Purpose: representation ablation.

### P1b — prior-only predictive belief

Propagates the declared arming model after executed triggers but ignores detector observations. It therefore retains uncertainty induced by action exposure without receiving observation information.

Purpose: strong conservative information-ablation baseline. The development study showed that this comparator can match or outperform P4 operationally by accepting longer routes; it is therefore mandatory in all primary V4 risk/cost analyses.

### P2 — activation oracle

Receives the true latent armed set \(A_t\).

Purpose: upper-information reference. Not a realistic deployment condition.

### P3 — latched detector-as-truth

Uses a naive monotone point estimate consistent with the monotone arming model: once any detector observation reports hazard (i) as armed, the estimator retains (i) as armed for the rest of the mission. A negative observation never clears a previously latched positive.

Before the first positive observation, the hazard is treated as inactive.

Purpose: tests overconfidence from collapsing posterior uncertainty to a binary persistent state. This baseline is intentionally distinct from the Bayesian posterior and its latching semantics must remain fixed across all V4 runs.

### P4 — belief-conditioned

Maintains the exact posterior over armed sets and uses posterior-predictive safe-return reliability

\[
R(x,b)=\sum_A b(A)R(x,A).
\]

This is the primary proposed representation.

### P5 — hard belief-safe-return

Uses the same belief and oracle as P4 but rejects successors with

\[
R(x,b)<\tau.
\]

Purpose: separate representation value from soft-objective choice.

### P6 — exact small-world belief-policy reference (tiny worlds only)

For at most three uncertain hazards and short horizon, solve an exact finite-horizon belief-policy problem by exhaustive dynamic programming/branching over observations.

Purpose: quantify the approximation in P4. P4 must not be described as a general optimal POMDP solver.

## 7. Main planner semantics

P4 is a receding-horizon predictive-belief planner.

At each executed step:

1. start from current posterior \(b_t\);
2. for candidate search transitions, propagate arming uncertainty caused by hypothetical trigger execution;
3. before a hypothetical future observation exists, marginalize over that unseen observation;
4. compute predictive safe-return reliability;
5. execute only the next transition;
6. receive the actual observation;
7. perform the Bayes update;
8. replan.

Any future-observation branching implementation must be labeled separately.

## 8. Objective settings

Primary soft cost:

\[
c(z,z')=1+\lambda\left(1-R_{\mathrm{return}}(z')\right).
\]

Primary value:

\[
\lambda=8,
\]

inherited from the existing V3 publication setting to avoid selecting a new headline value from V4 test outcomes.

Primary hard threshold:

\[
\tau=0.90.
\]

Secondary predeclared sensitivity:

\[
\lambda\in\{1,2,4,8,16\},
\qquad
\tau\in\{0.70,0.80,0.90,0.95\}.
\]

No held-out result may be used to select the headline hyperparameter.

## 9. Observation regimes

| Regime | Sensitivity | Specificity | Role |
|---|---:|---:|---|
| O0 | 1.00 | 1.00 | perfect-information control |
| O1 | 0.95 | 0.95 | mild symmetric noise |
| O2 | 0.85 | 0.85 | **primary imperfect-observation regime** |
| O3 | 0.70 | 0.70 | severe symmetric noise |
| O4 | 0.70 | 0.95 | miss-heavy |
| O5 | 0.95 | 0.70 | false-alarm-heavy |
| O6 | 0.50 | 0.50 | uninformative control |

Primary operational/calibration comparison: **P4 vs P3 under O2**.

Mandatory strong-baseline comparison: **P4 vs P1b under O2**, reported on both return risk and path cost. No V4 operational-superiority claim is authorized if it depends on omitting P1b.

O0 is a mandatory sanity control: when the observation model is perfect, belief and detector-as-truth should agree up to implementation/tie-breaking details.

O6 is a mandatory information-null control: observations should add no information beyond the predictive prior.

## 10. Arming and closure parameters

Use frozen values drawn from:

\[
q_i\in\{0,0.4,0.7,1.0\},
\]

\[
p_i\in\{0,0.25,0.50,0.80\}.
\]

Zero values are reserved for explicit null controls; non-null generated scenarios must contain at least one \(q_i>0\) and \(p_i>0\).

Multi-hazard scenarios should include heterogeneous \(q_i,p_i\) values.

The scenario manifest is authoritative after freeze.

## 11. Environment families

The held-out suite contains 96 scenarios: 12 from each of eight families.

### F1 — bridge/detour
Short trigger-exposed route versus longer return-preserving route.

### F2 — asymmetric fork
Alternative outbound branches arm different hazards with different return consequences.

### F3 — loop/redundant return
At least two return routes; single-cell criticality is insufficient.

### F4 — chamber multi-trigger
Multiple possible trigger histories reach the same region.

### F5 — parallel joint cut
Individually noncritical closures jointly disconnect return.

### F6 — unavoidable-hazard choice
Every feasible outbound path arms at least one hazard; methods must select which exposure, not merely avoid all exposure.

### F7 — multiple safe regions
Closures alter which safe target remains reachable.

### F8 — null/history-irrelevant
Triggers are irrelevant to safe return, or \(q=0\)/\(p=0\). Information-aware planners should not manufacture advantage.

Every scenario must pass machine-checkable topology contracts before stochastic evaluation.

## 12. Data split

### Development
48 scenarios. Outcomes may be inspected for debugging and implementation development.

### Validation
48 scenarios. Used for numerical checks and already-declared engineering decisions.

### Held-out test
96 scenarios. Outcomes remain hidden until:

- planner semantics are frozen;
- generator code is frozen;
- scenario manifest is committed;
- primary configuration is frozen;
- unit/property tests pass;
- raw artifact schema is frozen;
- statistics/calibration scripts are frozen.

Generator seeds:

- development: \`2026100301\`
- validation: \`2026100302\`
- held-out: \`2026100303\`

The emitted scenario files, not seeds alone, become the retained source of truth.

## 13. Stochastic sample size

Primary O2 held-out test:

- 96 scenarios;
- 250 paired execution seeds per scenario;
- fixed sample size;
- 24,000 paired executions per planner.

This sample size is chosen for continuity with V3 and stable scenario-level estimation; it is not described as a formal prospective power calculation.

Secondary O0/O1/O3/O4/O5/O6 analyses may use 100 paired seeds per scenario if the compute budget requires it, **but that choice must be committed before any secondary test outcome is viewed**.

No outcome-based early stopping or outcome-based sample-size increase is allowed.

## 14. Common random numbers

Stochastic variables are keyed, not consumed sequentially by planner order.

Key:

\`\`\`text
(scenario_id, execution_seed, hazard_id, event_type, occurrence_index)
\`\`\`

Required event types:

- \`arming\`
- \`observation\`
- \`closure\`
- \`correlation_mixture\`
- \`correlation_common_draw\`
- \`correlation_independent_draw\`

Planner route divergence must not shift another planner's latent random draws.

## 15. Primary endpoints

### 15.1 Operational

Post-closure return-infeasible indicator at the outbound evaluation point.

Primary effect:

\[
\Delta_{\mathrm{risk}}
=
\mathrm{risk}(P4)-\mathrm{risk}(P3)
\]

under O2.

Negative values favor P4.

### 15.2 Probabilistic/calibration

Brier score of final predicted return probability against realized return feasibility.

Primary effect:

\[
\Delta_{\mathrm{Brier}}
=
\mathrm{Brier}(P4)-\mathrm{Brier}(P3).
\]

Negative values favor P4.

These endpoints answer different questions. Improvement on one does not imply improvement on the other.

## 16. Secondary outcomes

Record at minimum:

- exact post-hoc return probability under true armed state and true closure model;
- planner-predicted return probability;
- path length;
- outbound goal success;
- return feasibility;
- true armed hazard identities;
- trigger identities executed;
- observation sequence;
- posterior support size;
- posterior entropy;
- posterior mass on the true armed set;
- planning latency;
- nodes expanded;
- oracle calls;
- regret versus P2.

Do not collapse these into one composite score.

## 17. Calibration analysis

Prediction target:

\`\`\`text
return_feasible_after_realized_future_closures
\`\`\`

Required outputs:

1. Brier score;
2. reliability diagram;
3. fixed-bin expected calibration error;
4. calibration-in-the-large;
5. calibration slope/intercept if stable;
6. uncertainty intervals.

Fixed probability bins:

\[
[0,.1),[.1,.2),\ldots,[.9,1].
\]

Do not change binning after viewing results.

Correct-specification calibration and misspecification robustness are separate analyses.

## 18. Model-misspecification study

True primary O2 sensor:

\[
s=c=0.85.
\]

Evaluate P4 with assumed parameters:

- M0 correct: \(\hat s=\hat c=0.85\)
- M1 overconfident: \(\hat s=\hat c=0.95\)
- M2 weak: \(\hat s=\hat c=0.70\)
- M3 miss-rate error: \(\hat s=0.70,\hat c=0.85\)
- M4 false-alarm error: \(\hat s=0.85,\hat c=0.70\)

Also include arming-model misspecification for a subset:

\[
\hat q\in\{q-0.2,q,q+0.2\}
\]

clipped to \([0,1]\), with the exact frozen grid specified in configuration before test execution.

A Bayesian method is expected to become miscalibrated under a wrong likelihood/model; negative results are required evidence.

## 19. Correlated-closure study

Use F3 and F5 topologies.

For a group with equal marginal closure probability \(p\), define

\[
\rho\in\{0,0.25,0.50,0.75,1.0\}.
\]

Generation:

1. draw \(M\sim\operatorname{Bernoulli}(\rho)\);
2. if \(M=1\), draw one common \(Z\sim\operatorname{Bernoulli}(p)\) and set all grouped closures to \(Z\);
3. if \(M=0\), draw each grouped closure independently from \(\operatorname{Bernoulli}(p)\).

This preserves each marginal \(p\) while increasing positive dependence.

Compare:

- true joint/scenario oracle;
- independent-marginal oracle;
- belief-conditioned planner using true joint model where tractable;
- belief-conditioned planner using misspecified independence.

Primary correlation quantity:

\[
\hat R_{\mathrm{independent}}-R_{\mathrm{joint}}.
\]

Also report route disagreement and realized return-infeasibility.

No claim about arbitrary correlation structures is allowed.

## 20. Statistical analysis

Experimental hierarchy:

\[
\text{scenario}\rightarrow\text{paired execution seed}.
\]

Do not treat all trial rows as independent environments.

### 20.1 Scenario-level estimate

For each scenario, compute paired method differences over execution seeds.

Primary estimate: equally weighted mean of scenario-level differences.

### 20.2 Hierarchical bootstrap

Use a frozen bootstrap seed.

For each bootstrap replicate:

1. resample scenarios with replacement;
2. within each selected scenario, resample paired execution indices with replacement;
3. preserve planner pairing.

Use 5,000 replicates for publication output.

Report 95% intervals.

### 20.3 Paired binary diagnostics

McNemar tests may be reported as secondary diagnostics where pairing is explicit.

Effect sizes and intervals remain primary.

### 20.4 Multiple primary endpoints

Risk difference and Brier difference are co-primary.

If null-hypothesis p-values are reported for both, use Holm correction across the two tests.

## 21. Interpretation rules

An operational-improvement statement requires:

- negative predeclared O2 P4–P3 risk difference;
- a 95% hierarchical-bootstrap interval excluding zero;
- path cost reported beside the risk effect.

A calibration-improvement statement requires:

- negative P4–P3 paired Brier difference;
- interval reported;
- reliability plots consistent with the numerical result.

Regardless of outcome, report:

- O0 perfect-sensing control;
- O6 uninformative-sensor control;
- F8 null topologies;
- misspecification results;
- hard-constraint comparison;
- path-cost changes.

No “universal winner” language is permitted.

## 22. Computational scaling

Vary:

- hazard count: \(\{1,2,4,6,8,10,12\}\);
- reachable belief support;
- graph/grid size;
- joint closure scenario count.

For each measured configuration:

- 10 warm-ups;
- 100 repetitions;
- median, IQR, p95;
- nodes expanded;
- return-oracle calls;
- memory where reliable.

Default per-call research budget:

- 60 seconds;
- 4 GiB process memory.

Record the first infeasible configuration rather than silently dropping it.

Approximation work begins only if this study establishes a real bottleneck.

## 23. Exact small-world policy validation

For at most three uncertain hazards and short finite horizons:

1. enumerate latent armed states;
2. enumerate observations;
3. solve the finite-horizon belief-policy problem exactly;
4. compare P4.

Report:

- first-action disagreement;
- policy/value gap;
- runtime.

If branching on future observations has negligible value in these worlds, retain that result.

## 24. Software information barriers

Tests must enforce:

- P0/P1/P1b cannot read true armed state;
- P3 receives detector outcomes only and applies the frozen positive-latching rule; it cannot read true arming state;
- P4 receives detector outcome + declared probabilistic model only;
- P2 is the only planner permitted to read truth;
- planned candidate paths do not mutate persistent truth or posterior;
- post-hoc evaluator may read truth but cannot affect planner decisions.

Any truth leakage invalidates the affected publication run.

## 25. Required unit/property tests

### Belief update

- normalization;
- perfect sensor collapse;
- uninformative sensor gives predictive prior;
- \(q=0\) and \(q=1\);
- repeated monotone arming;
- multiple hazards;
- impossible observation handling;
- immutable belief state.

### Posterior-predictive oracle

- mixture equals weighted known-state values;
- current-cell conditioning;
- equal armed-cell-map equivalence;
- known independent cases.

### CRN

- planner order invariance;
- route-divergence stream invariance;
- deterministic unused-event keys.

### Correlation

- empirical marginals equal \(p\) within Monte Carlo tolerance;
- \(\rho=0\) reproduces independence;
- \(\rho=1\) reproduces common outcome;
- dependence increases monotonically in the generator parameter.

## 26. Gazebo V4 gate

Gazebo is execution-level evidence and must implement the same information semantics.

The stack must distinguish:

- executed trigger;
- simulator latent arming truth;
- detector observation;
- planner posterior;
- future blocker realization.

Non-oracle planners must never subscribe to latent arming truth.

Minimum Gazebo conditions:

- O0 perfect;
- O2 medium;
- O4 miss-heavy.

Planner set:

- oracle;
- detector-as-truth;
- belief-conditioned;
- fixed-marginal/shortest reference.

Target at least 30 valid repetitions per planner/condition. This is a mechanism-validation target, not a formal power claim.

If >10% of trials in a condition are protocol-invalid, do not make comparative efficacy claims from that condition until the infrastructure issue is resolved and the full frozen condition is rerun.

## 27. Physical-robot boundary

V4 does not authorize physical-robot efficacy claims.

Hardware requires a separately frozen protocol and an actual/blinded latent arming mechanism. A future ROS 2 platform may use a door/gate, virtual closure controller, or other environment process, but simulation truth cannot be directly replayed to non-oracle planners.

## 28. Rerun rules

### Semantic/code bug

If a bug changes planner actions, belief update, stochastic semantics, metrics, or CRN pairing, invalidate and rerun all affected conditions from the frozen scenario manifest.

### Infrastructure-invalid trial

Never convert protocol-invalid trials into planner failures.

### Unexpected outcome

Retain it. Do not change the protocol because a preferred method loses.

## 29. Raw artifact schema

Every retained trial records at least:

\`\`\`text
protocol_version
scenario_id
topology_family
execution_seed
planner
observation_regime
lambda
tau
path
path_length
trigger_ids_executed
true_armed_set
detector_observations
belief_support_size
belief_entropy
predicted_return_probability
true_model_return_probability
realized_closure_set
return_feasible
mission_success
planning_time_ms
nodes_expanded
oracle_calls
protocol_valid
invalid_reason
\`\`\`

Truth fields are retained for post-hoc scoring even though non-oracle planners are blinded to them.

## 30. Provenance contract

Every publication-facing run must record:

- exact Git SHA;
- dirty/clean state;
- dependency/runtime versions;
- protocol version;
- scenario manifest digest;
- workflow run ID;
- artifact ID;
- artifact digest;
- planner configs;
- model parameters;
- seed policy;
- raw trials;
- scenario summaries;
- statistics;
- calibration output;
- timing output;
- generated tables/figures.

Publication values must be generated from retained artifacts, not manually transcribed.

## 31. Pre-outcome figure set

Generate programmatically:

1. return-risk difference versus observation noise;
2. path-length versus return-risk frontier;
3. reliability diagrams;
4. Brier score versus observation regime;
5. oracle / belief / detector / fixed-marginal comparison;
6. misspecification heatmap;
7. correlation error versus \(\rho\);
8. scaling versus hazard count/support size;
9. scenario-level paired primary result;
10. O0/O6/F8 negative controls.

Every figure must correspond to a stated research question.

## 32. Authorized claim scope

Potentially supportable if the frozen evidence warrants it:

- belief over latent action-induced topology state improves return-risk estimation under tested partial observation;
- belief-conditioned planning changes route choice and may improve the tested risk/cost frontier;
- sensor/model misspecification degrades calibration;
- independent marginals misestimate return connectivity under the tested correlated model;
- exact categorical belief tracking has measured scaling limits.

Not authorized by V4 alone:

- first POMDP safe-return planner;
- universal safety improvement;
- formal kinodynamic safety;
- real-world calibrated probabilities;
- arbitrary correlation handling;
- arbitrary-map generalization;
- physical-robot efficacy;
- certification;
- universal superiority over hard constraints.

## 33. Freeze checklist

Before viewing held-out V4 outcomes, commit:

- [ ] final \`RESEARCH_GAP_V2.md\`;
- [ ] this protocol;
- [ ] arming model;
- [ ] observation model;
- [ ] exact belief update;
- [ ] planner conditions P0–P5;
- [ ] P6 small-world reference if included;
- [ ] topology generator;
- [ ] development/validation/test manifests;
- [ ] primary configurations;
- [ ] raw artifact schema;
- [ ] statistics/calibration code;
- [ ] unit/property tests.

Then record the exact pre-outcome commit SHA.

Any semantic change after that point requires a protocol amendment and a new retained run.
