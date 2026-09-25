# Literature Gap Audit for G1-G5

**Audit date:** 2026-09-25  
**Status:** selective current-web screen, not a systematic review.

This file is a novelty constraint, not evidence that DynNav is the first work at any broad intersection. A venue submission still requires database-specific searches, backward/forward citation chaining, duplicate removal, title/abstract screening and full-text review of the closest papers.

## G1 — dependence-ambiguous action-triggered topology

### Established prior art

- Distributionally robust motion planning and control in robotics already use ambiguity sets for uncertain obstacles, perception and prediction. Examples include OFDR-RRT (IFAC 2020), distributionally robust risk maps (IEEE T-RO, 2022), and sensor-based distributionally robust navigation/control (IJRR, 2026).
- Decision-dependent/endogenous uncertainty is an established optimization topic. Doan's EJOR 2022 work develops distributionally robust optimization with decision-dependent discrete distributions and Frechet classes.
- Decision-dependent uncertainty has already been studied in shortest-path/network optimization outside robotics, including robust shortest-path examples and endogenous-uncertainty network/interdiction problems.
- Robot actions modifying future traversability are now explicit robotics prior art: Frenkel, Parker and Mansouri, *Coverage with Self-Induced Obstacles on Grids*, IEEE RA-L 2026, models visited vertices becoming future obstacles and uses a sufficient graph representation.

### Surviving candidate gap

The defensible candidate is **not** "distributionally robust robotics", "endogenous uncertainty", "correlated failures", or "actions change the map." The narrower unresolved intersection from this selective screen is:

> Safe-return planning in which the robot's executed transition history activates a subset of future topology hazards, while only partial information about the *joint dependence* of those activated future closures is available.

The research object is therefore the composition

`executed transition -> activated hazard set -> dependence ambiguity -> return connectivity -> route choice`.

No first-of-kind wording is authorized until a systematic search confirms the intersection.

### Closest sources found

- Doan, *Distributionally robust optimization under endogenous uncertainty with an application in retrofitting planning*, EJOR 2022.
- Nohadani & Sharma, *Optimization under Decision-Dependent Uncertainty*, SIAM J. Optimization 2018.
- Safaoui et al., distributionally robust motion-planning work, ICRA 2024.
- Long et al., *Sensor-based distributionally robust control for safe robot navigation in dynamic environments*, IJRR 2026.
- Frenkel, Parker & Mansouri, *Coverage with Self-Induced Obstacles on Grids*, IEEE RA-L 2026.

## G2 — noisy activation belief

### Established prior art

Belief-state/POMDP navigation under noisy sensing is mature. Safe exploration work also explicitly reasons about probabilistic reachability and returnability while learning environmental hazards.

### Consequence

G2 should not be a standalone novelty claim in its current form. Its strongest role is as a **robustness boundary of DynNav**: physical trigger execution, noisy trigger observation and later closure realization are different random variables, and treating the detector as ground truth can be false-safe.

A paper-level G2 claim would need a genuinely new planning formulation or a strong empirical finding that is specific to action-triggered return topology, not merely a Bayesian update.

### Close source

- *Planning under uncertainty for safe robot exploration using Gaussian process prediction*, Autonomous Robots 2024: information-seeking exploration with probabilistic reachability/returnability.

## G3 — policy-dependent learning of trigger consequences

### Established prior art

Safe exploration and active learning already trade information gain against safety, and modern safe RL methods explicitly explore uncertain dynamics while remaining inside pessimistic safe sets.

### Surviving candidate gap

The potentially distinctive statistical issue is narrower:

> The policy controls *exposure* to the endogenous trigger, so the same safe-return policy that avoids hazards also changes which trigger-conditioned closure outcomes enter the calibration data.

This creates a missingness/selection mechanism tied to robot decisions. The current analytic control shows why coding non-exposure as a negative closure observation is biased. Novelty would require stronger treatment than a standard safe active-learning objective: for example, explicit exposure-aware estimators, identifiability conditions, or finite-sample calibration/safety guarantees.

### Close sources

- *Planning under uncertainty for safe robot exploration using Gaussian process prediction*, Autonomous Robots 2024.
- ActSafe, active exploration with safety constraints for model-based reinforcement learning.

## G4 — causal trigger-to-closure discovery

### Established prior art

Generic causal discovery and causal decision-making in robotics are active and recent:

- CAnDOIT (Advanced Intelligent Systems, 2024) combines observational and interventional time-series data for causal discovery and validates on a robotic manipulation benchmark.
- Castri, Beraldo & Bellotto, *Causality-enhanced decision-making for autonomous mobile robots in dynamic environments*, Expert Systems with Applications 2026, integrates causal discovery/reasoning with ROS and Gazebo-style mobile-robot decision making.

### Consequence

G4 has **low standalone novelty** as currently implemented. IPW with logged randomized propensities is a sound experimental primitive, not a new causal-discovery method.

Its best role is either:
1. a measurement tool for validating that a candidate DynNav trigger truly has an interventional effect on a later topology event, or
2. a future separate paper only if a topology-specific causal-identification problem and stronger method emerge.

The hidden-confounding failure case must remain publication-facing.

## G5 — exact history compression

### Established prior art

Exact state aggregation, MDP model minimization and bisimulation quotienting are classical. Modern work also uses bisimulation quotienting for combinatorial optimization. Therefore "state compression" or "quotienting" is not a novelty claim.

The 2026 self-induced-obstacle work is also especially relevant because it constructs a sufficient representation for action-modified grid planning.

### Surviving contribution

For DynNav, G5 is best positioned as a **problem-specific exact sufficient-statistic reduction**:

> Under the repository's existing semantics, multiple triggers that activate the same future closure cell with the same probability induce the same future closure event. Trigger identity can therefore be quotiented away without changing the return distribution or planner objective.

The value is computational and explanatory. It becomes a stronger contribution only if the scaling experiments show a substantial practical reduction and the equivalence is stated/proved as a theorem specialized to the DynNav hazard model.

### Close sources

- Givan, Dean & Greig, *Equivalence notions and model minimization in Markov decision processes*, Artificial Intelligence 2003.
- Drakulic et al., *Bisimulation Quotienting for Efficient Neural Combinatorial Optimization*, 2023.
- Frenkel, Parker & Mansouri, IEEE RA-L 2026.

## Updated programme priority

| Priority | Track | Research role after literature stress-test |
|---|---|---|
| 1 | **G1** | strongest paper-extension candidate, but novelty must be the action-triggered **return-connectivity + dependence-ambiguity** intersection |
| 2 | **G3** | promising second paper if exposure-aware learning yields theory or a clear safety/calibration frontier |
| 3 | **G5** | strong exact computational companion to G1; weak as generic state-compression novelty |
| 4 | G2 | important robustness extension, but generic belief/POMDP novelty is not defensible |
| 5 | G4 | useful validation/inference tool; generic causal-discovery novelty is not defensible with the current estimator |

## Claim rule

Until a systematic literature review is completed, use formulations such as "we study" and "we evaluate" rather than "first", "novel class", "unexplored", or "no prior work." The current evidence can establish properties of the DynNav model and its experiments; it cannot establish absence of prior art.
