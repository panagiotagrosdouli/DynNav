# Contribution Readiness Checklist

Use this checklist before marking a DynNav contribution as upgraded, complete, or publication-ready.

## 1. Scientific framing

- [ ] The module states one clear research question.
- [ ] The module explains why the question matters for robot navigation.
- [ ] The assumptions are explicit.
- [ ] The limitations are explicit.
- [ ] The module avoids claiming more than the experiment supports.

## 2. Algorithmic clarity

- [ ] The main algorithm is described in words.
- [ ] Inputs and outputs are documented.
- [ ] Important hyperparameters are listed.
- [ ] The module explains how uncertainty, risk, safety, or learning enters the planner.
- [ ] The module separates implemented behavior from planned future work.

## 3. Reproducibility

- [ ] There is a documented command to run the experiment.
- [ ] The command works from the repository root.
- [ ] Random seeds are controlled or reported.
- [ ] Runtime is reported approximately.
- [ ] Outputs are saved to a documented path.

## 4. Metrics

- [ ] The module reports at least one task-performance metric.
- [ ] The module reports at least one safety, uncertainty, risk, or robustness metric when applicable.
- [ ] Metric definitions are included.
- [ ] Units are specified where relevant.
- [ ] The result is not only a qualitative screenshot or printout.

## 5. Baselines

- [ ] At least one meaningful baseline is included.
- [ ] The baseline is described fairly.
- [ ] The comparison uses the same scenario and seed policy.
- [ ] Improvements are reported quantitatively.
- [ ] Cases where the baseline wins are not hidden.

## 6. Ablations

- [ ] A core design component is removed or varied.
- [ ] The ablation shows whether the proposed component actually matters.
- [ ] Sensitivity to key thresholds or weights is checked where relevant.

## 7. Failure analysis

- [ ] At least one failure mode is described.
- [ ] The module explains when it should not be trusted.
- [ ] The module distinguishes perception, planning, control, and evaluation failures when possible.

## 8. Code quality

- [ ] The module can be imported without side effects.
- [ ] Experiment scripts use `if __name__ == "__main__"`.
- [ ] Core logic is separated from plotting or CLI code.
- [ ] Tests or smoke checks exist for critical functions.
- [ ] Outputs are deterministic when the seed is fixed.

## 9. Documentation quality

- [ ] README or module notes include purpose, method, command, metrics, and limitations.
- [ ] Tables are readable.
- [ ] Claims are supported by logged results.
- [ ] Future work is clearly labeled as future work.

## Readiness levels

| Level | Meaning |
|---|---|
| Prototype | Code exists but evidence is limited. |
| Reproducible demo | A documented command runs and produces saved outputs. |
| Benchmark-ready | Includes metrics, baseline, and repeated trials. |
| Paper-ready | Includes ablations, failure analysis, statistics, and clear limitations. |

## Recommended module badge

Each module README can include:

```text
Readiness: Prototype / Reproducible demo / Benchmark-ready / Paper-ready
Evidence: path/to/results.csv
Main limitation: ...
```
