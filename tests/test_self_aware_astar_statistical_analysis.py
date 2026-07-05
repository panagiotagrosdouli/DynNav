from benchmarks.self_aware_astar.statistical_analysis import (
    bootstrap_ci,
    build_report,
    cohens_d,
    summarize,
)


def test_bootstrap_ci_contains_mean_for_simple_values():
    values = [1.0, 2.0, 3.0, 4.0]
    low, high = bootstrap_ci(values, n_bootstrap=200, confidence=0.95, seed=7)

    assert low <= 2.5 <= high


def test_cohens_d_sign_matches_candidate_improvement_for_lower_risk():
    baseline = [0.5, 0.6, 0.7]
    candidate = [0.2, 0.3, 0.4]

    assert cohens_d(baseline, candidate) < 0.0


def test_summarize_reports_expected_count():
    stats = summarize([1.0, 2.0, 3.0], n_bootstrap=100, confidence=0.95, seed=3)

    assert stats.n == 3
    assert stats.mean == 2.0
    assert stats.ci_low <= stats.mean <= stats.ci_high


def test_build_report_contains_methods_and_metrics():
    rows = [
        {
            "method": "classic_astar",
            "success_rate": "1.0",
            "collision_rate": "0.5",
            "path_length": "10",
            "nodes_expanded": "20",
            "mean_risk": "0.5",
            "max_risk": "0.8",
            "information_gain": "0.2",
            "recoverability": "0.2",
            "compute_time_ms": "1.0",
        },
        {
            "method": "self_aware_full",
            "success_rate": "1.0",
            "collision_rate": "0.0",
            "path_length": "12",
            "nodes_expanded": "25",
            "mean_risk": "0.2",
            "max_risk": "0.4",
            "information_gain": "0.5",
            "recoverability": "0.6",
            "compute_time_ms": "1.5",
        },
    ]

    report = build_report(rows, n_bootstrap=50, confidence=0.95, baseline="classic_astar", seed=11)

    assert "SelfAwareAStar Statistical Evaluation" in report
    assert "classic_astar" in report
    assert "self_aware_full" in report
    assert "mean_risk" in report
    assert "Cohen" in report
