from __future__ import annotations

from dynnav.evaluation.g1_gazebo_v2_analysis import analyze_g1_gazebo_v2


def _trial(
    *,
    dependence: str,
    repetition: int,
    planner: str,
    both_triggers: bool,
    recovery_feasible: bool,
    navigation_time_s: float,
) -> dict[str, object]:
    hazards = [
        {"trigger_observed": both_triggers},
        {"trigger_observed": both_triggers},
    ]
    return {
        "dependence": dependence,
        "repetition": repetition,
        "planner_id": planner,
        "valid_trial": True,
        "invalid_reason": None,
        "hazards": hazards,
        "recovery_feasible": recovery_feasible,
        "operational_irreversible_failure": False,
        "navigation_success": True,
        "navigation_time_s": navigation_time_s,
        "initial_plan": {
            "success": True,
            "path_length_m": 5.0 if planner != "DynNavRobustHistory" else 10.0,
            "route_class": "upper_direct"
            if planner != "DynNavRobustHistory"
            else "lower_detour",
            "trigger_gate_crossings": [both_triggers, both_triggers],
        },
    }


def test_g1_analysis_reports_return_infeasibility_separately() -> None:
    trials = []
    for repetition in range(4):
        for planner in ("DynNavShortest", "DynNavHistory", "DynNavRobustHistory"):
            trials.append(
                _trial(
                    dependence="common_cause",
                    repetition=repetition,
                    planner=planner,
                    both_triggers=planner != "DynNavRobustHistory",
                    recovery_feasible=(
                        planner == "DynNavRobustHistory" or repetition == 0
                    ),
                    navigation_time_s=10.0 if planner != "DynNavRobustHistory" else 30.0,
                )
            )

    data = {
        "schema_version": 1,
        "benchmark_type": "correlated_action_triggered_history",
        "trials": trials,
    }
    result = analyze_g1_gazebo_v2(
        data,
        bootstrap_resamples=1000,
        seed=7,
    )
    condition = result["conditions"]["common_cause"]

    assert condition["descriptive"]["DynNavHistory"]["return_infeasibility_rate"] == 0.75
    assert condition["descriptive"]["DynNavRobustHistory"]["return_infeasibility_rate"] == 0.0

    effect = condition["paired_effects"][
        "DynNavRobustHistory_vs_DynNavHistory"
    ]["return_infeasibility"]
    assert effect["baseline_rate"] == 0.75
    assert effect["proposed_rate"] == 0.0
    assert effect["risk_difference"] == -0.75
    assert effect["baseline_only_events"] == 3
    assert effect["proposed_only_events"] == 0
