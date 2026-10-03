from __future__ import annotations

from dynnav.experiments.v4_belief_scaling import (
    run_belief_scaling_benchmark,
    scaling_world,
    summarize_belief_scaling,
)


def test_scaling_world_has_declared_number_of_hazards() -> None:
    grid, start, goal, safe, model = scaling_world(3)

    assert grid.width == 5
    assert start == (0, 0)
    assert goal == (4, 0)
    assert safe == {(0, 1)}
    assert len(model.closures) == 3


def test_exact_belief_support_doubles_with_each_uncertain_hazard() -> None:
    records = run_belief_scaling_benchmark(
        hazard_counts=(1, 2, 3),
        warmups=0,
        repetitions=1,
        per_call_budget_s=10.0,
    )

    assert [row.hazard_count for row in records] == [1, 2, 3]
    for row in records:
        assert row.success
        assert row.final_belief_support_size == 2**row.hazard_count
        assert row.final_belief_support_size == row.expected_support_size
        assert row.oracle_calls > 0
        assert row.nodes_expanded > 0


def test_scaling_benchmark_records_first_budget_boundary() -> None:
    records = run_belief_scaling_benchmark(
        hazard_counts=(1, 2, 4),
        warmups=0,
        repetitions=1,
        per_call_budget_s=1e-12,
    )
    summary = summarize_belief_scaling(records)

    assert len(records) == 1
    assert records[0].budget_exceeded
    assert summary["first_budget_exceeded_hazard_count"] == 1
