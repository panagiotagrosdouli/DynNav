# Publication Readiness

Assessment date: 2026-10-04. Status terms are `READY`, `PARTIAL`, and `NOT READY`.

| Category | Status | Evidence and boundary |
|---|---|---|
| 1. Core scientific claim | READY | The constructive proposition, exact oracle, information-gap benchmark, and retained controls support the narrow claim that an activated-hazard sufficient statistic can distinguish equal geometric states under action-triggered topology hazards. |
| 2. Novelty | PARTIAL | The manuscript now states explicitly that `(position, active hazards)` is standard MDP Markovization and that the state-only marginal planner is a restricted ablation. AFADA is added as a close stochastic-topology precedent. The manuscript makes no first-of-kind claim; broader venue-specific literature screening remains required. |
| 3. Mathematical validity | READY | The finite independent-Bernoulli model, exact enumeration, bounds, analytic phase boundary, and joint-cut counterexample have executable regression tests. This judgment does not extend to correlated or delayed-revelation hazards. |
| 4. Implementation validity | READY | The canonical Python suite and ROS-independent benchmark contracts pass. The C++ implementation has dedicated unit/plugin tests in ROS CI; local ROS compilation was unavailable in this audit environment. |
| 5. Baseline fairness | READY | Shortest, state-only marginal, exact-history, critical-cut, and hard-threshold baselines are retained. The negative result that hard constraints can match the soft objective is publication-facing. |
| 6. Experimental validity | PARTIAL | Controlled, held-out-horizon, and three frozen geometric studies are retained with common random numbers. Strict action-triggered Gazebo mechanism probes are also retained and protocol-valid, but they show integration/execution evidence rather than a stable comparative efficacy effect. The comparative evidence remains synthetic and narrow. |
| 7. Statistical validity | READY | Binary comparisons are paired by seed/event identity and report risk differences, paired bootstrap intervals, discordant counts, and exact McNemar tests. Timing values remain descriptive and environment-specific. |
| 8. Generalization evidence | PARTIAL | Evidence covers heterogeneous probabilities, unseen module counts, and three hand-authored topologies. It does not establish arbitrary-map, correlated-hazard, delayed-observation, or real-world generalization. |
| 9. Computational scalability | PARTIAL | Exact enumeration and augmented-state scaling are measured, and approximation failure is retained. No broad real-time guarantee is supported. |
| 10. ROS validation | PARTIAL | ROS 2/Nav2 integration and executed-transition history semantics are implemented and tested. Retained strict Gazebo probes contain 24/24 valid trials with successful navigation for all three planner conditions in the frozen mechanism study, but no stable comparative DynNav efficacy effect is supported. Physical-robot efficacy remains unsupported. |
| 11. Reproducibility | READY | Deterministic seeds, CLI entry points, frozen protocols, raw/processed artifacts, CI, and an evidence manifest are present. Publication release still requires a clean tagged CI run. |
| 12. Literature coverage | PARTIAL | Relevant categories and direct novelty constraints are discussed, but each bibliographic record and claim placement still needs final human/venue verification. |
| 13. Manuscript quality | PARTIAL | The manuscript is scoped conservatively and retains negative results. Final copy-editing, number-to-manifest verification, and venue formatting remain. |
| 14. Remaining limitations | READY | Independence, synthetic topology, calibration, partial observability, dynamics, localization, simulation, hardware, and certification boundaries are explicit. |
| 15. Remaining required work | NOT READY | A submission freeze needs a clean tagged full-main audit (including CI and paper build) at the release commit and a final bibliography/number-to-manifest audit. Any stronger Gazebo efficacy or hardware claim requires a new predeclared study; it may not be inferred from the retained integration probes. |

## Decision

**No-go for submission from the current moving `main` branch.** The narrow representation result is defensible, and action-triggered Gazebo execution/integration has retained protocol-valid evidence, but the repository should be released only from a tagged commit after the full-main validation set, paper build, final bibliography audit, and number-to-manifest verification. Gazebo comparative efficacy must remain unsupported unless a broader predeclared study establishes it.
