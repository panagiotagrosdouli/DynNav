# C10 Scientific Upgrade Notes — Human-Aware Ethics Policy

## What was already strong

Contribution 10 already connected navigation with human-aware and ethics-guided constraints.

The original module described:

- no-go zones,
- slow zones,
- announcement zones,
- avoid-if-possible zones,
- human proximity constraints,
- operator trust,
- language preferences.

This is important because autonomous navigation should not optimize only geometry, risk, and uncertainty. It must also respect human expectations and ethical constraints.

## Main weakness before this upgrade

The original README described the idea, but it did not provide a concrete decision layer.

A reviewer could ask:

> How does an ethical zone or low operator trust become an actual planner action?

or:

> Which constraints are hard, which are soft, and when should the robot ask for operator confirmation?

## New contribution added

C10 now includes:

```text
code/human_ethics_policy.py
experiments/eval_human_ethics_policy.py
```

The new policy layer maps context to planner-facing decisions:

- planner action,
- maximum speed,
- autonomy level,
- path allowed / blocked,
- announcement requirement,
- operator confirmation requirement,
- ethical cost multiplier,
- explanation.

## New benchmark

Run:

```bash
python contributions/10_human_language_ethics/experiments/eval_human_ethics_policy.py
```

Output:

```text
contributions/10_human_language_ethics/results/c10_human_ethics_policy.csv
```

The benchmark evaluates scenarios such as:

- normal corridor,
- human nearby,
- personal-space violation,
- no-go zone,
- slow zone,
- announce zone,
- low operator trust,
- ambiguous language instruction,
- soft ethical zone.

## Reviewer-safe claim

A stronger claim after this upgrade is:

> Contribution 10 converts human-aware and ethical navigation context into explicit planner actions, distinguishing hard constraints, soft penalties, speed adaptation, announcement requirements, and operator confirmation.

## Relationship to other contributions

C10 connects directly to:

- C05 safe mode when human-aware risk rises,
- C07 NBV when exploration would enter ethically sensitive areas,
- C11 VLM navigation agent for visual grounding,
- C17 topological semantic maps for semantic zones,
- C19 LLM mission planner for natural language commands,
- C20 failure explainer for human-readable explanations.

## Limitations

- The policy is interpretable and rule-based, not learned from human feedback.
- Ethical zone semantics are simplified.
- Real deployment requires human detection reliability, privacy policy, local norms, and institutional constraints.
- Language confidence is modeled as a scalar; real language grounding should include ambiguity classes.

## Next research step

The strongest extension is preference learning with safety constraints:

```text
human feedback -> preference model -> ethical planner cost / constraints
```

This would allow C10 to adapt to different operators, environments, and institutional policies while preserving hard safety and ethics rules.
