# C19 Scientific Upgrade Notes — Mission-Plan Quality Evaluation

## What was already strong

Contribution 19 already implemented the core language-to-navigation idea:

> Convert natural-language mission instructions into structured waypoint sequences that DynNav can execute.

The existing module supports:

- LLM parsing,
- local Ollama-style endpoint use,
- offline keyword fallback,
- waypoint ordering,
- action labels,
- metric coordinate resolution through a zone map.

This is important because natural language can reduce the burden of manual waypoint programming.

## Main weakness before this upgrade

The original module could produce a waypoint sequence, but it did not evaluate whether the mission was correct, executable, or constraint-aware.

A reviewer could ask:

> Did the planner preserve the requested waypoint order?

or:

> Did it produce unresolved or duplicate waypoints?

or:

> Did it include forbidden semantic zones?

## New contribution added

C19 now includes:

```text
mission_plan_evaluator.py
experiments/eval_mission_plan_quality.py
```

The new evaluator reports:

- predicted waypoint sequence,
- expected waypoint sequence,
- ordering accuracy,
- exact sequence match,
- unresolved waypoint count,
- duplicate waypoint count,
- forbidden-zone violations,
- missing required waypoints,
- execution-readiness verdict,
- confidence.

## New benchmark

Run:

```bash
python contributions/19_llm_mission_planner/experiments/eval_mission_plan_quality.py
```

Output:

```text
contributions/19_llm_mission_planner/results/c19_mission_plan_quality.csv
```

The benchmark evaluates instructions such as:

- go to the kitchen, corridor, and exit,
- inspect the office and return to charging,
- start at the entrance and check storage,
- avoid forbidden/private areas,
- handle duplicate corridor mentions.

## Reviewer-safe claim

A stronger claim after this upgrade is:

> Contribution 19 evaluates language-generated navigation missions using execution-readiness metrics, including ordering accuracy, exact sequence match, unresolved waypoints, duplicate waypoints, missing required waypoints, and forbidden-zone violations.

## Relationship to other contributions

C19 connects directly to:

- C10 ethical constraints for forbidden zones,
- C11 VLM semantic goal validation,
- C17 topological semantic maps for zone grounding,
- C20 failure explanation when mission parsing or execution fails,
- C18 formal safety shields during execution.

## Limitations

- The benchmark uses deterministic offline fallback for reproducibility.
- It does not measure real human time savings yet.
- Language ambiguity is only partially captured.
- Real LLM evaluation should include paraphrase sets, multilingual commands, and adversarial instructions.

## Next research step

The strongest extension is constraint-aware mission repair:

```text
parsed mission -> validator detects issue -> repaired mission -> human-confirmable plan
```

This would make C19 more robust to ambiguous instructions, forbidden areas, and missing waypoints.
