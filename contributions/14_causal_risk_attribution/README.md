# Contribution 14 — Causal Risk Attribution and Root-Cause Evaluation

[![Module](https://img.shields.io/badge/Module-14-purple)](.) [![Type](https://img.shields.io/badge/Type-Causal%20AI-blue)](.) [![Status](https://img.shields.io/badge/Status-Core%20Upgraded-brightgreen)](.)

## Plain-language summary

When a robot fails, it is not enough to say:

```text
The risk was high.
```

The more useful question is:

```text
Why did the risk become high?
```

Contribution 14 uses a Structural Causal Model to reason about navigation failures. It asks counterfactual questions such as:

```text
Would the collision still have happened if sensor noise had been zero?
Would the failure disappear if map accuracy had been restored?
```

The upgraded version adds benchmark cases with known injected root causes, so causal attribution can be evaluated rather than only described.

---

## Research Question

> **RQ14:** Can counterfactual causal reasoning identify root causes of navigation failure more usefully than correlation or anomaly flags alone?

This contribution studies:

- structural causal models,
- observational queries,
- counterfactual interventions,
- average causal effects,
- root-cause ranking,
- synthetic injected failure causes,
- attribution accuracy.

---

## Conceptual Pipeline

```text
navigation failure episode
      ↓
SCM observational query
      ↓
counterfactual interventions
      ↓
root-cause ranking
      ↓
attribution benchmark
      ↓
targeted mitigation recommendation
```

---

## Causal Graph

The default SCM uses the following simplified causal structure:

```text
sensor_noise → localization_error → obstacle_detection → path_risk → collision
            ↘ map_accuracy        ↗
```

Interpretation:

- sensor noise can degrade localization,
- sensor noise can reduce map accuracy,
- localization error and sensor noise can degrade obstacle detection,
- poor map accuracy and poor obstacle detection increase path risk,
- path risk and localization error increase collision probability.

---

## Existing SCM Methods

| Method | Description |
|---|---|
| `observational_query(noise)` | Forward evaluation through the causal graph |
| `counterfactual_query(noise, intervention)` | Intervention-style query using the same episode noise |
| `average_causal_effect(X, Y, ...)` | Monte-Carlo ACE estimation |
| `root_cause_ranking(noise)` | Shapley-inspired ablation ranking |

---

## New Upgrade Added

C14 now includes:

```text
causal_attribution_evaluator.py
```

This evaluator measures whether the SCM recovers known injected root causes.

It reports:

- predicted root cause,
- true root-cause rank,
- top-1 correctness,
- baseline outcome value,
- counterfactual outcome value,
- counterfactual risk reduction,
- full root-cause ranking.

---

## Files

```text
14_causal_risk_attribution/
├── README.md
├── causal_risk.py
├── causal_attribution_evaluator.py
├── docs/
│   └── SCIENTIFIC_UPGRADE.md
├── experiments/
│   └── eval_root_cause_attribution.py
└── results/
    └── c14_root_cause_attribution.csv
```

---

## Quick Start

Run the new root-cause attribution benchmark:

```bash
python contributions/14_causal_risk_attribution/experiments/eval_root_cause_attribution.py
```

This generates:

```text
contributions/14_causal_risk_attribution/results/c14_root_cause_attribution.csv
```

---

## Benchmark Cases

The new benchmark includes synthetic failure episodes with known root causes:

| Case | Injected root cause |
|---|---|
| `sensor_noise_failure` | sensor noise |
| `localization_drift_failure` | localization error |
| `map_accuracy_failure` | map accuracy |
| `obstacle_detection_failure` | obstacle detection |
| `path_risk_failure` | path risk |

For each case, the benchmark checks whether the SCM ranking places the true cause near the top.

---

## Metrics

| Metric | Meaning |
|---|---|
| Top-1 accuracy | Whether the highest-ranked cause is the true injected cause |
| True-cause rank | Rank position of the true injected cause |
| Counterfactual outcome | Failure outcome after intervening on the true cause |
| Counterfactual reduction | Baseline outcome minus counterfactual outcome |
| Full ranking | Ordered attribution scores for all candidate causes |

---

## Scientific Contribution

The upgraded C14 contribution is not simply:

> Build a causal graph for navigation failures.

It is stronger:

> Evaluate whether a causal root-cause attribution method recovers known injected failure causes and whether counterfactual interventions reduce predicted collision risk.

This makes the module scientifically testable.

---

## Integration

- **Receives:** anomaly evidence from C08 security / IDS
- **Receives:** risk and failure data from C03, C04, C05, and C12
- **Supports:** C20 multimodal failure explanation
- **Can use:** C25 adversarial attack simulator to create controlled causal failures
- **Can guide:** targeted safe-mode or replanning mitigation after failure

Recommended runtime interface:

```text
failure_episode = {
    sensor_noise,
    localization_error,
    map_accuracy,
    obstacle_detection,
    path_risk,
    collision
}
```

---

## Limitations

- The SCM is hand-specified and simplified.
- Synthetic injected causes are useful for benchmark sanity checks but do not prove real-world causal validity.
- Root-cause rankings depend on the structural equations.
- Real deployment requires validating the causal graph with robot logs and expert knowledge.
- Counterfactual results should be interpreted as model-based explanations, not guaranteed physical truth.

---

## Next Research Step

The strongest extension is intervention-guided repair:

```text
failure episode
      ↓
causal attribution
      ↓
targeted mitigation
      ↓
replay / validation
```

This would turn C14 from a post-hoc diagnostic module into a prescriptive repair module.

---

## Conclusion

Contribution 14 establishes the causal failure-analysis layer of DynNav.

The upgraded version makes the module stronger by evaluating root-cause attribution on known injected failures and measuring counterfactual risk reduction.
