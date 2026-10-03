from __future__ import annotations

from dynnav.experiments.belief_route_mechanism import (
    BeliefRouteRegime,
    run_belief_route_development_benchmark,
    summarize_belief_route_records,
)


def test_medium_information_improves_availability_over_prior_but_not_for_free() -> None:
    regime = BeliefRouteRegime(
        name="medium_test",
        prior_arming_probability=0.7,
        sensitivity=0.85,
        specificity=0.85,
    )
    records = run_belief_route_development_benchmark(
        regimes=(regime,),
        seeds=tuple(range(500)),
    )
    summary = summarize_belief_route_records(records)[regime.name]

    assert summary["belief"]["mean_path_length"] < summary["prior_only"]["mean_path_length"]
    assert (
        summary["belief"]["return_infeasible_rate"]
        >= summary["prior_only"]["return_infeasible_rate"]
    )


def test_miss_heavy_belief_avoids_detector_as_truth_false_safe_route() -> None:
    regime = BeliefRouteRegime(
        name="miss_heavy_test",
        prior_arming_probability=0.7,
        sensitivity=0.70,
        specificity=0.95,
    )
    records = run_belief_route_development_benchmark(
        regimes=(regime,),
        seeds=tuple(range(500)),
    )
    summary = summarize_belief_route_records(records)[regime.name]

    assert (
        summary["belief"]["return_infeasible_rate"]
        < summary["detector_as_truth"]["return_infeasible_rate"]
    )
    assert summary["belief"]["mean_path_length"] > summary["detector_as_truth"]["mean_path_length"]
    assert summary["detector_as_truth"]["return_infeasible_rate"] > 0.05
