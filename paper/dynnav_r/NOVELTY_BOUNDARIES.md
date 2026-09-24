# Novelty boundary register

This file records the claims that the manuscript must **not** make and the narrower hypothesis that remains under test. It is intentionally adversarial: a nearby prior result should narrow the claim rather than be treated as a weak baseline.

## Claim boundary matrix

| Broad claim | Prior art that already covers it | Status for this paper |
|---|---|---|
| Safe-return planning is new | Guo et al., *IEEE TAC* 2023, DOI 10.1109/TAC.2023.3244884; Zhang & Guo, *Online Planning of Uncertain MDPs under Temporal Tasks and Safe-Return Constraints* | **Excluded** |
| History-dependent probabilistic robot risk is new | Xiao, Dufek, Murphy, *IEEE RA-L* 2020, DOI 10.1109/LRA.2020.2974434 | **Excluded** |
| Decision-dependent/endogenous uncertainty is new | Mature stochastic/robust optimization literature; decision-dependent network reliability formulations predate this work | **Excluded** |
| Actions changing future robot capability is new | Baldes et al., *A Model for Optimal Resilient Planning Subject to Fallible Actuators*, 2024 | **Excluded** |
| Predicting near-miss commitment / future bottleneck closure is new | RCSP and related predictive-commitment work | **Excluded** |
| Contingency or backup feasibility is new | Backup-plan MPC, contingency MPPI, safe-return and reachability methods | **Excluded** |
| Action-dependent environmental evolution is new | Existing robotics work models action-dependent environmental transition fields, including 2026 sequential cleanup/risk-field work | **Excluded** |
| Graph articulation / cut concepts are new | Classical graph theory and prior robotics/network applications | **Excluded** |

## Surviving research hypothesis

The manuscript tests the narrower statement:

> Robot path/action history can activate stochastic changes to the **environment's future return-connectivity**, so two histories ending at the same geometric state can have different safe-return reliability even when a state-only marginal closure model assigns them the same value.

This is a representational/information claim, not a universal planning-superiority claim.

## Markov-state qualification

The augmented state `(x, A)` is a standard Markovization for the stated finite model; it is not itself a novel planning principle. A conventional MDP can represent this process exactly when its state includes the active hazard state (and any other variables required by the event model). The state-only marginal planner in this repository is a deliberately restricted ablation that omits that variable, not a general MDP/POMDP baseline. Its null result isolates information loss under that restriction and does not demonstrate superiority over general history-aware planning.

The closest environmental-topology precedent located in this audit is Kameyama et al.'s AFADA, which demonstrates robot navigation in an environment whose topology changes stochastically. AFADA assigns routing and topology management to an active modular environment; the DynNav model instead makes future closure hazards conditional on the robot's own executed directed transitions and evaluates safe-return connectivity. This is a difference in modeled mechanism, not evidence that either work subsumes the other.

## What the current evidence supports

The retained CI artifacts support only the following mechanism-level statements:

1. Counterfactual histories ending at the same geometric cell can differ in exact safe-return reliability under the implemented action-triggered topology-hazard model.
2. A state-only marginal model aliases those histories by construction.
3. In the controlled repeated-module family, state-only marginal planning is paired-identical to shortest-path planning, while history-conditioned planning avoids trigger activations.
4. A hard safe-return threshold can match the history-aware planner in some controlled families and can be more conservative in at least one frozen heterogeneous scenario.
5. The critical-cut approximation is exact on the controlled series-critical family but optimistic on a joint-cut counterexample.

## What remains unsupported

The current evidence does **not** establish:

- first-of-kind novelty across all robotics/planning literature;
- geometric-domain generalization beyond the procedural families tested;
- calibrated real-world closure probabilities;
- kinodynamic safety guarantees;
- ROS2/Gazebo or hardware validation of the new history-conditioned planner;
- superiority over every safe-return, contingency, reachability, or endogenous-uncertainty method.

## Reviewer rule

If a new paper is found that explicitly models **robot-action-triggered stochastic environmental topology changes whose activation history changes safe-return connectivity at otherwise identical geometric states**, the novelty claim must be narrowed again or withdrawn. The experimental contribution may remain useful even if the modeling idea is not novel.
