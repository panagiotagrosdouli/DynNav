# Post-Full-Study Findings and Research Decisions

**Date:** 2026-09-25  
**Frozen V1 artifact:** workflow run `36101578097`, artifact `10850230790`, digest `sha256:c3eafc891e8c78a8abcb666f1c751ca14ee945f7a6adb649db3f8509d10a7cd3`  
**Confirmatory protocol:** `EXPERIMENT_PROTOCOL_G1_G5_V1.md`

This document records decisions made **after** inspecting the frozen V1 full-study artifact. Any experiment introduced here is exploratory unless a later protocol version explicitly promotes it to a confirmatory test.

## Overall decision

The five tracks do not support one equally strong paper claim.

| Track | V1 result | Decision |
|---|---|---|
| **G1 dependence ambiguity** | strong, clean safety-efficiency separation with retained negative regime | **primary extension candidate** |
| G2 uncertain activation | strong robustness/calibration boundary, weak novelty as standalone method | supporting study |
| **G3 policy-dependent calibration** | exposes a real learning/safety feedback lockout; current probe rule is not a satisfactory solution | **continue research, do not claim solved** |
| G4 interventional trigger effects | clean randomized recovery; known hidden-confounding failure | measurement/validation tool |
| **G5 exact history compression** | exactness holds; early-goal A* search reduction is modest | computational companion; continue scaling diagnostics |

## G1 — result survives the frozen study

The independence-history planner takes the four-step trigger-activating shortcut. Across 10,000 retained trials per dependence condition (five repetitions x 2,000):

- independent closures: failure rate **0.2473**;
- common-cause closures: failure rate **0.5074**;
- anti-correlated closures: failure rate **0.0000**.

The marginal-dependence-robust planner takes the eight-step trigger-free detour and has **0 observed return failures** in each of the three retained dependence conditions.

This is not a universal superiority result. Anti-correlation is the mandatory harm regime: the shortcut has zero failures while the robust planner still pays the doubled path length.

### G1 claim that is currently supported

Within the frozen synthetic construction, equal marginal closure probabilities do not determine return risk; dependence shift changes the failure rate of an independence-assuming action-triggered route, and a marginal-dependence-robust planner avoids that exposure at a path-cost penalty.

### G1 next gates

1. broader held-out graph/topology families;
2. ambiguity sets learned from finite data rather than declared exactly;
3. ROS/Gazebo execution in which common-cause topology changes are injected after observed trigger execution;
4. systematic literature review before any first-of-kind wording.

## G2 — useful robustness result, not standalone novelty

Across the frozen (q,p) grid, the Bayesian activation posterior has lower Brier score than the prior-only estimate in all 9 strong-calibrated conditions and all 9 weak-calibrated conditions.

Mean Brier scores across the nine (q,p) combinations:

| Sensor profile | Bayesian | Prior only | Detector as truth | Activation oracle |
|---|---:|---:|---:|---:|
| strong calibrated | 0.1088 | 0.1534 | 0.1106 | 0.0953 |
| weak calibrated | 0.1493 | 0.1537 | 0.2032 | 0.0942 |
| sensitivity miscalibrated | 0.1549 | 0.1530 | 0.1712 | 0.0940 |

The negative result is scientifically important: under sensitivity misspecification the Bayesian model no longer beats the prior on average. At threshold 0.20, the (q=0.8,p=0.8) misspecified case calls about 49.7% of decisions safe, and about **51.2% of those accepted decisions fail**.

G2 therefore remains a robustness boundary around observation/model calibration, not a generic belief-state novelty claim.

## G3 — the full study exposes a feedback-lockout problem

The V1 posterior-mean gate behaves well only when the current model permits enough exposure. In more conservative or higher-risk regimes it stops collecting data, so posterior error remains substantial.

Selected five-repetition means:

| True closure p | Minimum return | Safe-probe exposures / 2000 | Mean absolute error |
|---:|---:|---:|---:|
| 0.1 | 0.5 | 2000.0 | 0.0063 |
| 0.3 | 0.7 | 128.6 | 0.0668 |
| 0.5 | 0.7 | 1.8 | 0.1533 |
| 0.7 | 0.5 | 7.0 | 0.1476 |

The separate logging negative control also remains important: with true (p=0.7), correctly excluding non-exposures produced a posterior mean about 0.674 in the initial retained mechanism run, whereas incorrectly coding unexposed opportunities as open outcomes produced about 0.338.

### G3 research interpretation

The current data support the existence of a policy/data feedback problem, not the claim that the current safe-probe heuristic solves it.

### New exploratory diagnostic

After inspecting V1, the branch adds a one-sided posterior lower bound on return probability and compares:

- posterior-mean exposure gate;
- credible-lower-bound exposure gate;
- oracle gate.

This diagnostic is intentionally expected to reveal a **safe-learning deadlock**: if the uncertainty-aware lower bound is already below the minimum allowed return probability, a strictly conservative policy cannot obtain the trigger-conditioned samples required to tighten that bound without additional information or tolerated exploration risk.

A later G3 paper needs either:
1. an identifiability/impossibility result plus conditions that break the deadlock, or
2. a stronger method using side information, contextual transfer, an explicit exploration-risk budget, or another defensible source of information.

## G4 — keep as an interventional validation primitive

The frozen randomized sparse graph benchmark achieved precision = recall = 1.0 at all retained per-pair sample sizes ({250,500,1000,2000}).

This does **not** authorize a generic causal-discovery claim. The hidden-confounding negative control has true ATE 0 but produces a spurious effect around 0.426 when the estimator is supplied the wrong constant propensity.

Current role: validate whether deliberately randomized candidate trigger transitions have a measurable effect on later topology events.

## G5 — exact but current planner-level speedup is modest

The event quotient preserves final safe-return probability and path length in every frozen module count.

At 8 modules:

- raw hazard identities: 16;
- quotient closure events: 8;
- raw nodes expanded: 50;
- quotient nodes expanded: 43;
- realized node reduction: **14%**;
- raw/compressed planning-time ratio in the retained run: about **1.16x**.

The theoretical subset-history difference is much larger than the observed early-goal A* difference. Therefore the V1 evidence supports exactness and a modest practical reduction, not a dramatic speedup claim.

### New exploratory diagnostic

The branch now enumerates the **complete reachable augmented state graph** for the duplicated-trigger diamond family, independently of A* stopping at the first goal. This directly tests whether the quotient removes substantial reachable history redundancy even when the primary route search does not need to visit it.

This new diagnostic is post-V1 and must remain separate from the frozen primary result.

## Publication direction after V1

The strongest coherent paper extension is:

> **History-conditioned safe-return planning under action-triggered topology hazards with uncertain closure dependence.**

G5 can accompany G1 as an exact representation/computation result if the full reachable-state diagnostic shows substantial redundancy reduction.

G2 belongs naturally as a robustness section or follow-up.

G3 is scientifically promising but currently contains an unresolved exploration-identification tradeoff; that unresolved result should drive the next method rather than be hidden.

G4 is currently infrastructure for causal validation, not the headline method.

## Evidence discipline

- The raw V1 full-study artifact is not rewritten after inspection.
- New G3/G5 diagnostics are explicitly post-full-study exploratory.
- Null, harmful and failure regimes remain retained.
- No ROS/Gazebo, physical-robot, certification or universal-safety conclusion follows from the synthetic studies.


## Expanded post-V1 exploratory evidence

A later retained exploratory artifact extends the post-V1 diagnostics without changing the frozen V1 claims.

**Source commit:** `562d2c01567188094c77fd433a7dccf3fbf40df4`  
**Workflow:** `36107200128`  
**Artifact:** `10851712188`  
**Digest:** `sha256:ff7985ee0e807351f0c0b63e5520ef535658957ffbc2fb1f3be468ca341c0df6`

### G1 — topology-dependent dependence is not a hand-built artifact

Across 40 held-out connected random 6x5 grids, every unordered pair of free nonterminal cells was evaluated as a two-hazard candidate. The survey covered 7,881 hazard pairs:

- negative interaction: 254 pairs;
- zero interaction: 7,375 pairs;
- positive interaction: 252 pairs;
- 37/40 maps contained at least one negative interaction;
- 25/40 maps contained at least one positive interaction;
- 23/40 maps contained both signs.

These counts are not estimates of real-world prevalence. Their role is narrower: both dependence-sensitivity directions occur beyond the serial/parallel hand constructions, while the exact two-hazard interaction identity predicts the sign.

### G3 — risk-budget deadlock breaking replicates as an information/risk frontier

The exploratory risk-budget benchmark was repeated over 10 independent seeds for all 12 combinations of true closure probability `{0.1,0.3,0.5,0.7}` and minimum-return threshold `{0.5,0.7,0.9}`.

Across all 12 conditions:

- mean exposures were nondecreasing from budget 5 -> 20 -> 50;
- mean observed failures were also nondecreasing from budget 5 -> 20 -> 50;
- budget 5 had lower mean absolute estimation error than the strict credible gate in 10/12 conditions;
- budget 20 did so in 10/12;
- budget 50 did so in 12/12.

A representative unsafe regime is true closure probability 0.7 with minimum return 0.7. The strict credible gate takes zero exposures and remains at mean absolute error 0.45. Budget 5 averages 7.4 exposures, 5.1 failures and error 0.159; budget 20 averages 28.6 exposures, 19.0 failures and error 0.101; budget 50 averages 70.4 exposures, 48.6 failures and error 0.048.

This does not make the risk-budget method a safety solution. It establishes the trade-off: trigger-conditioned identification can be purchased with explicitly admitted exposure risk. The next G3 method must obtain information more efficiently or introduce defensible side information / transfer assumptions.

### G5 — full reachable-state redundancy is large

The post-V1 exhaustive state-space diagnostic clarifies why the frozen early-goal A* timing result looked modest. At 6 duplicated-trigger modules, the raw augmented graph has 33,354 reachable position-history states, while the exact closure-event quotient has 126, a 264.7x ratio (99.62% reduction).

This strengthens G5 as an exact representation/computation companion, but does not convert the result into a universal online speedup claim.
