# Experiment Protocol V4

## Belief-Conditioned Safe-Return Planning under Partially Observed Action-Induced Topology State

**Protocol status:** frozen research design before publication-facing V4 outcomes.

**Freeze date:** 2026-10-03.

**Relationship to V3:** V4 extends, but does not replace, the evidence supporting the known-history paper. Existing V3 retained results remain historical evidence under their original semantics. V4 introduces a new latent hazard-arming state, noisy observations of that state, belief-conditioned planning, and a separate correlated-closure study.

No V4 result may be used in the manuscript unless it was generated after the relevant implementation/configuration was frozen under this protocol and retained with raw artifacts.

---

## 1. Scientific questions

### RQ1 — hidden action-induced state

When robot actions can arm latent topology hazards, does a posterior belief over the armed-hazard state preserve safe-return information that is lost by geometric or fixed-marginal representations?

### RQ2 — operational value

Under imperfect observations, does belief-conditioned planning improve return-connectivity outcomes or the risk/path-cost frontier relative to treating detector output as ground truth?

### RQ3 — calibration

Are belief-conditioned return probabilities calibrated under a correctly specified model, and how do calibration and decisions degrade under parameter misspecification?

### RQ4 — correlated closures

How much error arises when future closures are modeled as independent despite a correlated joint topology distribution with the same marginal closure probabilities?

### RQ5 — boundary and scaling

When is belief tracking unnecessary, harmful through conservatism, or computationally impractical?

---

## 2. Causal semantics

V4 separates four events that must never be conflated.

### 2.1 Trigger execution

The robot executes a directed trigger transition (e_i). In the abstract V4 planning study the geometric transition is known to have occurred.

### 2.2 Latent hazard arming

Executing (e_i) does not necessarily reveal whether the environmental mechanism was armed.

For hazard (i),

[
B_isimmathrm{Bernoulli}(q_i),
]

and the monotone armed state updates as

[
A_i^+ = A_ilor B_i.
]

The original known-activation DynNav semantics are recovered with (q_i=1).

### 2.3 Arming observation

The planner observes (Y_iin{0,1}) through a detector with sensitivity (s_i) and specificity (c_i):

[
P(Y_i=1mid A_i=1)=s_i,
]

[
P(Y_i=0mid A_i=0)=c_i.
]

The simulator ground-truth arming state must not be exposed to a non-oracle planner.

### 2.4 Future closure realization

An armed hazard may later realize a closure. Under the independent model,

[
C_imid A_i=1simmathrm{Bernoulli}(p_i),
]

and (C_i=0) when (A_i=0).

The primary synthetic study realizes closures only for the post-outbound safe-return evaluation, preserving comparability with V3. A later execution-level study may introduce within-mission realization only under a protocol revision.

---

## 3. Information state

The planner maintains

[
b_t(A)=P(A_t=Amid u_{0:t-1},y_{0:t}),
]

where (A) is a set/bit-vector of armed hazard identities.

Under the primary model assumptions:

- geometric state (x_t) is observed;
- hazard arming is Markov and monotone;
- model parameters are fixed within an episode;
- arming observations are conditionally independent given the relevant latent state;
- future closure law depends on history only through (A_t);
- no hidden event-time variable affects closure;

the pair

[
(x_t,b_t)
]

is the information state used by the belief-conditioned method.

This is standard belief-state Markovization and is not claimed as a new POMDP result.

---

## 4. Return-connectivity quantities

For known armed state (A),

[
R(x,A)=
Pleft[
xleadstomathcal S_{mathrm{safe}}
	ext{ after future closures}
mid A
ight].
]

For activation belief (b),

[
R(x,b)=
sum_A b(A)R(x,A).
]

The exact small-hazard oracle remains an evaluation/reference mechanism. It is not assumed scalable.

The current robot cell is conditioned traversable at the decision instant, consistent with V3.

---

## 5. Planner conditions

Every publication-facing planning study must include the following conditions where computationally feasible.

### P0 — shortest

Geometric shortest-path / unit-cost planner. It receives no hazard-information advantage.

### P1 — fixed-marginal exact

Uses the exact return-connectivity oracle but applies one fixed marginal hazard field independent of executed arming observations/history.

Purpose: representation ablation.

### P2 — activation oracle

Receives the true armed set after each executed transition.

Purpose: upper-information reference, not deployable baseline.

### P3 — detector-as-truth

Treats the binary arming detector output as exact armed/inactive state.

Purpose: tests the cost of point-estimate overconfidence.

### P4 — belief-conditioned

Maintains the exact discrete posterior over armed hazard sets and evaluates posterior-predictive safe-return reliability.

This is the primary proposed information representation.

### P5 — hard belief-safe-return

Uses the same belief and oracle as P4 but rejects successor states below a frozen safe-return threshold.

Purpose: separate representation value from soft-objective choice.

### Optional P6 — exact small-world belief-policy reference

For tiny worlds with at most three uncertain hazards and short finite horizon, implement exact dynamic programming / exact belief-policy evaluation that branches on observations.

Purpose: quantify the approximation introduced by the main receding-horizon predictive-belief planner. It is not required for the full 96-scenario suite if computationally prohibitive.

No weak baseline may be substituted for a stronger one because the stronger one performs well.

---

## 6. Primary planning algorithm semantics

The main V4 planner is **not** to be described as an optimal POMDP solver unless such a solver is actually implemented.

The default publication method is a receding-horizon predictive-belief planner:

1. At decision time, start from posterior (b_t).
2. During candidate-path search, a future trigger transition propagates the belief through the arming transition model but marginalizes the as-yet-unseen observation.
3. Path transition cost uses posterior/predictive safe-return reliability under the propagated belief.
4. Execute only the next transition.
5. Sample/receive the arming observation.
6. Apply the exact Bayes update.
7. Replan.

This design uses partial-observation information without claiming full observation-contingent policy optimality.

Any implementation that instead branches on future observations must be labeled separately.

---

## 7. Objective settings

### Primary soft objective

To isolate representation from tuning, the primary soft-planner experiment inherits

[
lambda=8
]

from the V3 publication-facing setting.

Transition cost is

[
c = 1+lambda(1-R_{mathrm{return}}).
]

If implementation details require a modified cost, this protocol must be versioned before test outcomes are inspected.

### Primary hard threshold

[
	au=0.90.
]

### Predeclared sensitivity grid

Soft:

[
lambdain{1,2,4,8,16}.
]

Hard:

[
	auin{0.70,0.80,0.90,0.95}.
]

Hyperparameter sensitivity is secondary analysis. No test-set result may be used to select the headline value.

---

## 8. Observation regimes

The primary observation regimes are defined by true detector sensitivity/specificity.

| Regime | Sensitivity (s) | Specificity (c) | Role |
|---|---:|---:|---|
| O0 perfect | 1.00 | 1.00 | null/control; belief and detector-as-truth should converge |
| O1 mild symmetric | 0.95 | 0.95 | low observation noise |
| O2 medium symmetric | 0.85 | 0.85 | **primary imperfect-observation condition** |
| O3 severe symmetric | 0.70 | 0.70 | high observation noise |
| O4 miss-heavy | 0.70 | 0.95 | false-negative stress |
| O5 false-alarm-heavy | 0.95 | 0.70 | false-positive stress |

The primary operational comparison is P4 vs P3 under O2.

Observation draws are paired across planner conditions when the same hazard is armed/exposed under that planner's executed route.

---

## 9. Arming and closure parameter ranges

The procedural scenario generator must draw/freeze values from:

[
q_iin{0.4,0.7,1.0}
]

for conditional arming probability after trigger execution, and

[
p_iin{0.25,0.50,0.80}
]

for closure probability conditional on arming.

The generator must include mixtures within multi-hazard scenarios rather than assigning one common value everywhere.

The held-out scenario manifest stores the exact (q_i,p_i) values; they must not be regenerated after outcomes are inspected.

---

## 10. Environment families

The publication test suite contains 96 frozen scenarios: 12 scenarios from each of eight families.

### F1 — bridge/detour

Shorter trigger-exposed route versus longer route preserving a critical return bridge.

### F2 — asymmetric fork

Two outbound branches with different trigger identities and return consequences.

### F3 — loop/redundant return

At least two return routes so no single local risk score trivially captures network reliability.

### F4 — chamber multi-trigger

Multiple trigger opportunities before the same geometric region/goal.

### F5 — parallel joint cut

Individually noncritical closures can jointly destroy return connectivity.

### F6 — unavoidable-hazard choice

Every mission-feasible outbound route arms at least one hazard; methods must select *which* exposure rather than avoid all exposure.

### F7 — multiple safe regions

More than one safe-return target; closures change which safe region remains reachable.

### F8 — null/history-irrelevant controls

Triggers either do not affect return connectivity or the relevant closure probability is zero. History-aware methods should not gain artificial benefit.

Each scenario must have a machine-checkable topology contract and known feasible outbound path before stochastic evaluation.

---

## 11. Dataset split and freeze procedure

### Development split

48 scenarios.

Used for implementation debugging, visualization, and gross parameter sanity checks.

Development outcomes may be inspected.

### Validation split

48 scenarios.

Used only for predeclared engineering decisions such as resolving numerical instability or selecting among already-declared approximation variants.

### Held-out test split

96 scenarios as defined above.

Test outcomes must not be inspected until:

- generator code is frozen;
- planner code is frozen;
- configuration schema is frozen;
- scenario manifest is generated and committed;
- unit/property tests pass;
- the analysis script is frozen.

### Seed policy

Base generator seeds:

- development: `2026100301`;
- validation: `2026100302`;
- held-out test: `2026100303`.

The generator must emit explicit scenario JSON/YAML files. The committed manifest, not the seed alone, becomes authoritative.

If generator semantics change after manifest generation, V4 must be revised and a new manifest created before new outcomes are inspected.

---

## 12. Stochastic execution sample size

For the held-out test:

- 96 scenarios;
- 250 paired stochastic seeds per scenario per observation regime;
- fixed sample size;
- no outcome-based early stopping;
- no outcome-based sample-size increase.

Primary O2 analysis therefore has:

[
96	imes250=24{,}000
]

paired executions per planner.

Secondary O0/O1/O3/O4/O5 conditions use the same 250 seeds unless computation becomes infeasible **before test execution begins**. Any reduction must be recorded as a protocol amendment before outcomes.

---

## 13. Common-random-number indexing

All stochastic variables are generated deterministically from keyed indices rather than planner execution order.

Keys include:

```text
(scenario_id, execution_seed, hazard_id, event_type, occurrence_index)
```

Event types include at least:

- `arming`;
- `observation`;
- `closure`;
- `correlation_mixture`;
- `correlation_common_draw`;
- `correlation_independent_draw`.

A planner that never executes a trigger simply does not consume that hazard's realization. Random-number streams must not shift because another planner took a different path.

---

## 14. Primary endpoints

### Primary operational endpoint

Post-closure return-infeasible indicator at the outbound evaluation point.

Primary effect:

[
Delta_{mathrm{risk}}
=
mathrm{risk}(P4)-mathrm{risk}(P3)
]

under O2, with negative values favoring belief conditioning.

### Primary probabilistic endpoint

Brier score of the planner's predicted final safe-return probability against realized binary return feasibility.

Primary effect:

[
Delta_{mathrm{Brier}}
=
mathrm{Brier}(P4)-mathrm{Brier}(P3).
]

Negative values favor belief conditioning.

The two endpoints answer different questions and must both be reported.

A positive result on one does not license claiming a positive result on the other.

---

## 15. Secondary outcomes

Report at minimum:

- exact post-hoc return probability under ground-truth armed state and true closure model;
- final predicted return probability available to each planner;
- path length;
- mission success / goal reached;
- safe-return feasibility;
- activated/armed hazard count;
- activated/armed hazard identities;
- trigger count;
- planning latency;
- p95 planning latency;
- nodes expanded;
- oracle calls;
- belief support size;
- belief entropy;
- posterior probability assigned to the true armed state;
- arming-state classification error for point-estimate methods;
- calibration-in-the-large;
- expected calibration error with fixed bins;
- regret relative to P2 activation oracle.

Do not collapse these into one composite score.

---

## 16. Calibration analysis

Prediction target:

```text
return_feasible_after_realized_future_closures
```

Predicted quantity:

[
hat R = R(x,b)
]

or the corresponding prediction under the comparison method.

Required calibration outputs:

1. Brier score;
2. reliability diagram;
3. fixed-bin expected calibration error;
4. mean prediction minus empirical frequency;
5. calibration slope/intercept if numerically stable;
6. bootstrap uncertainty intervals.

Use fixed probability bins:

[
[0,.1),[.1,.2),ldots,[.9,1].
]

Do not choose bins after viewing results.

Calibration under correct specification and robustness under misspecification are separate analyses.

---

## 17. Model-misspecification study

This is secondary but mandatory.

True O2 sensor:

[
s=c=0.85.
]

Evaluate belief planners that assume:

### M0 correct

[
hat s=hat c=0.85.
]

### M1 overconfident

[
hat s=hat c=0.95.
]

### M2 pessimistic

[
hat s=hat c=0.70.
]

### M3 miss-rate error

[
hat s=0.70,quad hat c=0.85.
]

### M4 false-alarm error

[
hat s=0.85,quad hat c=0.70.
]

The purpose is not to show robustness at all costs. A correctly implemented Bayesian planner is expected to become miscalibrated when its likelihood model is wrong.

---

## 18. Correlated-closure study

The correlation study is separate from activation-observation uncertainty.

Use topologies from F3 and F5 where redundant paths make joint failures consequential.

### 18.1 Equal-marginal correlation model

For a group of closure hazards with common marginal (p), define correlation parameter

[
hoin{0,0.25,0.50,0.75,1.0}.
]

Generate closures by:

1. draw (Msimmathrm{Bernoulli}(ho));
2. if (M=1), draw one common (Zsimmathrm{Bernoulli}(p)) and set every group closure equal to (Z);
3. if (M=0), draw each closure independently as (mathrm{Bernoulli}(p)).

This preserves marginal closure probability (p) and induces positive dependence that increases with (ho).

### 18.2 Compared models

- true joint/scenario oracle;
- independent-marginal oracle using the same marginals;
- belief-conditioned planner with true joint model where tractable;
- belief-conditioned planner with misspecified independent model.

### 18.3 Primary correlation outcome

Absolute and signed error in predicted return probability:

[
hat R_{mathrm{independent}}-R_{mathrm{joint}}.
]

Also report route disagreement and realized return-infeasibility.

No claim about arbitrary correlation structures is allowed.

---

## 19. Statistical analysis

The experimental hierarchy is:

[
	ext{scenario}
ightarrow
	ext{paired execution seed}.
]

Do not analyze all trial rows as independent environments.

### 19.1 Scenario-level primary summaries

For each scenario compute the paired method difference over its 250 execution seeds.

Primary reported estimate is the equally weighted mean of scenario-level differences.

### 19.2 Hierarchical bootstrap

Use a fixed bootstrap seed recorded in the artifact.

For each resample:

1. resample scenarios with replacement;
2. within each selected scenario, resample paired execution indices with replacement;
3. preserve planner pairing.

Use at least 5,000 bootstrap replicates for publication output.

Report 95% intervals.

### 19.3 Paired binary diagnostics

Exact McNemar tests may be reported within scenarios or pooled only when the pairing interpretation is explicit.

They are secondary to effect sizes and confidence intervals.

### 19.4 Multiple outcomes

The operational risk difference and Brier difference are co-primary.

If formal null-hypothesis p-values are used for both, apply Holm correction across the two primary tests.

Secondary metrics are descriptive/exploratory unless explicitly predeclared otherwise.

---

## 20. Interpretation rules

### Evidence supporting H2/H3

A result may be described as an operational improvement only if:

- the paired risk difference is negative in the predeclared primary O2 comparison;
- its 95% hierarchical-bootstrap interval excludes zero;
- path cost and mission feasibility are reported beside it.

A calibration improvement requires lower Brier score with an interval for the paired difference.

### No universal-winner language

Even if P4 wins the primary comparison, the paper must explicitly report:

- O0 perfect-sensing equivalence/null behavior;
- F8 history-irrelevant controls;
- misspecification failures;
- hard-constraint comparisons;
- regimes in which path cost increases materially.

---

## 21. Computational scaling study

Vary independently where possible:

- hazard count: (min{1,2,4,6,8,10,12});
- reachable belief-support size;
- grid/graph size;
- number of joint closure scenarios.

For each configuration:

- 10 warm-ups;
- 100 measured repetitions;
- same machine/runner class for compared methods;
- record median, IQR, p95;
- peak memory where measurement is reliable;
- nodes expanded;
- return-oracle calls.

Timing values are environment-specific descriptive measurements.

### Scaling failure criterion

If exact belief support exceeds a predeclared memory/time budget, record the first infeasible configuration rather than silently skipping it.

Default CI budget:

- 60 seconds per individual planner call;
- 4 GiB process memory.

If these limits are changed, record the reason before rerunning the publication suite.

---

## 22. Approximation work

Do not introduce approximation only to create an extra contribution.

Approximation work begins only if the scaling study establishes a meaningful exact-inference bottleneck.

Candidate methods may include:

- sparse posterior support;
- factorized activation belief;
- scenario sampling;
- particle belief;
- cutset-aware joint reliability approximations.

Every approximation must include:

- a regime where it is accurate;
- an adversarial failure case;
- error versus exact reference;
- route-disagreement analysis;
- computational benefit.

---

## 23. Small-world exact belief-policy validation

For worlds with at most three uncertain hazards:

1. enumerate latent armed states;
2. enumerate binary observations;
3. solve a finite-horizon belief-policy problem exactly or by exhaustive dynamic programming;
4. compare the receding-horizon predictive-belief route/policy.

Report:

- value gap;
- action disagreement;
- runtime.

This is a validation of the approximation level, not the primary scalability result.

If exact policy branching offers no meaningful benefit in these worlds, retain that negative result.

---

## 24. Gazebo / ROS 2 protocol extension

Gazebo remains a separate execution-level gate.

### 24.1 Required V4 mechanism

The execution stack must distinguish:

- true executed trigger transition;
- latent arming state generated by the experiment controller;
- detector message delivered to the planner;
- planner belief;
- later blocker/closure realization.

The planner may not subscribe to the simulator's true arming state except in the explicitly named oracle condition.

### 24.2 Noise conditions

At minimum test:

- perfect observation;
- medium observation noise matching O2;
- miss-heavy observation matching O4.

### 24.3 Planner set

- DynNav oracle activation;
- DynNav detector-as-truth;
- DynNav belief-conditioned;
- DynNav fixed-marginal or shortest reference as appropriate.

### 24.4 Repetitions

Target at least 30 valid repetitions per planner/condition for mechanism comparison.

This target is not a power claim. If protocol-invalid rates are high, fix infrastructure and rerun the entire frozen condition rather than selectively replacing failed outcomes.

### 24.5 Validity

Retain V3 validity rules for lifecycle, reset, trigger observation, blocker injection, costmap observation, and recovery assessment.

Add:

- arming draw logged;
- detector draw logged;
- planner input contains only the detector outcome;
- no ground-truth arming leakage.

If more than 10% of trials in a condition are protocol-invalid, do not make comparative efficacy claims from that condition.

---

## 25. Physical-robot boundary

V4 does not require hardware for the abstract contribution.

No physical-robot efficacy claim is authorized unless a separately frozen hardware protocol exists.

A future hardware study should use an actual latent/environmental arming mechanism or a rigorously blinded virtual closure controller rather than merely replaying simulator truth to the planner.

---

## 26. Stopping and rerun rules

### No outcome-based stopping

The fixed sample size is completed regardless of interim performance.

### Code/semantic bug

If a bug changes:

- planner action selection;
- belief update;
- stochastic semantics;
- metric definition;
- pairing;

invalidate the affected publication run and rerun all affected conditions from the frozen scenario manifest.

### Infrastructure failure

Infrastructure-invalid trials are never reclassified as planner failures.

For deterministic simulation, any nonzero protocol-invalid count should trigger investigation before publication.

### Outcome surprise

An unexpected negative result is retained. It is not a reason to change the protocol.

---

## 27. Artifact contract

Every retained V4 run must record:

- exact Git commit SHA;
- dirty state;
- Python/compiler/package versions;
- workflow run ID;
- artifact ID;
- artifact digest;
- protocol version;
- scenario manifest digest;
- planner configs;
- model parameters;
- observation parameters;
- correlation parameters where applicable;
- random seed/key policy;
- raw per-trial data;
- per-scenario summaries;
- statistical output;
- calibration output;
- timing output;
- generated figures/tables.

Publication-facing values must be generated from artifacts, not manually transcribed.

---

## 28. Required raw trial fields

At minimum:

```text
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
```

Correlated study adds joint-model/group/correlation identifiers.

Do not omit truth fields from retained artifacts merely because planners are blinded to them; truth is required for post-hoc scoring.

---

## 29. Required software tests before held-out execution

### Belief update

- posterior normalization;
- perfect-sensor collapse to truth;
- uninformative-sensor posterior equals predictive prior;
- zero/one arming probabilities;
- repeated trigger execution under monotone arming;
- multiple hazards;
- impossible observation handling;
- no mutation/aliasing of belief maps.

### Return oracle

- belief mixture equals weighted known-state oracle values;
- current-cell conditioning;
- equal active-cell map equivalence;
- independent known-answer cases.

### Planner information barriers

- non-oracle planners fail tests if ground-truth armed set is injected;
- detector-as-truth uses detector only;
- belief planner uses likelihood parameters and observation only;
- planned paths do not mutate persistent posterior history.

### CRN

- planner execution order does not change stochastic realizations;
- route divergence does not shift event draws;
- unused hazard draws remain deterministic.

### Correlation

- empirical marginals match (p);
- empirical pairwise dependence increases with (ho);
- (ho=0) matches independent model;
- (ho=1) matches common-outcome model.

---

## 30. Pre-publication figures

The analysis pipeline should generate, without manual number entry:

1. risk difference by observation noise;
2. path-length versus return-risk frontier;
3. calibration/reliability diagrams;
4. Brier score by observation regime;
5. oracle–belief–detector–fixed-marginal comparison;
6. model-misspecification heatmap;
7. correlation error versus (ho);
8. scaling plot versus hazard count/belief support;
9. scenario-level paired scatter/ranked difference for the primary O2 comparison;
10. negative-control figure for O0/F8.

Every figure must answer a stated research question.

---

## 31. Claim authorization

A retained V4 result may support only claims matching the tested scope.

Potentially supportable:

- belief over latent action-induced topology state can improve return-risk estimation under the tested partial-observation model;
- belief-conditioned planning can change route selection and improve the tested risk/cost frontier under specified observation regimes;
- model misspecification can degrade calibration;
- independent marginals can misestimate return connectivity under the tested correlated-closure model;
- exact belief inference has measured scaling limits.

Not authorized without further evidence:

- first POMDP safe-return planner;
- universal safety improvement;
- formal kinodynamic safety;
- real-world probability calibration;
- arbitrary correlation handling;
- arbitrary-map generalization;
- physical-robot efficacy;
- certification;
- universal superiority over hard constraints.

---

## 32. Freeze checklist

Before the first held-out V4 test outcome is viewed, commit:

- [ ] final `RESEARCH_GAP_V2.md`;
- [ ] this protocol;
- [ ] hazard-arming model;
- [ ] observation model;
- [ ] belief update;
- [ ] planner implementations;
- [ ] exact small-world reference if included;
- [ ] topology generator;
- [ ] development/validation/test manifests;
- [ ] all primary configs;
- [ ] raw artifact schema;
- [ ] analysis/statistics script;
- [ ] calibration script;
- [ ] unit/property tests.

Then tag or otherwise record the exact pre-outcome commit.

Any semantic change after that point requires a protocol amendment and a fresh retained publication run.
