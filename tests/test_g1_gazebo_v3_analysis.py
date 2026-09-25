from __future__ import annotations

from dynnav.evaluation.g1_gazebo_v2_analysis import analyze_g1_gazebo_v2


def _row(
    dependence: str,
    planner: str,
    *,
    valid: bool = True,
    invalid_reason: str | None = None,
) -> dict[str, object]:
    robust = planner == "DynNavRobustHistory"
    return {
        "dependence": dependence,
        "repetition": 0,
        "planner_id": planner,
        "valid_trial": valid,
        "invalid_reason": invalid_reason,
        "navigation_success": valid,
        "navigation_time_s": 10.0 if valid else 12.0,
        "operational_irreversible_failure": False,
        "hazards": [
            {"trigger_observed": not robust},
            {"trigger_observed": not robust},
        ],
        "initial_plan": {
            "success": True,
            "path_length_m": 11.5 if robust else 5.4,
            "route_class": "lower_detour" if robust else "upper_direct",
            "trigger_gate_crossings": [False, False] if robust else [True, True],
        },
    }


def test_v3_analysis_separates_planning_validity_and_paired_efficacy() -> None:
    planners = ("DynNavShortest", "DynNavHistory", "DynNavRobustHistory")
    conditions = ("independent", "common_cause", "anti_correlated")
    trials = [
        _row(condition, planner)
        for condition in conditions
        for planner in planners
    ]

    # Keep an invalid execution trial in the denominator rather than replacing it.
    trials.append(
        {
            **_row("independent", "DynNavShortest", valid=False),
            "repetition": 1,
            "invalid_reason": "localization_jump",
        }
    )
    # Remove the only valid anti-correlated Robust execution pair while preserving
    # the successful pre-execution planner audit.
    for row in trials:
        if (
            row["dependence"] == "anti_correlated"
            and row["planner_id"] == "DynNavRobustHistory"
            and row["repetition"] == 0
        ):
            row["valid_trial"] = False
            row["invalid_reason"] = "controller_failure"

    result = analyze_g1_gazebo_v2(
        {
            "schema_version": 1,
            "benchmark_type": "correlated_action_triggered_history",
            "trials": trials,
        },
        bootstrap_resamples=100,
        seed=9,
    )

    shortest = result["conditions"]["independent"]["descriptive"]["DynNavShortest"]
    assert shortest["total_trials"] == 2
    assert shortest["valid_trials"] == 1
    assert shortest["valid_trial_rate"] == 0.5
    assert shortest["invalid_reasons"] == {"localization_jump": 1}
    assert shortest["initial_plan"]["route_classes"] == ["upper_direct"]
    assert shortest["initial_plan"]["trigger_gate_crossing_patterns"] == [
        [True, True]
    ]

    robust = result["conditions"]["anti_correlated"]["descriptive"][
        "DynNavRobustHistory"
    ]
    assert robust["total_trials"] == 1
    assert robust["valid_trials"] == 0
    assert robust["invalid_reasons"] == {"controller_failure": 1}
    assert robust["initial_plan"]["route_classes"] == ["lower_detour"]

    paired = result["conditions"]["anti_correlated"]["paired_effects"][
        "DynNavRobustHistory_vs_DynNavHistory"
    ]
    assert paired["paired_valid_trials"] == 0
    assert paired["both_trigger_exposure"] is None
    assert paired["irreversible_failure"] is None
    assert paired["navigation_time"] is None
