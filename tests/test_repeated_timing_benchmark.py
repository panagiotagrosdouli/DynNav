from __future__ import annotations

from dynnav.experiments.repeated_timing_benchmark import (
    run_repeated_timing_benchmark,
    summarize_repeated_timings,
)


def test_repeated_timing_records_distributions_and_stable_outputs() -> None:
    records = run_repeated_timing_benchmark(
        repetitions=3,
        warmups=1,
        oracle_hazard_count=4,
        planner_modules=2,
    )
    summary = summarize_repeated_timings(records)

    assert summary["oracle_h4"]["exact"]["n"] == 3
    assert summary["oracle_h4"]["critical_cut"]["n"] == 3
    assert summary["planner_m2"]["history_exact"]["n"] == 3
    assert summary["planner_m2"]["history_cut"]["n"] == 3
    assert summary["planner_m2"]["shortest_augmented"]["n"] == 3
    assert summary["oracle_h4"]["median_speedup_exact_over_cut"] > 0.0

    for benchmark in summary.values():
        if not isinstance(benchmark, dict):
            continue
        for value in benchmark.values():
            if not isinstance(value, dict) or "n" not in value:
                continue
            assert value["median_ms"] >= 0.0
            assert value["q1_ms"] <= value["q3_ms"]
            assert value["p95_ms"] >= value["median_ms"]
