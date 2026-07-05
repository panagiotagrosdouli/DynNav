from benchmarks.dynamic_self_aware_astar.randomized_dynamic_benchmark import aggregate, run_benchmark


def test_dynamic_randomized_benchmark_smoke_run():
    rows = run_benchmark(n_seeds=2, max_steps=64)
    summary = aggregate(rows)

    assert len(rows) == 4
    assert "static_self_aware_astar" in summary
    assert "dynamic_self_aware_astar" in summary

    for row in rows:
        assert row["module_id"] == "C28"
        assert 0.0 <= float(row["success_rate"]) <= 1.0
        assert 0.0 <= float(row["mean_risk"]) <= 1.0
        assert 0.0 <= float(row["recoverability"]) <= 1.0
