# DynNav Research Audit

**Audit revision:** `a6e032c132c2feed5968915c6f367cf2e8f69461`  
**Audit date:** 2026-08-18  
**Research question:** Can explicit recoverability estimation reduce irreversible navigation failures during online replanning without excessive path-length and computation overhead?

## Executive verdict

DynNav is an unusually broad robotics prototype, but it is not yet a defensible experimental basis for the central paper claim. The strongest current evidence is: deterministic algorithm tests (Level 1), a CI-described Nav2 plugin build and pluginlib load test (Level 2), one retained static planner-server Gazebo run (Level 3 integration context, but not closed-loop navigation evidence), and one retained dynamic closed-loop commissioning run with eight valid trials (Level 4 protocol commissioning). The dynamic run contains no operational irreversible failures, only one repetition, four rather than six requested planners, and no rosbag. It therefore cannot estimate the treatment effect in H1–H4.

The repository correctly calls the C++ quantity `localIrreversibility` a heuristic, not a probability. Scientifically, however, the name overstates what it measures: it depends only on the number of traversable four-connected neighboring cells and a piecewise penalty derived from that same count. It does not estimate future retreat feasibility, viability, failure probability, obstacle motion, robot dynamics, or uncertainty.

## A. Scientific contribution

### Exact contribution that is presently implemented

The smallest defensible contribution is an experimental framework for comparing costmap A* objectives with a local escape-option regularizer during Nav2 replanning. The implemented C++ objective is

\[
J(\pi)=\sum_{s\in\pi}\left[1+\lambda_R\,c_{\mathrm{map}}(s)+\lambda_I\,h_{\mathrm{local}}(s)\right],
\]

where `c_map` is normalized Nav2 costmap cost and `h_local` is a deterministic structural heuristic in `[0,1]`. This is not yet an explicit estimator of recoverability in the usual reachability/viability sense.

### Definition audit

The README definition, “runs without a feasible safe exit,” lacks the required time, knowledge, dynamics, safe-set, and resource-budget qualifiers. For V2, define at evaluation time \(t_e\):

* robot-information state \(b_{t_e}\): map/costmap and state estimate available to the robot;
* evaluation state \(x_{t_e}^{GT}\): simulator ground truth, used only for scoring;
* safe region \(S\), fixed before evaluation;
* recovery policy class \(\Pi_{rec}\), dynamics/controller, collision model, and horizon/budget \((T_{rec},D_{rec})\);
* `recovery_feasible = 1` iff a collision-free execution under an allowed recovery policy reaches `S` before the budget under the frozen post-event world;
* `irreversible_failure = 1` iff the mission fails after a valid route-invalidation event and `recovery_feasible = 0` at the first post-event assessment.

This is an operational simulation label, not formal irreversibility. A stricter paper may call it **post-invalidation recovery infeasibility**.

### Novelty boundary

| Component | Assessment |
|---|---|
| Weighted A* over Nav2 costmap | Engineering integration; not novel |
| Costmap risk penalty | Standard cost-aware planning/engineering |
| Local degree/escape penalty | Simple, interpretable heuristic; potential experimental treatment, weak standalone novelty |
| J0–J3 ablation in one plugin | Useful experimental design/integration, not algorithmic novelty |
| Dynamic Gazebo event and validity check | Research infrastructure contribution |
| Claim that explicit recoverability reduces irreversible failures | Novel empirical claim, currently untested at adequate power |
| Formal safety, viability, or calibrated failure probability | Not implemented |

### Claims currently supportable

* Level 1: the deterministic grid search implements zero/risk/local-heuristic/joint weights and has unit tests.
* Level 2: repository CI defines a Jazzy build, pluginlib discovery test, and package installation check. The retained source and workflow support an integration claim, though this audit could not re-execute it locally.
* Retained static artifact: 36/36 `ComputePathToPose` requests succeeded for six configurations on two queries. This supports path/latency observations only.
* Retained dynamic commissioning artifact: a TurtleBot3 simulation received eight controlled blocker events; all eight post-event costmaps met the observation validity rule; 7/8 navigations succeeded; 0/8 met the repository's operational irreversibility criterion.

### Claims not currently supportable

* H1–H4, including any failure-reduction or bounded-overhead claim.
* Superiority over NavFn, Smac2D, risk-only, or shortest-only.
* Generalization across uncertainty or dynamic-event rates.
* A causal claim that retained escape options produced success.
* Calibrated recoverability probability, formal safety, or viability.
* Real-robot readiness beyond a checklist; no hardware bag/log exists.

## B. Experimental validity

| Hypothesis | Independent variables | Dependent variables | Required baselines/ablations | Main confounders | Minimum design | Decision rule |
|---|---|---|---|---|---|---|
| H1 recoverability reduces irreversible failures | Planner J0–J3; scenario family | Primary: irreversible failure; secondary mission/recovery success | J0, J1, J2, J3; NavFn/Smac external references | route geometry, event timing, controller stochasticity, planner order, costmap latency | paired seeds; initially 50 per planner×family×condition, increase from blinded pilot power analysis | preregistered J2/J3 vs J0/J1 odds/risk difference CI excludes 0 after multiplicity control |
| H2 benefit grows with uncertainty/invalidation | planner × uncertainty level × event probability/timing | irreversible failure and interaction effect | all J0–J3 | invalid trials, sensor visibility, event severity coupled to uncertainty | at least 3 prespecified levels; paired event schedules; mixed-effects logistic model | planner×uncertainty interaction CI excludes 0 in predicted direction |
| H3 bounded overhead | planner | executed path length, planning latency, CPU time | J0 reference; NavFn/Smac descriptive | hardware load, warm-up, failed-run censoring | same machine; randomized/counterbalanced blocks; report success-stratified and all-trial estimands | upper 95% CI below preregistered margins (suggested: +15% length, +25 ms replan latency) |
| H4 joint is contextually superior | planner × scenario mechanism | irreversible failure, cumulative risk, overhead | J1 and J2 are essential | scenarios constructed to reward joint objective | include risk-dominant, recovery-dominant, conflict, and neutral families | J3 Pareto/non-inferiority criteria defined per family; no universal superiority claim |

Binary outcomes require Wilson or exact binomial CIs per cell. Primary paired contrasts use exact McNemar tests and paired risk differences with bootstrap CIs; a mixed-effects logistic regression with seed/scenario random intercepts estimates interactions. Continuous paired outcomes use bootstrap median/mean differences and standardized paired effect sizes; Wilcoxon tests are secondary. Correct the finite primary contrast family using Holm. Seeds are not independent if several planners share one generated world; model the pairing rather than treating rows as independent.

Failure criteria: collision; unrecoverable immobilization; timeout; planner/controller terminal failure; or recovery infeasibility after a valid event. Invalid trials (event not injected, not observed, localization invalid, lifecycle failure) are protocol failures and excluded from efficacy denominators but reported separately. Success is goal reached within the preregistered duration without collision or emergency stop. Recovery success is safe-region arrival within its separate recovery budget.

### Fairness defects in current experiments

* The synthetic fragile-commitment generator always places the closure on the route labeled fragile. Route labels, event exposure, and the desired decision are therefore entangled.
* Candidate routes are explicitly supplied and policies choose between them; this is not equivalent to online planning in a common state/action space.
* The synthetic recoverability-aware weight `20.0` is hard-coded and lacks a training/validation/test split.
* The randomized topology defaults deliberately bias route risk (`fragile=0.020`, `resilient=0.004`), so risk and recoverability are not orthogonally manipulated.
* The retained dynamic experiment compares only NavFn, Smac2D, DynNavRisk, and DynNavJoint. J0 and J2 are missing.
* Event time is deterministic and may occur at different robot states because planner paths/execution speeds differ. Trigger by a common spatial commitment surface or analyze achieved commitment at injection.
* The post-event recovery test is an eight-connected inflated-costmap graph test, whereas the planner uses four-connected search; its relationship to executable controller recovery is not established.

## C. Evidence hierarchy

| Result or capability | Tier | Classification |
|---|---|---|
| Grid search, metric, conversion, and benchmark-contract tests | LEVEL 1 | Unit-test evidence |
| Fragile-commitment and contribution CSVs | LEVEL 1 | Synthetic evidence |
| C++ plugin source plus CI plugin-load test | LEVEL 2 | ROS/Nav2 integration evidence |
| `static_run_31488640827` | LEVEL 2 within Gazebo runtime | Planner-server request evidence; not robot execution |
| `dynamic_run_31488640894` | LEVEL 4 commissioning | Dynamic Gazebo evidence, `n=1`; not comparative efficacy |
| Hardware validation | LEVEL 5 | Unsupported claim; no evidence |

The dynamic artifact lacks rosbags and raw ROS logs. Its JSON, costmap snapshots, environment package list, behavior trees, map/parameter snapshots, and hashes are useful retained evidence, but they do not independently prove every lifecycle/log assertion.

## D. Reproducibility

The retained ROS artifact contains a workflow URL, a non-null `source_revision`, revisions in `RUN.md`, environment packages, Gazebo version, kernel, map, parameters, scenario, blocker SDF, behavior trees, partial/final tables, costmap snapshots, and checksums. Defects: the exact launch command is described by workflow rather than copied into a per-run command file; no stdout/stderr or ROS logs are retained; no rosbag exists; and seeds are schedule/order seeds rather than physical stochastic-world seeds.

The older `REPRODUCIBILITY_REPORT.md` and `STATUS.yaml` refer to a different repository name/branch and stale validation state, so they cannot serve as the current paper record. Many tracked results across the 26 contribution folders lack a uniform manifest linking command, revision, environment, seed, raw data, and analysis version.

An independent researcher cannot presently reproduce every reported quantitative statement from a single locked environment. Required fixes are: immutable run manifest with non-null Git SHA; dependency lock/container digest; raw event/perception/navigation topics; analysis command and version; figure-to-input manifest; explicit tuning/evaluation split; and CI that checks every cited artifact hash and regeneration command.

## ROS 2 / Nav2 / Gazebo audit

The canonical planner package has credible plugin XML registration, `pluginlib_export_plugin_description_file`, lifecycle methods, mutex-protected costmap snapshotting, standard Nav2 exceptions, cancellation forwarding, parameter validation, and `nav_msgs/msg/Path` output. The plugin-load unit test verifies discovery, not planner-server lifecycle activation. Retained planner-server outputs provide indirect execution evidence; lifecycle logs are not stored.

The dynamic benchmark uses `BasicNavigator.goToPose`, per-planner behavior trees, Gazebo `SpawnEntity`/`SetEntityPose`, pre/post global-costmap counts, and recovery assessment. This is real integration infrastructure rather than a toy offline map mutation. Nonetheless, no direct replan counter or timestamped planner-path stream is retained, and recovery feasibility is evaluated from a costmap snapshot instead of an executed retreat trial.

This audit environment has no `/opt/ros/jazzy/setup.bash`; therefore no local `rosdep`, `colcon`, Nav2 lifecycle, or Gazebo execution was performed. Existing artifacts were inspected, not regenerated.

## Reviewer-rejection risks

1. **The treatment is not recoverability estimation.** It is local grid degree with a renamed bottleneck penalty. Minimum remedy: define a task-level recovery-feasibility target, implement a horizon/budget-conditioned estimator using only robot-available information, validate discrimination/calibration against held-out simulator rollouts, and retain the local heuristic as an ablation.
2. **The central effect has no powered evidence.** The only dynamic run is `n=1`, has zero primary events, and omits J0/J2. Minimum remedy: run the frozen six-planner, multi-family, paired multi-seed protocol with an event rate that creates both failures and successes in a blinded pilot, then freeze it and report all trials with CIs/effect sizes.
3. **The benchmark is treatment-favoring and incompletely reproducible.** Closure is assigned to the fragile route, weights are hard-coded, and ROS logs/bags/Git SHA are incomplete. Minimum remedy: orthogonalize risk, recoverability, route length, and event location; separate tuning from testing; record complete manifests, bags/logs, and reproducible analysis for every paper figure.

## Remediation implemented after the audit

The audit was completed before these changes. The workspace now contains a
separate bias-controlled V2 synthetic benchmark with independent event RNG and
J0–J3, operational outcome metrics with missing/invalid-state handling, direct
ROS `/plan` capture and replan counts, pre-event route-intersection validation,
run-manifest and rosbag configuration, corrected plugin identifiers, and a
physical-TurtleBot3 readiness launch/checklist. The full Python regression suite
passes (`514 passed, 32 skipped`). None of these implementation changes is
promoted to ROS/Gazebo evidence until executed on ROS 2 Jazzy.
