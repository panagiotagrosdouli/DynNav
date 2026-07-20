"""Regression tests for randomized topology generation and paired execution."""

from __future__ import annotations

import numpy as np

from random_benchmark import PLANNERS, run_experiment, run_trial
from topology_families import TopologyConfig, available_families, generate_topology


def test_generators_are_reproducible() -> None:
    for family in available_families():
        config = TopologyConfig(family=family)
        first = generate_topology(7, config)
        second = generate_topology(7, config)
        assert np.array_equal(first.grid, second.grid)
        assert np.array_equal(first.risk, second.risk)
        assert first.closure == second.closure


def test_all_families_preserve_two_valid_routes() -> None:
    for family in available_families():
        scenario = generate_topology(3, TopologyConfig(family=family))
        for route in (scenario.fragile_route, scenario.resilient_route):
            assert route[0] == scenario.start
            assert route[-1] == scenario.goal
            assert all(scenario.grid[y, x] == 0 for x, y in route)
        assert scenario.closure in scenario.fragile_route
        assert scenario.closure not in scenario.resilient_route


def test_trial_is_paired_across_all_planners() -> None:
    rows = run_trial("bottleneck", 5)
    assert {row["planner"] for row in rows} == set(PLANNERS)
    assert {row["seed"] for row in rows} == {5}
    assert {row["family"] for row in rows} == {"bottleneck"}


def test_experiment_row_count() -> None:
    families = ("open", "bottleneck")
    rows = run_experiment(families, seeds=4)
    assert len(rows) == len(families) * 4 * len(PLANNERS)
