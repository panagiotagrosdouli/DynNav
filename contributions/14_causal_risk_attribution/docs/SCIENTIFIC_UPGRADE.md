# C14 Scientific Upgrade Notes — Root-Cause Attribution Benchmark

## What was already strong

Contribution 14 already introduced an important scientific direction for DynNav:

> Diagnose why a navigation failure happened using counterfactual causal reasoning, not only correlation or anomaly flags.

The existing module includes:

- a Structural Causal Model for navigation failures,
- observational queries,
- counterfactual interventions,
- average causal effect estimation,
- Shapley-inspired root-cause ranking.

This is valuable because a robot should not only know that something went wrong. It should identify which mechanism most likely caused the failure.

## Main weakness before this upgrade

The original module could produce a root-cause ranking, but it did not evaluate whether the ranking was correct on cases with known causes.

A reviewer could ask:

> Does the causal attribution method recover the true injected failure cause?

or:

> How much does the recommended counterfactual intervention actually reduce collision risk?

## New contribution added

C14 now includes:

```text
causal_attribution_evaluator.py
experiments/eval_root_cause_attribution.py
```

The new benchmark evaluates synthetic navigation failure cases with known injected root causes.

It reports:

- predicted root cause,
- true root-cause rank,
- top-1 attribution accuracy,
- baseline outcome value,
- counterfactual outcome value,
- counterfactual risk reduction,
- full root-cause ranking.

## New benchmark

Run:

```bash
python contributions/14_causal_risk_attribution/experiments/eval_root_cause_attribution.py
```

Output:

```text
contributions/14_causal_risk_attribution/results/c14_root_cause_attribution.csv
```

The benchmark includes cases such as:

- sensor-noise failure,
- localization-drift failure,
- map-accuracy failure,
- obstacle-detection failure,
- path-risk failure.

## Reviewer-safe claim

A stronger claim after this upgrade is:

> Contribution 14 evaluates causal root-cause attribution against synthetic failure cases with known injected causes, reporting top-1 attribution accuracy, rank of the true cause, and counterfactual collision-risk reduction.

## Relationship to other contributions

C14 connects directly to:

- C08 IDS alerts, which indicate that something abnormal happened,
- C05 safe mode, which may be triggered after causal diagnosis,
- C20 failure explanation, which can convert the attribution result into human-readable explanations,
- C25 adversarial attack simulation, which can generate controlled causal failure scenarios.

## Limitations

- The SCM is hand-specified and simplified.
- Synthetic injected causes are useful for testing but do not prove real-world causal validity.
- Root-cause rankings depend on the correctness of the structural equations.
- Real deployment requires learning or validating the causal graph from logged robot data and expert knowledge.

## Next research step

The strongest extension is intervention-guided repair:

```text
failure episode -> causal attribution -> targeted mitigation -> replay / validation
```

This would make C14 not only diagnostic, but also prescriptive: the system would recommend the intervention most likely to prevent the same failure from recurring.
