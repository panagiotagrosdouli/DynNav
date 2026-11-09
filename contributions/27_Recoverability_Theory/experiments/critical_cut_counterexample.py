"""Exhaustively check a multi-vertex-cut counterexample to a single-cut proxy.

This is a small numerical model check of one proposed C27 bound failure mode.
It is not a proof of a general result and does not register C27 as validated.
"""
from __future__ import annotations

import argparse
import json
import sys
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dynnav.planners.grid_map import GridCell, GridMap  # noqa: E402
from dynnav.recoverability_belief import (  # noqa: E402
    TopologyHazardBelief,
    exact_safe_return_probability,
)
from dynnav.recoverability_cut import critical_return_cut_upper_bound  # noqa: E402


def reachable(grid: GridMap, start: GridCell, goal: GridCell) -> bool:
    pending = [start]
    visited = {start}
    while pending:
        current = pending.pop()
        if current == goal:
            return True
        for nxt in grid.neighbors4(current):
            if nxt not in visited:
                visited.add(nxt)
                pending.append(nxt)
    return False


def run() -> dict[str, object]:
    # Two disjoint two-cell corridors connect start to the safe goal.
    # Removing any one hazard leaves another path, but closures can jointly
    # disconnect both corridors.
    base = GridMap.from_obstacles(
        width=5,
        height=3,
        obstacles={(1, 1), (2, 1), (3, 1)},
    )
    start, safe = (0, 1), {(4, 1)}
    hazards = {
        (1, 0): 0.5,
        (2, 0): 0.5,
        (1, 2): 0.5,
        (2, 2): 0.5,
    }

    # Independently enumerate every realization as a reference calculation.
    cells = sorted(hazards)
    direct_probability = 0.0
    for closed in product((False, True), repeat=len(cells)):
        weight = 1.0
        obstacles = set(base.obstacles)
        for cell, is_closed in zip(cells, closed, strict=True):
            p = hazards[cell]
            weight *= p if is_closed else 1.0 - p
            if is_closed:
                obstacles.add(cell)
        realized = GridMap.from_obstacles(5, 3, obstacles)
        if reachable(realized, start, next(iter(safe))):
            direct_probability += weight

    belief = TopologyHazardBelief(hazards)
    oracle_probability = exact_safe_return_probability(base, start, safe, belief)
    estimate = critical_return_cut_upper_bound(base, start, safe, belief)
    expected = 0.4375
    assert abs(direct_probability - expected) < 1e-12
    assert abs(oracle_probability - direct_probability) < 1e-12
    assert estimate.critical_hazard_cells == ()
    assert estimate.probability_upper_bound == 1.0
    assert oracle_probability <= estimate.probability_upper_bound
    return {
        "evidence_level": "exhaustive finite synthetic model check",
        "realizations_enumerated": 2 ** len(cells),
        "independent_reference_return_probability": direct_probability,
        "dynnav_exact_oracle_probability": oracle_probability,
        "single_vertex_critical_cut_upper_bound": estimate.probability_upper_bound,
        "critical_hazard_cells": [list(cell) for cell in estimate.critical_hazard_cells],
        "result": "counterexample_confirmed_bound_is_optimistic_for_joint_cutsets",
        "claim_boundary": "One finite counterexample; not a general proof or independent C27 validation.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = run()
    payload = json.dumps(result, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
