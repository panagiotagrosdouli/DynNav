# Contribution 11 — VLM Navigation Agent with Goal Validation

[![Module](https://img.shields.io/badge/Module-11-purple)](.) [![Type](https://img.shields.io/badge/Type-Perception%20%2F%20VLM-blue)](.) [![Status](https://img.shields.io/badge/Status-Core%20Upgraded-brightgreen)](.)

## Plain-language summary

A Vision-Language Model can help a robot understand what it sees, but the robot should not blindly execute every VLM suggestion.

Contribution 11 uses a VLM as a high-level semantic navigation agent. The VLM looks at an RGB frame and proposes a semantic goal such as:

```json
{"region": "corridor", "goal": "go forward", "confidence": 0.85, "pixel_u": 320, "pixel_v": 240}
```

The upgraded version adds a validation layer before the semantic goal reaches the navigation planner.

The key idea is:

> VLM outputs should be treated as uncertain semantic proposals, not direct robot commands.

---

## Research Question

> **RQ11:** Can a foundation Vision-Language Model support semantic navigation while remaining safe against hallucinated or unreliable goals?

This contribution studies:

- VLM-based semantic goal generation,
- JSON goal parsing,
- pixel-to-metric waypoint projection,
- confidence filtering,
- semantic validation,
- human-confirmation fallback,
- hallucination-aware planner gating.

---

## Conceptual Pipeline

```text
RGB frame
      ↓
VLM semantic interpretation
      ↓
JSON goal proposal
      ↓
goal validation
      ↓
accept / reject / ask human
      ↓
metric waypoint and planner
```

---

## Existing Planner

The existing `VLMNavigationPlanner` sends an image to a local or cloud VLM endpoint and parses a structured semantic goal.

It supports:

- local Ollama / LLaVA-style endpoints,
- OpenAI-compatible VLM endpoints,
- semantic region labels,
- confidence scores,
- pixel hints,
- depth-based waypoint projection.

---

## New Upgrade Added

C11 now includes:

```text
vlm_goal_validator.py
```

This module validates VLM goals using:

- confidence threshold,
- allowed semantic regions,
- forbidden semantic words,
- pixel bounds,
- maximum waypoint distance,
- accept / reject / ask-human decision.

This prevents unsafe behaviour such as:

- executing a low-confidence instruction,
- navigating to a hallucinated region,
- following a pixel outside the image,
- accepting a waypoint that is implausibly far away,
- entering a restricted or private semantic region.

---

## Files

```text
11_vlm_navigation_agent/
├── README.md
├── vlm_planner.py
├── vlm_goal_validator.py
├── docs/
│   └── SCIENTIFIC_UPGRADE.md
├── experiments/
│   ├── eval_vlm_planner.py
│   └── eval_vlm_goal_validation.py
└── results/
    ├── vlm_eval.csv
    └── c11_vlm_goal_validation.csv
```

---

## Quick Start

Run the existing offline VLM planner evaluation:

```bash
python contributions/11_vlm_navigation_agent/experiments/eval_vlm_planner.py \
    --n_frames 20 \
    --out_csv contributions/11_vlm_navigation_agent/results/vlm_eval.csv
```

Run the new VLM goal-validation benchmark:

```bash
python contributions/11_vlm_navigation_agent/experiments/eval_vlm_goal_validation.py
```

This generates:

```text
contributions/11_vlm_navigation_agent/results/c11_vlm_goal_validation.csv
```

---

## Benchmark Scenarios

| Scenario | Expected decision |
|---|---|
| valid corridor goal | accept |
| low-confidence goal | ask human or reject |
| hallucinated region | ask human or reject |
| out-of-frame pixel | reject |
| far waypoint | reject |
| forbidden semantics | ask human or reject |

---

## Scientific Contribution

The upgraded C11 contribution is not simply:

> Use a VLM to choose a navigation goal.

It is stronger:

> Use a VLM as a semantic proposal generator and validate its output before allowing it to influence navigation.

This is important because foundation models can hallucinate, misground visual concepts, or produce overconfident but unsafe commands.

---

## Integration

- **Uses:** C10 human-aware ethics for forbidden/private regions
- **Feeds into:** A* planner and C17 topological semantic maps
- **Combines with:** C19 LLM mission planner for language-to-goal decomposition
- **Explained by:** C20 failure explainer when a VLM goal is rejected
- **Can trigger:** C05 safe mode or human confirmation when validation fails

Recommended runtime interface:

```text
vlm_output = {
    region,
    goal,
    confidence,
    pixel_hint,
    metric_waypoint,
    validation_decision
}
```

---

## Production Upgrade

Local VLM example:

```python
config = VLMPlannerConfig(
    model_name="llava-1.6",
    api_endpoint="http://localhost:11434/api/chat"
)
```

Cloud VLM example:

```python
config = VLMPlannerConfig(
    model_name="gpt-4-vision-preview",
    api_endpoint="https://api.openai.com/v1/chat/completions"
)
```

For real robot deployment, the validation layer should remain active even when using a stronger VLM.

---

## Limitations

- The validator is rule-based and cannot prove semantic correctness.
- Allowed and forbidden semantic regions are hand-defined.
- Pixel validity does not guarantee correct object grounding.
- Depth back-projection currently uses a simplified camera model.
- Real deployment should use calibrated camera intrinsics and temporal consistency over multiple frames.

---

## Next Research Step

The strongest extension is temporal semantic consistency:

```text
single-frame VLM proposal
      ↓
multi-frame semantic agreement
      ↓
validated semantic waypoint
```

This would reduce hallucinated goals by requiring stable VLM evidence across time.

---

## Conclusion

Contribution 11 establishes the foundation-model semantic navigation layer of DynNav.

The upgraded version makes this layer safer by validating VLM outputs before they are passed to downstream planners.
