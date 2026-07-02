# Contribution 20 — Multimodal Failure Explainer and Report Quality Evaluation

[![Module](https://img.shields.io/badge/Module-20-purple)](.) [![Type](https://img.shields.io/badge/Type-XAI%20%2F%20Diagnostics-blue)](.) [![Status](https://img.shields.io/badge/Status-Core%20Upgraded-brightgreen)](.)

## Plain-language summary

When a robot fails, a human operator should not have to inspect raw logs line by line.

Contribution 20 generates a structured, human-readable failure report that combines:

- scene context,
- causal root-cause analysis,
- STL / safety-monitor evidence,
- suggested corrective actions.

The upgraded version adds report-quality evaluation:

> The explainer is not judged only by whether it produces text, but by whether the report is complete, causally useful, action-oriented, and ready for an operator.

---

## Research Question

> **RQ20:** Can automated multimodal failure explanations reduce debugging effort by producing complete, causal, and actionable robot failure reports?

This contribution studies:

- failure-event representation,
- causal root-cause summaries,
- STL robustness summaries,
- corrective-action generation,
- human-readable Markdown reports,
- report-quality scoring,
- operator-readiness evaluation.

---

## Conceptual Pipeline

```text
failure event
      ↓
scene description + causal attribution + STL robustness
      ↓
structured failure report
      ↓
report-quality evaluator
      ↓
operator-ready diagnosis or missing-evidence warning
```

---

## Existing Components

The original C20 implementation includes:

- `FailureType`,
- `FailureEvent`,
- `FailureReport`,
- `MultimodalFailureExplainer`,
- scene-description fallback,
- causal root-cause integration,
- STL robustness summary,
- corrective-action templates,
- Markdown and dictionary report output.

---

## New Upgrade Added

C20 now includes:

```text
failure_report_evaluator.py
```

This evaluator scores generated reports using:

- completeness score,
- root-cause recall,
- corrective-action relevance,
- STL coverage,
- operator readiness,
- total report-quality score.

---

## Files

```text
20_multimodal_failure_explainer/
├── README.md
├── multimodal_failure_explainer.py
├── failure_report_evaluator.py
├── docs/
│   └── SCIENTIFIC_UPGRADE.md
├── experiments/
│   └── eval_failure_report_quality.py
└── results/
    └── c20_failure_report_quality.csv
```

---

## Quick Start

Generate a failure report:

```python
from contributions.20_multimodal_failure_explainer.multimodal_failure_explainer import (
    MultimodalFailureExplainer,
    FailureEvent,
    FailureType,
)

explainer = MultimodalFailureExplainer(use_vlm=False, use_causal=True)

event = FailureEvent(
    failure_type=FailureType.COLLISION,
    timestamp=12.5,
    robot_pos=(3.2, 4.1),
    robot_vel=(0.3, 0.0),
    sensor_readings={"min_obstacle_dist": 0.15},
    stl_robustness={"always_keep_distance": -0.3},
)

report = explainer.explain(event)
print(report.to_markdown())
```

Run the new report-quality benchmark:

```bash
python contributions/20_multimodal_failure_explainer/experiments/eval_failure_report_quality.py
```

This generates:

```text
contributions/20_multimodal_failure_explainer/results/c20_failure_report_quality.csv
```

---

## Report Quality Metrics

| Metric | Meaning |
|---|---|
| Completeness score | Whether scene, causes, STL summary, actions, and confidence are present |
| Root-cause recall | Fraction of expected root causes mentioned in the report |
| Corrective-action relevance | Fraction of expected action keywords covered |
| STL coverage | Whether safety-monitor evidence is included when required |
| Operator readiness | Whether the report is sufficiently complete and actionable |
| Total score | Weighted combined report-quality score |

---

## Scientific Contribution

The upgraded C20 contribution is not simply:

> Generate a failure report.

It is stronger:

> Evaluate whether generated failure reports contain the information an operator needs: what happened, why it likely happened, which safety constraints were violated, and what corrective actions should be tried.

This makes explainability measurable instead of purely qualitative.

---

## Integration

- **Uses:** C14 causal root-cause attribution
- **Uses:** C18 STL / CBF safety-shield evidence
- **Explains:** C19 mission-plan validation failures
- **Explains:** C08 IDS alerts and trust degradation
- **Explains:** C05 safe-mode activations
- **Can include:** C11 VLM scene descriptions when visual data is available

Recommended runtime interface:

```text
failure_report_input = {
    failure_event,
    scene_frame,
    causal_ranking,
    stl_robustness,
    planner_logs,
    sensor_readings
}
```

---

## Limitations

- Report-quality scoring is rule-based.
- Corrective-action relevance is keyword-based.
- The benchmark does not yet involve human operators.
- VLM scene explanation is optional and stubbed for offline reproducibility.
- Causal attribution quality depends on the SCM used by C14.

---

## Next Research Step

The strongest extension is human-in-the-loop evaluation:

```text
failure report
      ↓
operator diagnosis task
      ↓
debugging time + repair quality + trust rating
```

This would directly test whether automated explanations improve human debugging and replanning decisions.

---

## Conclusion

Contribution 20 establishes the failure-explanation layer of DynNav.

The upgraded version makes the module scientifically stronger by scoring explanation quality rather than only generating reports.
