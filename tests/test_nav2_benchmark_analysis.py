from __future__ import annotations

import sys
from pathlib import Path
from xml.etree import ElementTree

import pytest

REPOSITORY = Path(__file__).resolve().parents[1]
ROS_PACKAGE = REPOSITORY / "ros2_ws" / "src" / "dynnav_nav2_benchmark"
sys.path.insert(0, str(ROS_PACKAGE))

from dynnav_nav2_benchmark.analysis import (  # noqa: E402
    Pose2D,
    TrialRecord,
    balanced_trial_order,
    load_suite,
    path_length,
    resolve_map_image,
    summarize_trials,
    summarize_trials_by_scenario,
)
from dynnav_nav2_benchmark.configuration import (  # noqa: E402
    PLANNER_IDS,
    inject_planner_parameters,
    planner_parameter_overrides,
)
from dynnav_nav2_benchmark.dynamic_analysis import (  # noqa: E402
    BoxSize,
    Pose3D,
    SafeRegion,
    assess_recovery_reachability,
    count_costs_in_oriented_box,
    load_dynamic_suite,
    maximum_cost_near,
    planner_behavior_tree,
    path_intersects_oriented_box,
    summarize_dynamic_trials,
    terminal_failure_class,
)


def test_benchmark_suite_is_valid_and_has_complete_ablation() -> None:
    suite = load_suite(ROS_PACKAGE / "config" / "sandbox_static_queries.yaml")
    ids = tuple(planner.planner_id for planner in suite.planners)
    assert PLANNER_IDS == ids
    assert set(ids) == set(planner_parameter_overrides())
    assert len(suite.scenarios) == 2


def test_declared_ablation_weights_match_runtime_configuration() -> None:
    suite = load_suite(ROS_PACKAGE / "config" / "sandbox_static_queries.yaml")
    configured = planner_parameter_overrides()
    for planner in suite.planners:
        if planner.family != "dynnav_ablation":
            continue
        assert configured[planner.planner_id]["risk_weight"] == planner.risk_weight
        assert (
            configured[planner.planner_id]["irreversibility_weight"]
            == planner.irreversibility_weight
        )


def test_all_turtlebot_configs_use_registered_plugin_type() -> None:
    configs = [
        REPOSITORY / "ros2_ws/src/dynnav_bringup/config/dynnav_nav2_params.yaml",
        REPOSITORY / "ros2_ws/src/dynnav_turtlebot3/config/nav2_dynnav_params.yaml",
        REPOSITORY / "ros2_ws/src/dynnav_turtlebot3/config/turtlebot3_dynnav_nav2.yaml",
    ]
    for path in configs:
        text = path.read_text(encoding="utf-8")
        assert "dynnav_nav2_cpp::DynNavGlobalPlanner" in text
        assert "dynnav_nav2_cpp/DynNavPlanner" not in text


def test_parameter_injection_is_non_mutating_and_removes_default_plugin() -> None:
    source = {
        "planner_server": {
            "ros__parameters": {
                "expected_planner_frequency": 20.0,
                "planner_plugins": ["GridBased"],
                "GridBased": {"plugin": "old"},
            }
        }
    }
    merged = inject_planner_parameters(source)
    assert source["planner_server"]["ros__parameters"]["planner_plugins"] == [
        "GridBased"
    ]
    parameters = merged["planner_server"]["ros__parameters"]
    assert parameters["planner_plugins"] == list(PLANNER_IDS)
    assert "GridBased" not in parameters
    assert parameters["expected_planner_frequency"] == 20.0


def test_trial_order_is_deterministic_and_complete() -> None:
    planners = ("a", "b", "c", "d")
    first = balanced_trial_order(planners, repetitions=8, seed=7)
    second = balanced_trial_order(planners, repetitions=8, seed=7)
    assert first == second
    assert all(set(block) == set(planners) for block in first)
    assert len(set(first)) > 1
    for planner in planners:
        position_counts = [
            sum(block[position] == planner for block in first)
            for position in range(len(planners))
        ]
        assert max(position_counts) - min(position_counts) <= 1


def test_path_length_uses_metric_polyline_distance() -> None:
    assert path_length([(0.0, 0.0), (3.0, 4.0), (6.0, 4.0)]) == pytest.approx(8.0)


def test_summary_retains_failures_and_uses_successful_lengths() -> None:
    records = [
        TrialRecord("s", "p", 0, 0, True, 10.0, 5.0, 2, 0.0, ((0.0, 0.0), (3.0, 4.0))),
        TrialRecord("s", "p", 1, 0, False, 30.0, None, 0, None, (), "no path"),
    ]
    summary = summarize_trials(records)["p"]
    assert summary["trials"] == 2
    assert summary["failures"] == 1
    assert summary["success_rate"] == 0.5
    assert summary["planning_latency_ms_mean"] == 20.0
    assert summary["planning_latency_ms_p95"] == pytest.approx(29.0)
    assert summary["path_length_m_mean"] == 5.0


def test_summary_is_stratified_by_scenario() -> None:
    records = [
        TrialRecord("easy", "p", 0, 0, True, 1.0, 2.0, 2, 0.0, ()),
        TrialRecord("hard", "p", 0, 0, False, 9.0, None, 0, None, (), "no path"),
    ]
    summary = summarize_trials_by_scenario(records)
    assert summary["easy"]["p"]["success_rate"] == 1.0
    assert summary["hard"]["p"]["success_rate"] == 0.0


def test_map_image_is_resolved_relative_to_yaml(tmp_path: Path) -> None:
    image = tmp_path / "map.pgm"
    image.write_bytes(b"P5\n1 1\n255\n\xff")
    map_yaml = tmp_path / "map.yaml"
    map_yaml.write_text("image: map.pgm\nresolution: 0.05\n", encoding="utf-8")
    assert resolve_map_image(map_yaml) == image


def test_dynamic_suite_is_frozen_and_matches_runtime_plugins() -> None:
    suite = load_dynamic_suite(
        ROS_PACKAGE / "config" / "sandbox_dynamic_events.yaml"
    )
    assert tuple(planner.planner_id for planner in suite.planners) == (
        "NavFn",
        "Smac2D",
        "DynNavShortest",
        "DynNavRisk",
        "DynNavRecoverability",
        "DynNavJoint",
    )
    assert set(planner.planner_id for planner in suite.planners) <= set(PLANNER_IDS)
    configured = planner_parameter_overrides()
    for planner in suite.planners:
        if planner.family == "dynnav_ablation":
            assert configured[planner.planner_id]["risk_weight"] == planner.risk_weight
            assert (
                configured[planner.planner_id]["irreversibility_weight"]
                == planner.irreversibility_weight
            )
    assert {scenario.name for scenario in suite.scenarios} == {
        "return_gate_closure",
        "forward_closure_negative_control",
    }
    requirements = {
        scenario.name: scenario.event.require_forward_path_invalidation
        for scenario in suite.scenarios
    }
    assert requirements == {
        "return_gate_closure": False,
        "forward_closure_negative_control": True,
    }
    model = ElementTree.parse(ROS_PACKAGE / "models" / "dynamic_blocker.sdf")
    size_text = model.findtext(".//collision/geometry/box/size")
    assert size_text is not None
    assert tuple(float(value) for value in size_text.split()) == (
        suite.blocker_size.x,
        suite.blocker_size.y,
        suite.blocker_size.z,
    )


def test_recovery_oracle_detects_reachable_blocked_and_over_budget() -> None:
    safe = SafeRegion(center=Pose2D(4.5, 2.5), radius_m=0.49)
    open_costs = [0] * 25
    reachable = assess_recovery_reachability(
        costs=open_costs,
        width=5,
        height=5,
        resolution=1.0,
        origin_x=0.0,
        origin_y=0.0,
        start=Pose2D(0.5, 2.5),
        safe_region=safe,
        budget_m=5.0,
    )
    assert reachable.reachable
    assert reachable.within_budget
    assert reachable.path_length_m == pytest.approx(4.0)

    over_budget = assess_recovery_reachability(
        costs=open_costs,
        width=5,
        height=5,
        resolution=1.0,
        origin_x=0.0,
        origin_y=0.0,
        start=Pose2D(0.5, 2.5),
        safe_region=safe,
        budget_m=3.0,
    )
    assert over_budget.reachable
    assert not over_budget.within_budget

    wall = open_costs.copy()
    for y in range(5):
        wall[y * 5 + 2] = 254
    blocked = assess_recovery_reachability(
        costs=wall,
        width=5,
        height=5,
        resolution=1.0,
        origin_x=0.0,
        origin_y=0.0,
        start=Pose2D(0.5, 2.5),
        safe_region=safe,
        budget_m=10.0,
    )
    assert not blocked.reachable
    assert blocked.reason == "no_recovery_path"


def test_obstacle_observation_and_terminal_classes() -> None:
    costs = [0] * 25
    costs[2 * 5 + 2] = 254
    assert maximum_cost_near(
        costs=costs,
        width=5,
        height=5,
        resolution=1.0,
        origin_x=0.0,
        origin_y=0.0,
        point=Pose2D(2.5, 2.5),
        radius_m=0.25,
    ) == 254
    assert count_costs_in_oriented_box(
        costs=costs,
        width=5,
        height=5,
        resolution=1.0,
        origin_x=0.0,
        origin_y=0.0,
        center=Pose3D(2.5, 2.5, 0.5),
        size=BoxSize(1.0, 1.0, 1.0),
    ) == 1
    assert terminal_failure_class(succeeded=True, timed_out=False, error_code=0) == "succeeded"
    assert terminal_failure_class(succeeded=False, timed_out=True, error_code=0) == "execution_timeout"
    assert terminal_failure_class(succeeded=False, timed_out=False, error_code=208) == "planning_failure"
    assert terminal_failure_class(succeeded=False, timed_out=False, error_code=105) == "controller_failure"


def test_path_invalidation_uses_blocker_geometry() -> None:
    box = BoxSize(1.0, 2.0, 1.0)
    center = Pose3D(2.0, 2.0, 0.5)
    assert path_intersects_oriented_box(
        [Pose2D(0.0, 2.0), Pose2D(2.0, 2.0), Pose2D(4.0, 2.0)], center, box
    )
    assert not path_intersects_oriented_box(
        [Pose2D(0.0, 0.0), Pose2D(4.0, 0.0)], center, box
    )


def test_behavior_tree_hard_codes_only_requested_planner() -> None:
    tree = planner_behavior_tree("DynNavJoint")
    assert 'planner_id="DynNavJoint"' in tree
    assert "GridBased" not in tree


def test_dynamic_summary_retains_invalid_trials() -> None:
    rows = [
        {
            "planner_id": "p",
            "valid_trial": True,
            "navigation_success": True,
            "operational_irreversible_failure": False,
            "terminal_failure_class": "succeeded",
            "simulation_duration_s": 4.0,
            "number_of_recoveries": 0,
        },
        {
            "planner_id": "p",
            "valid_trial": False,
            "navigation_success": False,
            "operational_irreversible_failure": None,
            "terminal_failure_class": "navigation_failure_unattributed",
            "simulation_duration_s": 0.0,
            "number_of_recoveries": 0,
        },
    ]
    summary = summarize_dynamic_trials(rows)["p"]
    assert summary["trials"] == 2
    assert summary["valid_trials"] == 1
    assert summary["invalid_trials"] == 1
    assert summary["navigation_success_rate"] == 1.0


def test_invalid_suite_version_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "invalid.yaml"
    source.write_text("schema_version: 2\nplanners: []\nscenarios: []\n")
    with pytest.raises(ValueError, match="unsupported schema_version"):
        load_suite(source)
