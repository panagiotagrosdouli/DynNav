from benchmarks.dynamic_self_aware_astar.statistical_analysis import (
    bootstrap_ci,
    build_report,
    cohens_d,
    summarize,
)


def test_bootstrap_ci_contains_mean():
    low, high = bootstrap_ci([1.0, 2.0, 3.0, 4.0], n_bootstrap=200, confidence=0.95, seed=5)
    assert low <= 2.5 <= high


def test_cohens_d_is_positive_when_candidate_has_higher_success():
    baseline = [0.0, 0.0, 1.0, 0.0]
    candidate = [1.0, 1.0, 1.0, 1.0]
    assert cohens_d(baseline, candidate) > 0.0


def test_summarize_count_and_mean():
    stats = summarize([2.0, 4.0], n_bootstrap=100, confidence=0.95, seed=1)
    assert stats.n == 2
    assert stats.mean == 3.0


def test_build_report_mentions_dynamic_and_baseline():
    rows = [
        {
            "method": "static_self_aware_astar",
            "success_rate": "0.0",
            "collision_rate": "1.0",
            "path_length": "5",
            "replans": "0",
            "nodes_expanded": "10",
            "mean_risk": "0.5",
            "max_risk": "0.9",
            "recoverability": "0.1",
            "compute_time_ms": "1.0",
        },
        {
            "method": "dynamic_self_aware_astar",
            "success_rate": "1.0",
            "collision_rate": "0.0",
            "path_length": "7",
            "replans": "1",
            "nodes_expanded": "20",
            "mean_risk": "0.2",
            "max_risk": "0.4",
            "recoverability": "0.6",
            "compute_time_ms": "2.0",
        },
    ]
    report = build_report(rows, "static_self_aware_astar", n_bootstrap=50, confidence=0.95, seed=4)
    assert "Dynamic SelfAwareAStar Statistical Evaluation" in report
    assert "dynamic_self_aware_astar" in report
    assert "static_self_aware_astar" in report
    assert "Cohen" in report
