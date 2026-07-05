from pathlib import Path

from benchmarks.self_aware_astar.plot_randomized_results import (
    build_index,
    grouped_values,
    safe_filename,
    summarize,
)


def test_grouped_values_groups_metrics_by_method():
    rows = [
        {"method": "classic_astar", "mean_risk": "0.5"},
        {"method": "classic_astar", "mean_risk": "0.7"},
        {"method": "self_aware_full", "mean_risk": "0.2"},
    ]

    groups = grouped_values(rows, "mean_risk")

    assert groups["classic_astar"] == [0.5, 0.7]
    assert groups["self_aware_full"] == [0.2]


def test_summarize_returns_ordered_methods_means_and_errors():
    methods, means, errors = summarize({"b": [2.0, 4.0], "a": [1.0]})

    assert methods == ["a", "b"]
    assert means[0] == 1.0
    assert means[1] == 3.0
    assert errors[0] == 0.0
    assert errors[1] == 1.0


def test_safe_filename_uses_metric_name():
    assert safe_filename("mean_risk") == "mean_risk_comparison.png"


def test_build_index_lists_generated_figures():
    report = build_index(
        [("mean_risk", Path("results/figures/self_aware_astar/mean_risk_comparison.png"))],
        Path("results/figures/self_aware_astar"),
    )

    assert "SelfAwareAStar Figure Index" in report
    assert "mean_risk" in report
    assert "mean_risk_comparison.png" in report
