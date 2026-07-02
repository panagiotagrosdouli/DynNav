# C11 Scientific Upgrade Notes — VLM Goal Validation

## What was already strong

Contribution 11 already introduced a high-level semantic navigation idea:

> Use a Vision-Language Model to interpret camera frames and propose navigation goals.

The existing planner supports VLM-style outputs with:

- semantic region labels,
- natural-language goals,
- confidence values,
- pixel hints,
- depth-based metric waypoint projection.

This is valuable because it connects foundation models with robot navigation.

## Main weakness before this upgrade

A VLM should not be trusted blindly.

A reviewer could ask:

> What happens if the VLM hallucinates a region, produces a low-confidence goal, points outside the image, or suggests a semantically forbidden area?

Without validation, the VLM output can become a dangerous planner input.

## New contribution added

C11 now includes:

```text
vlm_goal_validator.py
experiments/eval_vlm_goal_validation.py
```

The validation layer checks:

- confidence threshold,
- allowed semantic regions,
- forbidden semantic words,
- pixel hint bounds,
- maximum waypoint distance,
- whether the goal should be accepted, rejected, or sent to a human.

## New benchmark

Run:

```bash
python contributions/11_vlm_navigation_agent/experiments/eval_vlm_goal_validation.py
```

Output:

```text
contributions/11_vlm_navigation_agent/results/c11_vlm_goal_validation.csv
```

The benchmark evaluates:

- valid corridor goal,
- low-confidence goal,
- hallucinated region,
- out-of-frame pixel,
- far waypoint,
- forbidden semantics.

## Reviewer-safe claim

A stronger claim after this upgrade is:

> Contribution 11 treats VLM outputs as uncertain semantic proposals rather than direct navigation commands. It validates confidence, semantics, pixel geometry, waypoint plausibility, and forbidden concepts before a goal reaches the planner.

## Relationship to other contributions

C11 connects to:

- C10 human-aware ethics for forbidden or private semantic regions,
- C17 topological semantic maps for grounded semantic navigation,
- C19 LLM mission planning for language-to-goal decomposition,
- C20 failure explanation for human-readable rejected-goal reports.

## Limitations

- The validator is rule-based and does not prove semantic correctness.
- Allowed and forbidden semantic vocabularies are hand-defined.
- Pixel validity does not guarantee correct object grounding.
- Real deployment needs camera calibration, depth uncertainty, and semantic consistency over time.

## Next research step

The strongest extension is temporal semantic consistency:

```text
single-frame VLM goal -> multi-frame agreement -> validated semantic waypoint
```

This would reduce hallucinations by requiring semantic agreement across multiple frames before committing to a navigation goal.
