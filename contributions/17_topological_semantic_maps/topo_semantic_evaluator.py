"""Topological-semantic map evaluation utilities for Contribution 17.

This module evaluates the two main claims of a semantic-topological navigation
layer:

1. semantic grounding: natural-language-like queries should retrieve the correct
   region node;
2. graph planning: sparse semantic graphs should produce valid long-horizon
   routes and adapt when transitions become blocked.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from topo_semantic_map import TopologicalSemanticMap


@dataclass(frozen=True)
class SemanticEvalRow:
    query: str
    expected_label: str
    predicted_label: str
    top1_correct: bool
    topk_correct: bool
    best_similarity: float

    def to_dict(self) -> dict[str, str | bool | float]:
        return asdict(self)


@dataclass(frozen=True)
class PlanningEvalRow:
    scenario: str
    start_label: str
    goal_label: str
    path_found: bool
    path_length_nodes: int
    path_cost: float
    expanded_graph_nodes: int
    blocked_edges: int

    def to_dict(self) -> dict[str, str | bool | int | float]:
        return asdict(self)


def build_demo_semantic_map() -> TopologicalSemanticMap:
    m = TopologicalSemanticMap()
    kitchen = m.add_node("kitchen", (0.0, 0.0), embedding=m.embed_label_stub("kitchen"))
    corridor = m.add_node("corridor", (3.0, 0.0), embedding=m.embed_label_stub("corridor"))
    lab = m.add_node("robotics_lab", (6.0, 0.0), embedding=m.embed_label_stub("robotics_lab"))
    office = m.add_node("office", (3.0, 3.0), embedding=m.embed_label_stub("office"))
    exit_node = m.add_node("exit", (9.0, 0.0), embedding=m.embed_label_stub("exit"))
    storage = m.add_node("storage_room", (6.0, 3.0), embedding=m.embed_label_stub("storage_room"))

    m.add_edge(kitchen, corridor, weight=3.0, transition_type="door")
    m.add_edge(corridor, lab, weight=3.0, transition_type="open")
    m.add_edge(lab, exit_node, weight=3.0, transition_type="open")
    m.add_edge(corridor, office, weight=3.5, transition_type="narrow")
    m.add_edge(office, storage, weight=2.5, transition_type="door")
    m.add_edge(storage, lab, weight=2.0, transition_type="door")
    return m


def evaluate_grounding(
    topo_map: TopologicalSemanticMap,
    queries: list[tuple[str, str]],
    top_k: int = 3,
) -> list[SemanticEvalRow]:
    rows: list[SemanticEvalRow] = []
    for query, expected in queries:
        emb = topo_map.embed_label_stub(query)
        results = topo_map.ground_query(emb, top_k=top_k)
        predicted = results[0][1] if results else "none"
        labels = [label for _, label, _ in results]
        best_sim = float(results[0][2]) if results else 0.0
        rows.append(
            SemanticEvalRow(
                query=query,
                expected_label=expected,
                predicted_label=predicted,
                top1_correct=predicted == expected,
                topk_correct=expected in labels,
                best_similarity=best_sim,
            )
        )
    return rows


def _find_node_by_label(topo_map: TopologicalSemanticMap, label: str) -> int:
    for nid, node in topo_map.nodes.items():
        if node.label == label:
            return nid
    raise ValueError(f"No node with label {label}")


def evaluate_planning(
    topo_map: TopologicalSemanticMap,
    scenario: str,
    start_label: str,
    goal_label: str,
) -> PlanningEvalRow:
    start = _find_node_by_label(topo_map, start_label)
    goal = _find_node_by_label(topo_map, goal_label)
    path, cost = topo_map.plan(start, goal)
    return PlanningEvalRow(
        scenario=scenario,
        start_label=start_label,
        goal_label=goal_label,
        path_found=bool(path),
        path_length_nodes=len(path),
        path_cost=float(cost),
        expanded_graph_nodes=len(topo_map.nodes),
        blocked_edges=sum(1 for e in topo_map.edges if not e.passable),
    )


def summarize_semantic_rows(rows: list[SemanticEvalRow]) -> dict[str, float | int]:
    if not rows:
        raise ValueError("rows must not be empty")
    return {
        "n_queries": len(rows),
        "top1_accuracy": sum(r.top1_correct for r in rows) / len(rows),
        "topk_accuracy": sum(r.topk_correct for r in rows) / len(rows),
        "mean_best_similarity": float(np.mean([r.best_similarity for r in rows])),
    }
