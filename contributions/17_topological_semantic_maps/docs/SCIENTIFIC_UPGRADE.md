# C17 Scientific Upgrade Notes — Semantic Grounding and Sparse Graph Planning

## What was already strong

Contribution 17 already introduced a useful high-level navigation abstraction:

> Instead of planning only over dense metric grids, represent the environment as a sparse graph of semantic places and traversable transitions.

The existing module includes:

- semantic nodes,
- semantic edges,
- Dijkstra planning over a topological graph,
- edge invalidation when a transition becomes blocked,
- open-vocabulary-style grounding using embedding similarity,
- JSON-style serialization.

This is valuable because long-horizon navigation often depends on semantic structure: rooms, corridors, doors, exits, labs, offices, and other meaningful regions.

## Main weakness before this upgrade

The original module demonstrated the data structure, but did not evaluate the two core claims:

1. Can semantic queries be grounded to the correct node?
2. Can the topological graph still plan when a transition becomes blocked?

A reviewer could ask:

> Does this representation actually support instruction grounding and adaptive route repair?

## New contribution added

C17 now includes:

```text
topo_semantic_evaluator.py
experiments/eval_topo_semantic_navigation.py
```

The new benchmark evaluates:

- top-1 semantic grounding accuracy,
- top-k semantic grounding accuracy,
- best semantic similarity,
- path success,
- graph path cost,
- path length in semantic nodes,
- blocked-edge handling.

## New benchmark

Run:

```bash
python contributions/17_topological_semantic_maps/experiments/eval_topo_semantic_navigation.py
```

Output:

```text
contributions/17_topological_semantic_maps/results/c17_topo_semantic_navigation.csv
```

The benchmark builds a demo semantic graph with:

- kitchen,
- corridor,
- robotics lab,
- office,
- exit,
- storage room.

It then evaluates planning before and after the corridor-to-lab transition becomes blocked.

## Reviewer-safe claim

A stronger claim after this upgrade is:

> Contribution 17 evaluates topological-semantic navigation through explicit semantic grounding accuracy and sparse graph planning success under blocked-transition changes.

## Relationship to other contributions

C17 connects directly to:

- C10 ethical zones as semantic map properties,
- C11 VLM navigation for semantic goal proposals,
- C19 LLM mission planning for language-to-place grounding,
- C20 failure explanation for human-readable route descriptions.

## Limitations

- The current embedding function is a deterministic stub, not real CLIP.
- The benchmark is small and synthetic.
- The graph does not yet include uncertainty over semantic labels.
- Real deployment requires semantic segmentation, place recognition, loop closure, and metric-topological alignment.

## Next research step

The strongest extension is uncertainty-aware semantic grounding:

```text
VLM / CLIP evidence -> semantic node belief -> topological planner with uncertain labels
```

This would connect C17 more tightly with C02 calibration, C11 VLM validation, and C19 LLM mission planning.
