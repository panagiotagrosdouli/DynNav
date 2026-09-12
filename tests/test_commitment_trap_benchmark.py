from __future__ import annotations

import json

import pytest

from dynnav.experiments.commitment_trap_benchmark import (
    commitment_trap_world,
    run_commitment_trap_benchmark,
    write_commitment_trap_artifacts,
)
from dynnav.planners.hazard_reliability_astar import (
    HazardReliabilityAStarConfig,
    HazardReliabilityMode,
    hazard_reliability_astar,
)
from dynnav.planners.recoverability_astar import PlannerMode, recoverability_astar
from dynnav.recoverability_belief import exact_safe_return_probability


def test_shortest_route_enters_fragile_commitment_region() -> None:
    grid, start, goal, safe, hazard = commitment_trap_world(0.5)
    shortest = recoverability_astar(grid, start, goal, safe_cells=safe, mode=PlannerMode.SHORTEST)

    assert shortest.success
    assert shortest.geometric_length == 8
    assert (4, 1) in shortest.path
    exact = [
        exact_safe_return_probability(grid, cell, safe, hazard, max_hazard_cells=2)
        for cell in shortest.path
    ]
    assert min(exact) == pytest.approx(0.75)


def test_high_hazard_penalty_selects_long_hazard_free_corridor() -> None:
    grid, start, goal, safe, hazard = commitment_trap_world(0.9)

    for mode in (HazardReliabilityMode.SINGLE_RETURN, HazardReliabilityMode.REDUNDANT_RETURN):
        result = hazard_reliability_astar(
            grid,
            start,
            goal,
            safe_cells=safe,
            hazard=hazard,
            mode=mode,
            config=HazardReliabilityAStarConfig(reliability_weight=8.0),
        )
        assert result.success
        assert result.geometric_length == 16
        assert (4, 1) not in result.path
        exact = [
            exact_safe_return_probability(grid, cell, safe, hazard, max_hazard_cells=2)
            for cell in result.path
        ]
        assert min(exact) == pytest.approx(1.0)


def test_benchmark_spans_hazard_and_weight_regimes() -> None:
    records = run_commitment_trap_benchmark(
        closure_probabilities=(0.1, 0.9),
        reliability_weights=(1.0, 8.0),
    )

    assert len(records) == 2 * (2 + 2 * 2)
    shortest = [row for row in records if row.planner == "shortest"]
    assert all(row.geometric_length == 8 for row in shortest)
    assert all(row.uses_fragile_corridor for row in shortest)
    robust = [
        row
        for row in records
        if row.closure_probability == 0.9
        and row.reliability_weight == 8.0
        and row.planner in {"single_return", "redundant_return"}
    ]
    assert all(not row.uses_fragile_corridor for row in robust)
    assert all(row.minimum_exact_return_probability == pytest.approx(1.0) for row in robust)


def test_commitment_trap_writes_raw_artifacts(tmp_path) -> None:
    records = run_commitment_trap_benchmark(
        closure_probabilities=(0.5,),
        reliability_weights=(4.0,),
    )
    write_commitment_trap_artifacts(records, tmp_path)

    assert (tmp_path / "trials.csv").exists()
    payload = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert "shortest" in payload
    assert "structural" in payload
