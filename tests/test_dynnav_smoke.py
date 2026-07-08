from pathlib import Path

import numpy as np

from dynnav.benchmarks import run_benchmark, write_csv, write_summary
from dynnav.config import DynNavConfig
from dynnav.core import GridMap, NavigationState, Pose, estimate_self_awareness
from dynnav.planning import RiskAwareAStar
from dynnav.scenarios import generate_scenario


def test_risk_aware_astar_finds_path_on_empty_grid() -> None:
    grid = GridMap(np.zeros((8, 8), dtype=float))
    start = Pose(1, 1)
    goal = Pose(6, 6)

    trajectory, metrics = RiskAwareAStar(max_expansions=500).plan(grid, start, goal)

    assert metrics.path_found
    assert trajectory.poses[0] == start
    assert trajectory.poses[-1] == goal
    assert trajectory.length > 1


def test_self_awareness_recommends_safe_stop_for_high_risk_state() -> None:
    state = NavigationState(
        pose=(0, 0),
        goal=(5, 5),
        localization_uncertainty=0.8,
        map_uncertainty=0.8,
        perception_confidence=0.2,
        planner_confidence=0.2,
        risk_estimate=0.95,
        recoverability=0.2,
    )

    score = estimate_self_awareness(state)

    assert score.recommended_mode == "SAFE_STOP"
    assert 0.0 <= score.trust <= 1.0


def test_benchmark_writes_outputs(tmp_path: Path) -> None:
    config = DynNavConfig(width=10, height=10, n_scenarios=2, max_expansions=500)

    rows = run_benchmark(config)
    csv_path = tmp_path / "bench.csv"
    summary_path = tmp_path / "summary.md"
    write_csv(rows, csv_path)
    write_summary(rows, summary_path)

    assert len(rows) == 2
    assert csv_path.exists()
    assert summary_path.exists()
    assert "DynNav Benchmark Summary" in summary_path.read_text(encoding="utf-8")


def test_scenario_generation_is_deterministic() -> None:
    first = generate_scenario(12, 12, 0.1, 0.2, seed=42)
    second = generate_scenario(12, 12, 0.1, 0.2, seed=42)

    assert first.start == second.start
    assert first.goal == second.goal
    assert np.array_equal(first.grid.occupancy, second.grid.occupancy)
