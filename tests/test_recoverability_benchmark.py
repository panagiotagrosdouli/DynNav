from dynnav.experiments.recoverability_benchmark import evaluate_dynamic_invalidation, run_benchmark
from dynnav.planners.grid_map import GridMap
from dynnav.planners.recoverability_astar import PlannerMode, RecoverabilityAStarConfig


def test_benchmark_emits_all_modes_for_each_seed(tmp_path):
    output = tmp_path / "recoverability.csv"
    records = run_benchmark(range(3), output)

    assert len(records) == 3 * len(PlannerMode)
    assert output.exists()
    assert {record.mode for record in records} == {mode.value for mode in PlannerMode}


def test_benchmark_metrics_are_normalized_and_auditable():
    records = run_benchmark([0])

    for record in records:
        assert record.geometric_length >= 0
        assert record.path_length_overhead >= 0.0
        assert record.cumulative_risk >= 0.0
        assert record.cumulative_irreversibility >= 0.0
        assert record.minimum_escape_options >= 0
        assert record.nodes_expanded >= 0
        assert record.planning_time_ms >= 0.0


def test_blocked_goal_route_is_not_irreversible_when_safe_return_exists():
    grid = GridMap.from_obstacles(5, 1)
    success, irreversible_failure, initial = evaluate_dynamic_invalidation(
        grid,
        start=(0, 0),
        goal=(4, 0),
        invalidated_cell=(3, 0),
        mode=PlannerMode.SHORTEST,
        config=RecoverabilityAStarConfig(),
    )

    assert initial.success
    assert not success
    assert not irreversible_failure
