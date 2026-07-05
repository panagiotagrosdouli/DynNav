# DynNav v2 Research Roadmap

## Goal

DynNav v2 aims to turn the repository from a collection of modular navigation experiments into a lab-grade research platform for uncertainty-aware, risk-sensitive, and learning-augmented robot navigation in unknown environments.

The target is not to claim that DynNav already outperforms established robotics laboratories. The target is to make the project scientifically readable, reproducible, comparable, and extensible enough that a robotics researcher can evaluate it seriously.

## Central research question

How should an autonomous mobile robot plan, replan, and explore when its map, sensor observations, learned predictions, communication inputs, and high-level goals are uncertain or partially unreliable?

## Research thesis

A navigation system operating in unknown environments should not optimize path length alone. It should optimize a multi-objective cost that explicitly accounts for:

- geometric path cost,
- probabilistic collision risk,
- epistemic and aleatoric uncertainty,
- tail risk under rare but severe failures,
- recoverability after a bad decision,
- energy and communication feasibility,
- semantic and human-aware constraints,
- runtime safety guarantees.

A canonical DynNav v2 objective is:

```text
J(path) = alpha * length(path)
        + beta  * expected_risk(path)
        + gamma * CVaR_risk(path)
        + delta * uncertainty(path)
        + eta   * irreversibility(path)
        + zeta  * resource_cost(path)
        + rho   * intervention_cost(path)
```

The exact weights must not be hard-coded as a claim of optimality. They should be evaluated through ablations, sensitivity analysis, and task-specific trade-off curves.

## Scientific positioning

DynNav v2 should be positioned against four families of methods:

1. **Classical replanning**: A*, D*, D* Lite, RRT*, DWA, TEB, Nav2.
2. **Risk-aware planning**: expected-risk, max-risk, chance-constrained, and CVaR planners.
3. **Learning-augmented navigation**: learned heuristics, learned local policies, learned world models, and foundation-model-assisted planning.
4. **Safety-constrained autonomy**: runtime shields, control barrier filters, STL monitors, and human-aware constraints.

The contribution should be framed as an integrated evaluation framework, not as a single monolithic algorithm.

## DynNav v2 pillars

### 1. Uncertainty as a first-class planning signal

Every planner-facing state should expose uncertainty rather than hiding it inside perception or mapping.

Required artifacts:

- calibrated uncertainty metrics,
- reliability diagrams or equivalent calibration summaries,
- Brier score / NLL / ECE where probabilistic outputs are used,
- planner ablations with uncertainty disabled, raw, and calibrated.

### 2. Risk-sensitive decision making

DynNav should distinguish average risk from tail risk.

Required artifacts:

- expected risk,
- max risk,
- CVaR risk,
- risk-length Pareto curves,
- explicit failure cases where shortest paths are unsafe.

### 3. Recoverability and irreversibility

A path should not only be judged by whether it reaches the goal. It should also be judged by whether the robot preserves future options.

Required artifacts:

- returnability score,
- escape-option count,
- bottleneck exposure,
- feasibility after unexpected obstacle insertion,
- comparison between naive and recoverability-aware planning.

### 4. Prediction-aware dynamic navigation

Dynamic obstacles should be represented as future occupancy distributions rather than only current obstacle cells.

Required artifacts:

- future occupancy maps,
- prediction error metrics,
- risk over a planning horizon,
- comparison between reactive-only and prediction-aware navigation.

### 5. Runtime safety layer

Learning-based modules should be treated as proposals, not as trusted controllers.

Required artifacts:

- shielded vs unshielded evaluation,
- intervention rate,
- minimum distance to obstacles,
- STL robustness or equivalent formal safety score,
- correction cost.

### 6. Reproducibility and comparability

Every module should provide the same minimum reproducibility interface.

Required artifacts:

- command to run the experiment,
- deterministic seed support,
- CSV or JSON output,
- baseline comparison,
- metric definitions,
- limitations section,
- expected runtime.

## Minimum benchmark suite

DynNav v2 should include at least the following benchmark categories.

| Category | Purpose | Core metrics |
|---|---|---|
| Static unknown maps | Test exploration and replanning | success rate, path length, replans, runtime |
| Dynamic obstacles | Test prediction and reaction | collision rate, min distance, prediction error |
| Noisy sensing | Test uncertainty handling | calibration error, localization drift, risk score |
| Adversarial perturbations | Test robustness | detection F1, degradation, recovery success |
| Human-aware zones | Test semantic constraints | violation count, speed adaptation, confirmations |
| Multi-robot scenarios | Test coordination | conflicts, communication cost, team success |
| Resource-limited missions | Test energy/connectivity | feasibility verdict, margin, relay/recharge need |
| Safety-shield stress tests | Test formal safety | violations, interventions, correction cost |

## Required baseline policy

Each new contribution should compare against at least one of the following:

- naive shortest-path planner,
- classical risk-unaware planner,
- uncalibrated uncertainty version,
- no-shield version,
- no-prediction reactive version,
- random or greedy policy,
- existing Nav2-style baseline where applicable.

A module should not be marked as research-complete unless it includes a baseline and a measurable metric.

## Publication-readiness checklist

A module is publication-ready only when it satisfies all of the following:

- [ ] Clear problem statement.
- [ ] Explicit assumptions.
- [ ] Algorithm description.
- [ ] Baselines.
- [ ] Quantitative metrics.
- [ ] Ablation study.
- [ ] Limitations.
- [ ] Reproducible command.
- [ ] Stored result artifact.
- [ ] Short scientific note explaining what the result does and does not prove.

## Near-term implementation plan

### Phase 1 — Repository credibility

- Standardize README claims.
- Add benchmark protocol.
- Add contribution template.
- Add reproducibility checklist.
- Add issue templates for research modules, experiments, and paper-readiness tasks.

### Phase 2 — Core benchmark runner

- Add a unified benchmark manifest.
- Add machine-readable metric schema.
- Add comparison table generator.
- Add smoke tests for all lightweight experiments.

### Phase 3 — DynNav v2 algorithmic core

- Implement unified risk/uncertainty cost interface.
- Add prediction-aware future occupancy API.
- Add planner ablation hooks.
- Add deterministic scenario generator.

### Phase 4 — Research presentation

- Add figures for architecture and benchmark pipeline.
- Add a paper-style technical report skeleton.
- Add results tables generated from benchmark outputs.
- Add BibTeX/citation metadata for the modules.

## What DynNav v2 should avoid

- Overclaiming state-of-the-art performance without standardized benchmarks.
- Mixing speculative future work with implemented results.
- Reporting only reward or path length when safety is the actual objective.
- Treating foundation models as reliable planners without validation.
- Treating learned policies as safe without runtime monitoring.
- Adding many modules without a shared evaluation protocol.

## Success definition

DynNav v2 is successful when an external robotics researcher can clone the repository, run a documented benchmark, inspect the output metrics, understand each module's assumptions, and compare DynNav against a baseline without needing private context from the author.
