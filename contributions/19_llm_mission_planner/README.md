# Contribution 19 — LLM Mission Planner and Mission-Plan Validation

[![Module](https://img.shields.io/badge/Module-19-purple)](.) [![Type](https://img.shields.io/badge/Type-LLM%20%2F%20NLP-blue)](.) [![Status](https://img.shields.io/badge/Status-Core%20Upgraded-brightgreen)](.)

## Plain-language summary

A robot should be able to receive a mission in natural language:

```text
Go to the kitchen, then check the corridor, then exit.
```

Contribution 19 translates natural-language mission instructions into structured waypoint sequences compatible with DynNav's planning backend.

The upgraded version adds mission-plan validation:

> The system does not only parse language. It checks whether the parsed mission is ordered correctly, executable, and constraint-aware.

---

## Research Question

> **RQ19:** Can natural-language mission specifications be converted into executable robot plans while preserving waypoint order, semantic validity, and safety/ethics constraints?

This contribution studies:

- LLM-based mission parsing,
- offline keyword fallback,
- semantic waypoint extraction,
- waypoint ordering,
- zone-map grounding,
- execution-readiness validation,
- forbidden-zone and duplicate-step detection.

---

## Conceptual Pipeline

```text
natural-language instruction
      ↓
LLM parser or keyword fallback
      ↓
ordered semantic waypoints
      ↓
zone-map grounding
      ↓
mission-plan validation
      ↓
execution-ready plan or repair request
```

---

## Existing Components

The original C19 implementation includes:

- `Waypoint`,
- `Mission`,
- `LLMPlannerConfig`,
- `LLMMissionPlanner`,
- local LLM endpoint support,
- OpenAI-compatible API support,
- offline keyword fallback,
- metric coordinate resolution through a zone map.

---

## New Upgrade Added

C19 now includes:

```text
mission_plan_evaluator.py
```

This evaluator checks whether a generated mission plan is usable.

It reports:

- predicted sequence,
- expected sequence,
- ordering accuracy,
- exact sequence match,
- unresolved waypoint count,
- duplicate waypoint count,
- forbidden-zone violations,
- missing required waypoints,
- execution-readiness verdict,
- confidence.

---

## Files

```text
19_llm_mission_planner/
├── README.md
├── llm_mission_planner.py
├── mission_plan_evaluator.py
├── docs/
│   └── SCIENTIFIC_UPGRADE.md
├── experiments/
│   └── eval_mission_plan_quality.py
└── results/
    └── c19_mission_plan_quality.csv
```

---

## Quick Start

Parse an instruction offline:

```python
from contributions.19_llm_mission_planner.llm_mission_planner import LLMMissionPlanner

planner = LLMMissionPlanner()
mission = planner.parse("go to the kitchen then the corridor and exit")

zone_map = {
    "kitchen": (2.0, 3.0),
    "corridor": (5.0, 1.0),
    "exit": (8.0, 0.0),
}
mission = planner.resolve_to_metric(mission, zone_map)
```

Run the new mission-quality benchmark:

```bash
python contributions/19_llm_mission_planner/experiments/eval_mission_plan_quality.py
```

This generates:

```text
contributions/19_llm_mission_planner/results/c19_mission_plan_quality.csv
```

---

## Mission Quality Metrics

| Metric | Meaning |
|---|---|
| Ordering accuracy | Fraction of expected waypoints in the correct position |
| Exact sequence match | Whether predicted sequence exactly matches expected sequence |
| Unresolved waypoints | Predicted labels not found in the zone map |
| Duplicate waypoints | Repeated semantic destinations |
| Forbidden violations | Predicted waypoints in forbidden semantic zones |
| Missing required | Required waypoints omitted from the plan |
| Execution ready | True if no validation issue blocks execution |

---

## Scientific Contribution

The upgraded C19 contribution is not simply:

> Parse natural language into waypoints.

It is stronger:

> Evaluate whether language-generated missions are correctly ordered, semantically grounded, free from forbidden-zone violations, and ready for execution.

This makes language planning auditable instead of only convenient.

---

## Integration

- **Uses:** C17 topological semantic maps for zone grounding
- **Uses:** C10 ethical constraints for forbidden/private areas
- **Combines with:** C11 VLM navigation for visually grounded goals
- **Explained by:** C20 failure explainer when parsing or validation fails
- **Protected by:** C18 formal safety shields during execution

Recommended runtime interface:

```text
mission_plan = {
    raw_instruction,
    waypoints,
    metric_waypoints,
    confidence,
    validation_report
}
```

---

## Limitations

- The benchmark uses deterministic offline fallback for reproducibility.
- Real LLM performance should be evaluated using paraphrases, multilingual commands, and adversarial instructions.
- Human time savings are not measured yet.
- Language ambiguity is represented indirectly through plan validation failures.
- Mission repair is not yet implemented.

---

## Next Research Step

The strongest extension is constraint-aware mission repair:

```text
parsed mission
      ↓
validator detects issue
      ↓
repair or ask human
      ↓
confirmed executable plan
```

This would make C19 robust to ambiguous instructions, forbidden areas, and missing waypoints.

---

## Conclusion

Contribution 19 establishes the language-to-mission layer of DynNav.

The upgraded version makes the module stronger by validating whether parsed missions are correct, grounded, and execution-ready.
