# Reviewer Audit V4

**Status:** adversarial pre-submission audit for the belief-conditioned research track.

This document is written from the perspective of a skeptical robotics reviewer. It is not a rebuttal and does not assume that the proposed V4 paper deserves acceptance.

---

## Executive assessment

The V4 direction is scientifically stronger than simply extending history-aware A* because it asks a sharper information-state question: what should be retained when robot actions create a latent stochastic environmental state that controls future return connectivity?

However, the project is **not yet submission-ready**. The largest risks are conceptual rather than software-related:

1. the novelty boundary is narrow and sits between mature POMDP, safe-return, endogenous-uncertainty, and action-induced-topology literatures;
2. the proposed predictive-belief A* is not a full POMDP policy solver;
3. synthetic environments could manufacture the effect;
4. known model parameters may make the problem easier than realistic robotics;
5. exact categorical belief and exact connectivity enumeration scale exponentially;
6. the new latent-arming semantics need a credible robotics interpretation beyond an abstract Bernoulli variable;
7. current Gazebo evidence does not validate the new causal/observation model.

A good V4 paper is possible only if these limitations are tested rather than rhetorically minimized.

---

## R1. “This is just a standard POMDP with a custom state variable.”

### Why a reviewer may say this

Once hazard arming is hidden and observations are noisy, the correct information state is a belief. That is standard POMDP theory. Belief-state Markovization and Bayes filtering are not new.

### Current response

Agree with the premise. V4 should not claim novelty in the belief update or POMDP representation.

The research contribution, if supported, is narrower:

- identify a robotics mechanism in which executed actions create a latent environmental topology-exposure state;
- show that this state materially changes safe-return connectivity;
- quantify the information lost by geometric, fixed-marginal, and point-estimate representations;
- measure when belief tracking changes planning decisions and calibration.

### Acceptance gate

The paper must contain experiments where:

- position-only, fixed-marginal, detector-as-truth, and belief representations receive otherwise matched information/models;
- belief state changes route choice in held-out multi-step worlds;
- perfect sensing collapses the distinction as expected;
- history-irrelevant controls show no artificial advantage.

If these tests do not produce a clean representation result, do not frame V4 as a standalone paper.

---

## R2. “The closest POMDP / safe-return / dynamic-door work already covers this.”

### Risk

High.

The intersection is narrow. Safe return under uncertainty, noisy-edge POMDP navigation, uncertain obstacle safety, dynamic door-closing POMDPs, endogenous uncertainty, self-deleting topology, and action-dependent risk all exist.

### Required mitigation

Before submission:

1. perform backward citation chaining from the closest 6 works;
2. perform forward citation search through 2026;
3. record search strings/databases/dates;
4. read full methods sections, not only abstracts;
5. add a comparison table based on causal semantics, not terminology.

### Acceptance gate

The paper must be able to state a difference without relying on the phrase “action-triggered topology hazards.”

A defensible distinction would need to survive paraphrase:

> the robot's action changes a hidden environmental state that changes the distribution of future graph connectivity to a safe set.

If prior work already studies that same causal object with comparable objectives, novelty must move to a different contribution or V4 should become a robustness extension rather than the main paper.

---

## R3. “Your planner is not solving the POMDP.”

### Risk

High if presentation is careless.

The current V4 reference planner propagates predictive belief through candidate trigger executions but does not branch over future observations inside search. It replans after actual observations.

### Required wording

Call it:

- receding-horizon predictive-belief planner;
- belief-conditioned A* reference method.

Do not call it:

- optimal POMDP planner;
- belief-space optimal planner;
- POMDP solution algorithm.

### Required experiment

For tiny worlds, compute an exact finite-horizon observation-contingent reference policy and report:

- action disagreement;
- value gap;
- runtime.

### Acceptance gate

If the receding-horizon method differs substantially from the exact small-world policy in ordinary regimes, either:

- improve the planning method; or
- make the approximation itself an explicit limitation and stop claiming broad planning implications.

---

## R4. “The benchmark was engineered so history/belief must matter.”

### Risk

Very high based on the current DynNav history.

Many existing worlds deliberately contain return-critical trigger hazards.

### Required mitigation

The frozen V4 held-out suite must include:

- null/history-irrelevant worlds;
- noncritical hazards;
- redundant loops;
- unavoidable hazards;
- multiple safe sets;
- worlds where state-only is sufficient;
- worlds where longer conservative routes are undesirable;
- random/procedural topologies not manually edited after seeing planner behavior.

### Acceptance gate

Report results by topology family.

Do not pool all worlds into one headline statistic without showing where the effect disappears.

A credible result includes families where the belief method ties or loses on mission cost.

---

## R5. “The latent arming variable is artificial.”

### Risk

High.

A Bernoulli variable inserted between trigger execution and closure can look like a mathematical device created to obtain partial observability.

### Required mitigation

Ground the abstraction in at least two plausible mechanisms, for example:

- a traversed automatic gate may or may not latch into a later-close state, with an imperfect status sensor;
- an action may arm a delayed access-control or safety interlock without immediate visible geometry change;
- traversal may destabilize a passage with uncertain latent structural state and noisy sensing.

Avoid examples that require implausible independence assumptions.

### Execution-level gate

Gazebo/ROS experiments must implement the separation physically in the simulator/controller:

```text
executed trigger
  -> hidden arming draw/state
  -> noisy detector message to planner
  -> later closure draw/action
```

Non-oracle planners must not receive simulator truth.

A hardware experiment would greatly strengthen this point but is not mandatory if the paper remains mechanism-level.

---

## R6. “You know q, p, sensitivity and specificity exactly.”

### Risk

High for real-world interpretation.

Correctly specified Bayesian inference can look artificially favorable.

### Required mitigation

The mandatory misspecification study in V4 must remain in the main paper or main supplement:

- correct model;
- overconfident sensor;
- pessimistic sensor;
- false-negative misspecification;
- false-positive misspecification.

Also vary arming probability (q) and closure probability (p).

### Acceptance gate

The paper must explicitly show a regime where Bayesian belief becomes miscalibrated under wrong parameters.

If no failure boundary is reported, reviewers can reasonably suspect the study is protecting the preferred method.

---

## R7. “Calibration is being measured against samples from the same model.”

### Risk

Moderate to high.

Calibration under a correctly specified simulator is partly a unit test of probability propagation.

### Required distinction

Separate:

### Internal/model calibration

Does implementation match the declared stochastic model?

Useful for correctness but not a deployment claim.

### Robustness calibration

Does prediction remain useful under:

- sensor misspecification;
- correlation misspecification;
- topology-family shift?

This is scientifically more meaningful.

### Acceptance gate

Do not present correctly specified Brier score alone as a major empirical contribution.

---

## R8. “Exact inference is exponentially small-world only.”

### Risk

High.

A categorical armed-set belief can contain (2^m) states, and exact closure enumeration can also be exponential.

### Required mitigation

Report:

- belief support;
- oracle calls;
- median/IQR/p95 runtime;
- memory;
- first infeasible configuration.

Do not hide configurations that exceed budget.

### Acceptance gate

One of the following must be true:

1. the paper explicitly positions exact inference as a small-hazard reference and provides a useful approximation; or
2. the targeted application naturally has a small number of latent hazards and the paper justifies that scope.

Approximation claims require adversarial counterexamples.

---

## R9. “The soft objective is arbitrary and double-counts risk along a path.”

### Risk

Moderate.

Adding (1-R) at every transition is a design choice, not a theorem. It can favor routes based on repeated exposure to the same return-risk state.

### Required mitigation

Keep representation and objective separate.

Compare:

- soft belief cost;
- hard belief safe-return threshold;
- exact small-world policy where possible.

Report cases where the hard constraint matches or beats the soft method.

### Acceptance gate

The main conclusion must remain about information representation unless the objective comparison itself produces independent evidence.

---

## R10. “Detector-as-truth is a straw baseline.”

### Risk

Moderate.

It is useful as an overconfidence ablation but not sufficient as the strongest comparison.

### Required mitigation

Keep:

- detector-as-truth;
- prior-only;
- fixed-marginal exact;
- activation oracle;
- hard belief constraint.

Where tractable, include an exact small-world observation-contingent policy reference.

Search for a published baseline that can be implemented fairly under the same graph/observation model.

### Acceptance gate

Do not claim superiority over “POMDP methods” based on a detector-as-truth baseline.

---

## R11. “Your correlated-hazard experiment is a separate paper stapled on.”

### Risk

Moderate.

Correlation can distract from the main partial-observation contribution.

### Current recommendation

Treat correlation as a **model-misspecification boundary**, not a second headline contribution, unless it leads to a genuinely new planning/inference method.

The key result should be:

> equal closure marginals do not determine return connectivity.

Use the common-cause model to quantify how badly the independent oracle can be wrong.

### Acceptance gate

If correlation consumes substantial manuscript space without changing the main conclusion, move most of it to supplementary material.

---

## R12. “Common random numbers are mishandled when routes diverge.”

### Risk

Moderate but technically important.

Different planners execute different hazards, so naïvely consuming a sequential RNG stream can destroy pairing.

### Required mitigation

Use keyed random variables:

```text
(scenario, seed, hazard, event_type, occurrence)
```

Unused draws remain defined but unconsumed.

### Acceptance gate

Property tests must show that changing planner order or route length does not change the latent event assigned to the same hazard/event key.

---

## R13. “The 24,000 trials exaggerate the sample size.”

### Risk

High if inference is reported at trial level only.

Trials are nested within scenarios.

### Required mitigation

Primary inference unit must respect:

[
	ext{scenario} ightarrow 	ext{paired stochastic seed}.
]

Use scenario-level effects and hierarchical bootstrap.

Report both:

- number of scenarios;
- seeds per scenario.

### Acceptance gate

Do not write “n=24,000 independent environments.”

---

## R14. “The held-out suite is not actually held out.”

### Risk

High unless process is auditable.

### Required mitigation

Commit before outcomes:

- generator;
- explicit scenario manifests;
- planner code;
- parameters;
- statistical analysis;
- seed/key policy.

Record the pre-outcome commit SHA.

### Acceptance gate

Any semantic bug after outcome inspection invalidates the affected publication run and requires a fresh retained artifact. Do not silently patch and reuse numbers.

---

## R15. “There is no real robotics evidence.”

### Risk

Venue-dependent.

For a planning/mechanism paper, strong synthetic evidence plus ROS/Gazebo may be acceptable; for a systems-heavy robotics venue, hardware absence may be decisive.

### Required mitigation

At minimum, the new Gazebo experiment must exercise:

- true hidden arming;
- blinded noisy observation;
- belief update;
- replanning;
- delayed closure;
- independent post-hoc recovery assessment.

Target enough valid repetitions to characterize the mechanism, not eight runs.

### Hardware gate

If targeting a venue/reviewer population that strongly expects physical validation, add a small TurtleBot-class experiment or narrow the paper's claims accordingly.

---

## R16. “The old paper and the V4 paper are two stories mixed together.”

### Risk

Moderate.

Known-history aliasing is already a complete mechanism paper substrate. Partial observation adds another state layer.

### Recommendation

Use the progression

[
x ightarrow (x,A) ightarrow (x,b(A))
]

as one conceptual story, but do not overload the empirical paper.

The known-history result should become the deterministic/perfect-information limiting case for V4.

If page limits make this incoherent, publish the known-history paper separately and treat V4 as follow-on work.

---

## Current submission gates

V4 should **not** move from draft-research status to submission manuscript until all P0 gates below are satisfied.

### P0


**Gate interpretation:** checked items above are infrastructure/mechanism gates that
are already supported without viewing held-out outcomes. Unchecked empirical
gates must remain unchecked until the SHA-gated retained experiment is run.
The global repository CI also contains website dependency-audit jobs unrelated
to V4 research validity; the focused V4 workflow is the pre-outcome research
gate, while Python-version compatibility remains separately open until the
canonical Python matrix completes successfully.

- [ ] Python V4 contracts pass on all supported Python versions.
- [x] Held-out generator and explicit manifests are committed before outcomes.
- [x] Keyed CRN tests pass.
- [ ] Multi-step held-out planning shows a nontrivial belief-state effect.
- [ ] Perfect-sensor and history-irrelevant controls behave as null cases.
- [ ] Model-misspecification failure boundary is retained.
- [x] Scenario-level/hierarchical uncertainty analysis is implemented.
- [x] Exact-small-world policy comparison is completed, including a retained future-information counterexample that bounds the receding-horizon approximation.
- [x] Gazebo truth-leakage test exists.
- [x] Closest-prior-art citation chaining is documented.

### P1

- [x] Correlated equal-marginal development study completed and retained; publication positioning remains a misspecification boundary.
- [x] Exact-belief scaling boundary measured in retained development evidence; 8 hazards exceeded the 5 s development budget while the frozen held-out suite is capped at 6.
- [ ] Calibration plots generated automatically.
- [ ] Hard versus soft belief objective compared.
- [ ] Paper tables/figures generated from retained artifacts.

### P2

- [ ] Physical robot validation, if required by target venue.
- [ ] Approximate belief method for larger hazard sets, only if claims are extended beyond the current <=6-hazard exact-reference scope.

---

## Decision rule

The project should be willing to conclude that V4 is **not** a stronger standalone paper.

If belief conditioning:

- does not change decisions beyond toy worlds;
- provides no robust calibration/operational benefit in the frozen target regime;
- or is dominated by a stronger matched baseline,

then retain those results and keep the known-history paper as the main contribution.

The purpose of V4 is to test the idea, not to guarantee a second positive story.
