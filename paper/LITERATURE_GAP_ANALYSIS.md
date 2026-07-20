# DynNav-R Literature Gap Analysis

**Status:** Initial structured scan — not yet a complete systematic review  
**Paper track:** DynNav-R: Recoverability-Aware Risk-Sensitive Navigation with Runtime Safety Supervision

## 1. Review objective

The review asks whether prior work already combines all of the following in one mobile-robot navigation method:

1. route-level risk optimization;
2. an explicit recoverability or safe-return signal used during route selection;
3. measurement of progressive loss of recovery options, rather than collision risk alone;
4. runtime supervisory adaptation based jointly on risk and recoverability; and
5. comparative evaluation using irreversible-state entry and recovery outcomes.

The purpose is not to claim that recoverability, risk-aware planning, safe return, reachability, or runtime supervision are individually new. Each has substantial prior literature. The candidate contribution must lie in a narrower, defensible combination and evaluation protocol.

## 2. Search protocol

Initial search families:

- `recoverability-aware robot navigation`
- `recoverability motion planning robot`
- `safe-return constrained motion planning`
- `returnability autonomous exploration`
- `irreversible outcomes robot planning`
- `risk-aware navigation CVaR`
- `reachability-based risk-aware motion planning`
- `runtime safety supervisor robot navigation`
- `recovery policy safe navigation`

Primary-source venues prioritized in this first pass: Robotics: Science and Systems proceedings, IEEE publications, and author-hosted/arXiv manuscripts.

A complete review should record database, date, exact query, screening criteria, exclusions, and forward/backward citation searches.

## 3. Closest and representative prior work

| Work | Main contribution | Risk during planning | Safe return / recovery | Runtime supervision or recovery policy | Relation to DynNav-R |
|---|---|---:|---:|---:|---|
| Fan et al., **STEP: Stochastic Traversability Evaluation and Planning for Risk-Aware Off-road Navigation**, RSS 2021 | Uncertainty-aware traversability, CVaR tail risk, and risk-aware kinodynamic MPC for extreme terrain | Yes | Not a first-class route recoverability objective | Receding-horizon planning, but not the proposed recoverability supervisor | Strong baseline for risk and CVaR; shows that risk-aware navigation itself is established |
| Adu et al., **RADIUS: Risk-Aware, Real-Time, Reachability-Based Motion Planning**, RSS 2023 | Reachable-set construction and bounded collision-risk optimization in real time | Yes | Reachability supports certified tracking/collision analysis, not retained escape/return freedom | Online optimization | Important terminology warning: “reachability” is not automatically equivalent to DynNav-R recoverability |
| Guo et al., **Hierarchical Motion Planning under Probabilistic Temporal Tasks and Safe-Return Constraints**, 2023 | Joint outbound and return policies with probabilistic safe-return constraints for MDP/LTL tasks | Yes, through constrained probabilistic planning | **Yes — very close prior work** | Two synthesized policies rather than the proposed three-state runtime supervisor | Prevents a broad novelty claim about safe-return-aware planning; DynNav-R must distinguish continuous route fragility, local/mobile navigation setting, and runtime adaptation |
| Curtis et al., **TAMPURA: Partially Observable Task and Motion Planning with Uncertainty and Risk Awareness**, RSS 2024 | Long-horizon TAMP under uncertainty, including avoidance of undesirable and irreversible outcomes | Yes | Reasons about irreversible outcomes at task level | Closed-loop controllers within hierarchical planning | Prevents claiming that planning around irreversible outcomes is new in general; DynNav-R must target route-level recoverability metrics and navigation experiments |
| He et al., **Agile But Safe**, RSS 2024 | Agile locomotion plus a learned recovery policy, switched using a reach-avoid value network | Implicit safety/reach-avoid value | Yes, through a recovery policy | **Yes** | Very close conceptually to planning/execution plus recovery; differs in learned legged control and reach-avoid switching rather than interpretable grid-route recoverability |
| Axelrod et al., **Provably Safe Robot Navigation with Obstacle Uncertainty**, RSS 2017 | Safety evaluation and safe RRT under uncertain obstacle observations | Probabilistic safety | Long-term execution safety, not an escape-option score | No equivalent DynNav-R supervisor | Establishes that uncertainty-aware safety guarantees are mature; DynNav-R should avoid “provably safe” claims |
| Jasour and Williams, **Risk Contours Map for Risk Bounded Motion Planning under Perception Uncertainties**, RSS 2019 | Chance-constrained risk maps and bounded-risk paths | Yes | No explicit return/recovery freedom | No | Representative risk-bounded planning baseline |
| Holmes et al., **ARMTD: Reachable Sets for Safe, Real-Time Manipulator Trajectory Design**, RSS 2020 | Receding-horizon safe planning with fail-safe braking maneuvers | Safety constraints | Fail-safe maneuver embedded in every trajectory | Replanning with fail-safe behavior | Shows prior integration of planning and fallback maneuvers, although for manipulators and certified reachable sets |
| Farid et al., **Failure Prediction with Statistical Guarantees for Vision-Based Robot Control**, RSS 2022 | Failure prediction with bounds on false positive/negative rates | Predictive failure signal | Predicts need for intervention rather than optimizing route recoverability | Can trigger safety intervention | Relevant to supervisor evaluation: false activations and missed activations should be measured |
| Janson et al., **Safe Motion Planning in Unknown Environments**, RSS 2018 | Safe planning policies when obstacles are revealed online | Safety-focused | Implicit preservation of safe execution, not explicit returnability score | Adaptive online policy | Relevant benchmark family for partially revealed maps |
| Fisac et al., **Probabilistically Safe Robot Planning with Confidence-Based Human Predictions**, RSS 2018 | Confidence-aware predictions and probabilistic safety certificates | Yes | No route-level recoverability objective | Runtime confidence adaptation | Relevant for uncertainty-conditioned risk and supervisor sensitivity |
| Dharmadhikari et al., **Motion-Primitives-based Path Planning for Fast and Agile Exploration**, 2020 | Exploration planning with global layer and timely return-to-home | Primarily feasibility/exploration | Yes, return-to-home | Replanning architecture | Another warning that return capability is established in exploration systems |

## 4. What the literature already establishes

The initial scan rejects several over-broad novelty claims:

- Risk-aware and CVaR-based navigation are established.
- Reachability-based safe motion planning is established.
- Safe-return constraints are established.
- Planning that avoids irreversible outcomes exists in hierarchical task-and-motion planning.
- Runtime switching to recovery policies exists.
- Planning architectures with fail-safe maneuvers or return-to-home behavior exist.

Therefore, DynNav-R should **not** claim to introduce risk-aware planning, recoverability, safe return, irreversibility awareness, or safety supervision in isolation.

## 5. Candidate defensible gap

A narrower gap remains plausible but is not yet proven:

> Existing methods typically treat collision risk, formal reachability, safe-return feasibility, learned recovery control, and runtime supervision as separate formulations. The reviewed work does not yet reveal a lightweight mobile-navigation framework that uses an interpretable **continuous recoverability signal**—derived from retained escape options, bottleneck exposure, return distance, and route-level worst-case recovery freedom—as a first-class route-selection term, and then uses the same signal jointly with route risk to drive an auditable hysteretic runtime supervisor.

The potential novelty is therefore the **operationalization and integration** of three components:

1. **Continuous route recoverability:** not only whether return is possible, but how fragile that possibility is along the path.
2. **Joint planning objective:** geometric cost + uncertainty/risk + loss of recoverability.
3. **Closed-loop supervisory coupling:** thresholds and mode transitions based on both risk and deteriorating recoverability, evaluated through recovery outcomes.

## 6. Stronger formulation than the original objective

A simple weighted sum

\[
J(\pi)=L(\pi)+\lambda_rR(\pi)+\lambda_iI(\pi)
\]

is useful as a baseline, but by itself may be judged as incremental. A stronger research formulation should distinguish average exposure from critical route fragility:

\[
J(\pi)=L(\pi)+\lambda_r\operatorname{CVaR}_{\alpha}(r(\pi))
+\lambda_i\Phi(\pi),
\]

where

\[
\Phi(\pi)=
\beta_1\left(1-\min_{x\in\pi}R_{\mathrm{rec}}(x)\right)
+\beta_2\sum_t\max\left(0,-\Delta R_{\mathrm{rec},t}\right)
+\beta_3 B(\pi).
\]

Here:

- `min recoverability` captures the weakest point of the route;
- negative recoverability slope captures progressive commitment;
- `B(pi)` captures bottleneck duration or exposure;
- CVaR captures tail collision/traversability risk.

This formulation is more distinguishable from standard additive costmaps because it models the **trajectory of retained recovery freedom**, not merely local obstacle cost.

## 7. Primary hypothesis

> Compared with geometric and conventional risk-aware planners, recoverability-aware planning will reduce entry into fragile or effectively irreversible route segments and improve successful recovery after route invalidation, while incurring a measurable path-length and computation-time cost.

Secondary hypothesis:

> A supervisor that responds to both absolute recoverability and its rate of decline will produce fewer unrecoverable failures than a risk-only threshold supervisor, without excessive mode chattering.

## 8. Required baselines

At minimum:

1. shortest-path A*;
2. risk-aware A* using expected risk;
3. CVaR risk-aware A*;
4. safe-return feasibility constraint, without continuous recoverability ranking;
5. recoverability-aware planner without runtime supervisor;
6. risk-only runtime supervisor;
7. full DynNav-R.

A safe-return constrained baseline is essential because Guo et al. already demonstrate explicit safe-return planning. Comparing only against A* and risk-aware A* would not support the proposed novelty.

## 9. Required scenarios

The benchmark must contain cases where collision risk and recoverability disagree:

- short low-risk corridor that becomes blocked behind the robot;
- long route with multiple escape branches;
- cul-de-sac with initially low obstacle risk;
- narrow bottleneck followed by a high-value goal region;
- dynamically invalidated return edge;
- localization uncertainty increasing after commitment;
- energy or communication constraints that shrink the safe-return set;
- matched-risk paths with different escape-option counts.

Without such counterexamples, the recoverability term may collapse into an ordinary clearance or risk penalty.

## 10. Metrics that distinguish the contribution

- irreversible/fragile-state entry rate;
- probability of retaining a feasible safe-return policy;
- recovery success after controlled route invalidation;
- minimum route recoverability;
- duration below a recoverability threshold;
- cumulative negative recoverability slope;
- expected and CVaR route risk;
- mission success;
- path length and execution time;
- replans, safe-mode activations, emergency stops;
- supervisor false activations, missed activations, and chattering;
- planning runtime and expanded nodes.

## 11. Evidence boundary

Until stronger theory and simulation/hardware validation exist, the paper should state:

- recoverability is an interpretable planning proxy, not a viability certificate;
- returnability is geometric unless robot dynamics are explicitly modeled;
- safe mode is a software supervisory policy, not a certified emergency controller;
- grid-world evidence does not imply physical-robot safety;
- the literature gap is provisional until systematic screening and citation chaining are completed.

## 12. Immediate literature tasks

- [ ] Read the complete Guo et al. safe-return paper and reproduce its formal definition.
- [ ] Read TAMPURA’s treatment of undesirable and irreversible outcomes.
- [ ] Read Agile But Safe’s reach-avoid switching and recovery-policy evaluation.
- [ ] Search citations using `viability`, `backward reachable set`, `return policy`, `contingency planning`, `dead-end avoidance`, and `option-preserving planning`.
- [ ] Add mobile-robot exploration papers that guarantee return-to-home under energy or communication constraints.
- [ ] Build a PRISMA-style inclusion/exclusion log before using the phrase “systematic review.”
- [ ] Identify publicly available implementations suitable as baselines.

## 13. Provisional novelty statement

Use only as a working statement:

> We study interpretable recoverability as a continuous, route-level planning quantity that measures retained future recovery freedom rather than collision risk alone. We integrate this quantity with tail-risk-aware route selection and an auditable runtime supervisor, and evaluate whether the combined system reduces fragile commitments and improves recovery after controlled route invalidations.

Avoid claiming “the first” until the full review is complete.

## 14. Initial primary sources

- Fan, D. D., et al. “STEP: Stochastic Traversability Evaluation and Planning for Risk-Aware Off-road Navigation.” RSS, 2021. DOI: 10.15607/RSS.2021.XVII.021.
- Adu, C. E., et al. “RADIUS: Risk-Aware, Real-Time, Reachability-Based Motion Planning.” RSS, 2023. DOI: 10.15607/RSS.2023.XIX.083.
- Guo, M., et al. “Hierarchical Motion Planning under Probabilistic Temporal Tasks and Safe-Return Constraints.” arXiv:2302.05242, 2023.
- Curtis, A., et al. “Partially Observable Task and Motion Planning with Uncertainty and Risk Awareness.” RSS, 2024. DOI: 10.15607/RSS.2024.XX.118.
- He, T., et al. “Agile But Safe: Learning Collision-Free High-Speed Legged Locomotion.” RSS, 2024. DOI: 10.15607/RSS.2024.XX.059.
- Axelrod, B., et al. “Provably Safe Robot Navigation with Obstacle Uncertainty.” RSS, 2017. DOI: 10.15607/RSS.2017.XIII.023.
- Jasour, A. M., and Williams, B. “Risk Contours Map for Risk Bounded Motion Planning under Perception Uncertainties.” RSS, 2019. DOI: 10.15607/RSS.2019.XV.056.
- Holmes, P., et al. “Reachable Sets for Safe, Real-Time Manipulator Trajectory Design.” RSS, 2020. DOI: 10.15607/RSS.2020.XVI.100.
- Farid, A., et al. “Failure Prediction with Statistical Guarantees for Vision-Based Robot Control.” RSS, 2022. DOI: 10.15607/RSS.2022.XVIII.042.
- Janson, L., et al. “Safe Motion Planning in Unknown Environments: Optimality Benchmarks and Tractable Policies.” RSS, 2018. DOI: 10.15607/RSS.2018.XIV.061.
- Fisac, J. F., et al. “Probabilistically Safe Robot Planning with Confidence-Based Human Predictions.” RSS, 2018. DOI: 10.15607/RSS.2018.XIV.069.
