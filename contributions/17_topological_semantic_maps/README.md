# Contribution 17 — Topological Semantic Maps

[![Module](https://img.shields.io/badge/Module-17-purple)](.) [![Type](https://img.shields.io/badge/Type-Mapping%20%2F%20Grounding-blue)](.) [![Status](https://img.shields.io/badge/Status-Core%20Upgraded-brightgreen)](.)

## Plain-language summary

A robot does not always need to plan over every grid cell.

For long-horizon navigation, it can reason over meaningful places:

```text
kitchen → corridor → robotics lab → exit
```

Contribution 17 builds a sparse graph of semantic zones. Nodes represent named places such as rooms, corridors, exits, and labs. Edges represent traversable transitions such as doors, open passages, or narrow connections.

The upgraded version adds a benchmark for semantic grounding and route repair after a transition becomes blocked.

---

## Research Question

> **RQ17:** Does a topological-semantic representation reduce long-horizon planning complexity while supporting language-grounded navigation and dynamic route repair?

This contribution studies:

- semantic place graphs,
- sparse topological planning,
- open-vocabulary grounding,
- Dijkstra planning over semantic nodes,
- dynamic edge invalidation,
- route repair after blocked transitions.

---

## Conceptual Pipeline

```text
observations
      ↓
semantic zone detection
      ↓
node / edge graph update
      ↓
query grounding
      ↓
semantic graph planning
      ↓
metric waypoint execution
```

---

## Existing Components

The original C17 implementation includes:

- `SemanticNode`,
- `SemanticEdge`,
- `TopologicalSemanticMap`,
- node creation,
- edge creation,
- edge invalidation,
- embedding-based grounding,
- Dijkstra planning,
- serialization.

---

## New Upgrade Added

C17 now includes:

```text
topo_semantic_evaluator.py
```

This evaluator measures:

- semantic grounding top-1 accuracy,
- semantic grounding top-k accuracy,
- best semantic similarity,
- path success,
- path cost,
- number of semantic nodes in the route,
- blocked-edge handling.

---

## Files

```text
17_topological_semantic_maps/
├── README.md
├── topo_semantic_map.py
├── topo_semantic_evaluator.py
├── docs/
│   └── SCIENTIFIC_UPGRADE.md
├── experiments/
│   └── eval_topo_semantic_navigation.py
└── results/
    └── c17_topo_semantic_navigation.csv
```

---

## Quick Start

Run the topological-semantic benchmark:

```bash
python contributions/17_topological_semantic_maps/experiments/eval_topo_semantic_navigation.py
```

This generates:

```text
contributions/17_topological_semantic_maps/results/c17_topo_semantic_navigation.csv
```

---

## Benchmark

The benchmark builds a small semantic graph containing:

- kitchen,
- corridor,
- robotics lab,
- office,
- exit,
- storage room.

It evaluates:

1. whether semantic queries retrieve the correct node;
2. whether a path from kitchen to exit exists;
3. whether the graph can still route after the corridor-to-lab transition is blocked.

---

## Metrics

| Metric | Meaning |
|---|---|
| Top-1 grounding accuracy | Whether the highest-ranked semantic node is correct |
| Top-k grounding accuracy | Whether the correct node appears among the top results |
| Best similarity | Similarity of the best semantic match |
| Path found | Whether graph planning finds a valid route |
| Path cost | Total semantic traversal cost |
| Path length nodes | Number of semantic regions in the route |
| Blocked edges | Number of invalidated transitions |

---

## Scientific Contribution

The upgraded C17 contribution is not simply:

> Store semantic labels in a graph.

It is stronger:

> Evaluate whether semantic labels can be grounded to graph nodes and whether sparse topological planning can adapt when transitions become blocked.

This makes C17 a more testable semantic-navigation layer.

---

## Integration

- **Receives:** semantic goals from C11 VLM navigation
- **Receives:** natural-language missions from C19 LLM mission planner
- **Uses:** C10 ethical zones as semantic node or edge properties
- **Can explain:** route choices through C20 failure / decision explainer
- **Can guide:** C07 next-best-view exploration toward semantic frontiers

Recommended runtime interface:

```text
semantic_map_input = {
    observed_region_label,
    centroid_xy,
    semantic_embedding,
    edge_transition_type,
    blocked_transition_updates
}
```

---

## Limitations

- The current embedding function is a deterministic stub, not real CLIP.
- The benchmark is intentionally small and synthetic.
- Semantic label uncertainty is not yet modeled.
- Real deployment requires semantic segmentation, visual place recognition, loop closure, and metric-topological alignment.
- Dynamic graph repair is limited to edge invalidation and replanning.

---

## Next Research Step

The strongest extension is uncertainty-aware semantic grounding:

```text
VLM / CLIP evidence
      ↓
semantic node belief
      ↓
topological planner with uncertain labels
```

This would connect C17 to C02 calibration, C11 VLM validation, and C19 language planning.

---

## Conclusion

Contribution 17 establishes the topological-semantic mapping layer of DynNav.

The upgraded version adds measurable semantic grounding and blocked-transition planning evaluation, making the contribution more reproducible and research-ready.
