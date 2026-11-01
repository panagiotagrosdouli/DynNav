# Proposed discriminating experiment for DynNav V3
**Status: DESIGN PROPOSAL ONLY — not preregistered, frozen, approved, implemented, run, or evaluated.**
**Date:** 1 November 2026.
**Motivation:** a strong reviewer will correctly note that a history-free fixed-field ablation is intentionally information-deficient, and that action-induced topology and safe-return planning both have extensive prior art. A new prospective evaluation should test whether the *specific action-triggered stochastic closure model* provides useful decisions beyond this illustrative ablation.

## Research hypotheses (prospective)

- **H1 (conditional mechanism):** for task-matched stochastic closure distributions, actual executed-trigger history changes the *conditional predicted probability of safe-set connectivity* at aliased geometric states. This is a mechanism property, expected under the formal model; the statistical study measures prevalence and effect size rather than treating this as algorithmic novelty.
- **H2 (decision consequence):** on independent, mandatory-trigger maps, history-conditioned route decisions reduce realized return-infeasibility versus a same-oracle fixed-marginal control, with paired scenario-level uncertainty intervals and explicitly reported path-length cost. This hypothesis may fail in some maps.
- **H3 (nontrivial comparators):** the benefit is also characterized against a model that has the correct *information available at decision time* and an independently varied exogenous-closure process. **A fully informed state-augmented optimal-policy baseline is not expected to be beaten by an equivalent A* reference planner.** Fairness is the scientific target; do not invent dominance.
- **H4 (boundary):** as closure probabilities approach 0 or 1, the results approach the no-closure and deterministic-self-deletion limiting regimes under the declared *post-trajectory* event semantics, while stochastic midrange cases may have different cost-risk trade-offs.

## Key distinction to preserve

V3's current return-connectivity target evaluates possible closures **after the planning/trajectory context**; it does **not** simulate realized closures appearing and being observed during a mission. The deterministic p=1 limit is therefore a model-checking comparison, *not* a claim that the implementation reproduces all deterministic self-deleting graph movement semantics.

## Dataset design proposal — freeze only after independent review

1. Use a **new** map-generator commit and generator family IDs, fixed before running. Proposed scale: **120 new maps** across 6 route-topology families, each with 20 independently sampled maps, and **200 paired execution seeds/map**. These are prospective design values, **not completed experiments**. No overlap with the 96-scenario V3 publication suite, its map IDs or its random seeds.
2. Include graph motifs where every outbound route activates at least one hazard; include bridge, fork, multi-cut, bypass, loop, and cluttered-room families. Avoid only hand-picking easy, trigger-free detours.
3. Predefine one split of generator seeds for implementation debugging and a held-out *sealed* evaluation split. The author of the planner must not inspect held-out outcomes before the final SHA and analysis script are frozen.
4. Sweep predeclared closure-probability groups (e.g. low, medium, high) and record exact probability vectors, trigger-to-closure map, robot start/goal, safe set, shared random closure uniforms, executed-trigger history, and the true evaluation event.
5. Retain all attempted mission trials, including invalid protocol trials with explicit reason codes. Do not silently discard failed map generations or missing paths; report coverage/mission completion separately from safe-return risk.

## Comparators and their scientific roles

| Method | Information at planning | Objective / return oracle | Why include |
|---|---|---|---|
| **Shortest / distance-first** | Position, nominal topology | Distance-only | Usual task baseline |
| **Fixed-marginal exact** | Position, predeclared fixed hazard field | **Same exact return-connectivity oracle and same additive objective** as proposed method | Controlled information-removal ablation, *not SOTA* |
| **Activated-history exact (DynNav)** | Position, actual set of executed activated triggers | Exact return-connectivity oracle | Main method for frozen finite model |
| **Full-state reference solver** | **Same activated state** as DynNav, same model, reward and safe set | Independently implemented small-state dynamic-programming/exhaustive route reference | Sanity/optimality check for model and A* implementation; equivalent formulation is expected to agree, not to be outperformed |
| **Hard safe-return threshold** | Same activated state | Thresholded return probability | Cost/success/feasibility Pareto comparison |
| **Exogenous matched-closure control** | No action-trigger causality; marginal probabilities agreed in advance | Same return evaluation under an action-*independent* closure model | Tests whether the explanatory mechanism specifically depends on action-triggered activation |

Do **not** compare planners using different probabilities, closure draws, information access, nominal route costs or completion denominators while calling them "fair SOTA comparisons." Proper MDP policy and V3 history-conditioned A* may be mathematically equivalent under the same information/finite model.

## Endpoints and analyses (proposal, not performed)

- **Primary:** paired (DynNav minus fixed-marginal) *operational return-infeasibility*, averaged **per generated map** before across-map inference. Report a paired map-level bootstrap 95% CI, exact count of maps improved/worsened/tied, and absolute risk differences. Treat maps as inferential units; don't present 120 x 200 trial rows as 24,000 independent maps.
- **Co-primary interpretability metric:** fraction of matched (map,seed) scenarios in which the *chosen route or activated-hazard set differs*, specifically against correct-information alternatives. A calibration improvement with identical action decisions is not itself an operational planning improvement.
- **Secondary:** return reliability, mission completion and invalid-trial counts, path length, hazard activations, computation time/memory, structural cut width, probability-calibration metrics when corresponding empirical event frequencies are valid, and soft-versus-hard Pareto curves.
- **Model checks:** same-position/different-activation counterexamples, never-executed triggers not activated, reverse-direction nonactivation, repeated-activation of same cell counted once, p=0 and p=1 limits, joint-cut optimism in approximate oracle.
- **Statistical discipline:** specify one primary effect and planned sample size *before* inspecting the held-out output; keep all exploratory subgroup claims separate, with multiplicity policy where appropriate. Plot paired effect size and uncertainty, not only p-values.
- **Stop conditions:** if stronger information-matched controls tie or exceed DynNav, record the negative result; limit the manuscript claim to a useful **model/representation measurement**. No changing test seeds, maps, objectives or threshold values after outcome inspection.

## Implementation and evidence gate

Before any new result enters `paper/dynnav_r/main.tex`:

- [ ] Independent researcher checks mathematical and semantic parity with the frozen V3 code.
- [ ] Generator + exact map set + comparator code + analysis + seeds + preregistration text frozen together in a SHA and CI workflow that prevents post-outcome modification.
- [ ] Code passes Python regression and forward-model consistency checks.
- [ ] Retain raw paired rows, generator metadata, reason-coded exclusions, environment and dependency versions, SHA256 digests, and analysis script.
- [ ] Publish a separate post-outcome review (positive or null), then decide whether adding evidence justifies rewriting the conference abstract and rebuilding the IEEE paper.

**Scientific integrity:** this file adds **zero measured results**, makes no guarantee of novelty or acceptance, and does not change the existing V3 paper or experimental freeze.
