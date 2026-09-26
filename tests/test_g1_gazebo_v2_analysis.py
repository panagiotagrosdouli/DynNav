from __future__ import annotations

from dynnav.evaluation.g1_gazebo_v2_analysis import analyze_g1_gazebo_v2


def _row(dependence, repetition, planner, both, failure, time_s):
    return {
        "dependence": dependence,
        "repetition": repetition,
        "planner_id": planner,
        "valid_trial": True,
        "hazards": [
            {"trigger_observed": both},
            {"trigger_observed": both},
        ],
        "operational_irreversible_failure": failure,
        "navigation_success": not failure,
        "navigation_time_s": time_s,
    }


def test_g1_analysis_is_paired_by_dependence_and_repetition() -> None:
    trials = []
    for dependence in ("independent", "common_cause", "anti_correlated"):
        for repetition in range(4):
            trials.extend(
                [
                    _row(dependence, repetition, "DynNavShortest", True, repetition == 0, 10.0),
                    _row(dependence, repetition, "DynNavHistory", True, repetition == 0, 11.0),
                    _row(dependence, repetition, "DynNavRobustHistory", False, False, 20.0),
                ]
            )
    summary = analyze_g1_gazebo_v2(
        {
            "schema_version": 1,
            "benchmark_type": "correlated_action_triggered_history",
            "trials": trials,
        },
        bootstrap_resamples=200,
        seed=1,
    )
    effect = summary["conditions"]["common_cause"]["paired_effects"][
        "DynNavRobustHistory_vs_DynNavHistory"
    ]
    assert effect["paired_valid_trials"] == 4
    assert effect["both_trigger_exposure"]["risk_difference"] == -1.0
    assert effect["irreversible_failure"]["risk_difference"] == -0.25
    assert effect["navigation_time"]["mean_difference"] == 9.0
