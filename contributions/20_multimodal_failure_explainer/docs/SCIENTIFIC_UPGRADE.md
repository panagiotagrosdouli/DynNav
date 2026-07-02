# C20 Scientific Upgrade Notes — Failure-Report Quality Evaluation

## What was already strong

Contribution 20 already provided a useful explainability layer:

> After a navigation failure, generate a structured report combining scene context, causal attribution, STL/safety-monitor evidence, and suggested corrective actions.

The existing module includes:

- failure event representation,
- failure-type taxonomy,
- scene description fallback,
- causal root-cause extraction,
- STL robustness summary,
- corrective-action templates,
- Markdown and JSON report output.

This is important because debugging robot failures requires more than raw logs.

## Main weakness before this upgrade

The original module generated reports, but did not evaluate report quality.

A reviewer could ask:

> Is the explanation complete?

or:

> Does it mention the expected root causes and useful corrective actions?

or:

> Is the report ready for an operator to act on?

## New contribution added

C20 now includes:

```text
failure_report_evaluator.py
experiments/eval_failure_report_quality.py
```

The new evaluator reports:

- completeness score,
- root-cause recall,
- corrective-action relevance,
- STL coverage,
- operator-readiness score,
- total report-quality score.

## New benchmark

Run:

```bash
python contributions/20_multimodal_failure_explainer/experiments/eval_failure_report_quality.py
```

Output:

```text
contributions/20_multimodal_failure_explainer/results/c20_failure_report_quality.csv
```

The benchmark evaluates:

- collision near obstacle,
- sensor fault,
- irreversible state.

## Reviewer-safe claim

A stronger claim after this upgrade is:

> Contribution 20 evaluates generated failure explanations using report-quality metrics: completeness, root-cause coverage, corrective-action relevance, STL evidence coverage, and operator readiness.

## Relationship to other contributions

C20 connects directly to:

- C14 causal root-cause attribution,
- C18 STL/CBF safety-shield evidence,
- C19 mission-plan validation failures,
- C08 IDS alerts,
- C05 safe-mode activation logs.

## Limitations

- The report-quality evaluator uses rule-based expectations.
- It does not yet measure real human debugging time.
- Corrective-action relevance is keyword-based, not judged by a human study.
- VLM scene explanation remains optional and stubbed for offline reproducibility.

## Next research step

The strongest extension is human-in-the-loop explanation evaluation:

```text
failure report -> operator diagnosis task -> debugging time / repair quality
```

This would directly test whether automated explanations improve human debugging and replanning decisions.
