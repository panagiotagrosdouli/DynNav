"""Topological-semantic navigation benchmark for Contribution 17.

This benchmark evaluates semantic grounding and sparse graph planning before and
after a transition becomes blocked.

Run from the repository root:

    python contributions/17_topological_semantic_maps/experiments/eval_topo_semantic_navigation.py

Output:

    contributions/17_topological_semantic_maps/results/c17_topo_semantic_navigation.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[1]
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

from topo_semantic_evaluator import (  # noqa: E402
    build_demo_semantic_map,
    evaluate_grounding,
    evaluate_planning,
    summarize_semantic_rows,
)

RESULTS_DIR = Path("contributions/17_topological_semantic_maps/results")
DEFAULT_OUT = RESULTS_DIR / "c17_topo_semantic_navigation.csv"


def write_csv(path: Path, rows: list[dict[str, str | bool | int | float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="C17 topological-semantic benchmark.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    topo_map = build_demo_semantic_map()
    grounding_queries = [
        ("kitchen", "kitchen"),
        ("corridor", "corridor"),
        ("robotics_lab", "robotics_lab"),
        ("office", "office"),
        ("exit", "exit"),
        ("storage_room", "storage_room"),
    ]
    grounding_rows = evaluate_grounding(topo_map, grounding_queries)
    grounding_summary = summarize_semantic_rows(grounding_rows)

    planning_rows = [
        evaluate_planning(topo_map, "nominal", "kitchen", "exit"),
    ]
    corridor = next(nid for nid, node in topo_map.nodes.items() if node.label == "corridor")
    lab = next(nid for nid, node in topo_map.nodes.items() if node.label == "robotics_lab")
    topo_map.invalidate_edge(corridor, lab)
    topo_map.invalidate_edge(lab, corridor)
    planning_rows.append(evaluate_planning(topo_map, "blocked_corridor_lab", "kitchen", "exit"))

    rows: list[dict[str, str | bool | int | float]] = []
    for row in grounding_rows:
        rows.append({"row_type": "grounding", **row.to_dict(), "scenario": "semantic_query"})
    for row in planning_rows:
        rows.append({"row_type": "planning", **row.to_dict(), "query": "", "expected_label": "", "predicted_label": "", "top1_correct": False, "topk_correct": False, "best_similarity": 0.0})

    write_csv(args.out, rows)
    print(f"Saved C17 topological-semantic benchmark to {args.out}")
    print(
        f"grounding_top1={float(grounding_summary['top1_accuracy']):.3f}, "
        f"grounding_topk={float(grounding_summary['topk_accuracy']):.3f}"
    )
    for row in planning_rows:
        print(
            f"{row.scenario:<22} found={row.path_found} cost={row.path_cost:.2f} "
            f"nodes={row.path_length_nodes} blocked={row.blocked_edges}"
        )


if __name__ == "__main__":
    main()
