from benchmarks.self_aware_astar.randomized_ablation_benchmark import (
    aggregate,
    run_benchmark,
)


def test_randomized_ablation_benchmark_smoke_run():
    rows = run_benchmark(n_seeds=3)
    summary = aggregate(rows)

    assert rows
    assert "classic_astar" in summary
    assert "self_aware_full" in summary
    assert "ablation_no_risk" in summary
    assert len(rows) == 3 * 5

    for row in rows:
        assert row["module_id"] == "C27"
        assert 0.0 <= float(row["success_rate"]) <= 1.0
        assert 0.0 <= float(row["mean_risk"]) <= 1.0
        assert 0.0 <= float(row["max_risk"]) <= 1.0
        assert 0.0 <= float(row["recoverability"]) <= 1.0
