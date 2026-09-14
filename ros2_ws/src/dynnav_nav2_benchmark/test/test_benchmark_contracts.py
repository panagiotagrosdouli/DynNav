from pathlib import Path
from xml.etree import ElementTree

from dynnav_nav2_benchmark.analysis import Pose2D, balanced_trial_order, load_suite
from dynnav_nav2_benchmark.configuration import (
    HISTORY_PLANNER_IDS,
    PLANNER_IDS,
    inject_history_planner_parameters,
    inject_planner_parameters,
    planner_parameter_overrides,
)
from dynnav_nav2_benchmark.dynamic_analysis import (
    SafeRegion,
    assess_recovery_reachability,
    load_dynamic_suite,
    planner_behavior_tree,
)

PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def test_scenario_and_runtime_planner_contracts_match() -> None:
    suite = load_suite(PACKAGE_ROOT / "config" / "sandbox_static_queries.yaml")
    assert tuple(planner.planner_id for planner in suite.planners) == PLANNER_IDS
    configured = planner_parameter_overrides()
    for planner in suite.planners:
        if planner.family == "dynnav_ablation":
            assert configured[planner.planner_id]["risk_weight"] == planner.risk_weight
            assert (
                configured[planner.planner_id]["irreversibility_weight"]
                == planner.irreversibility_weight
            )


def test_complete_blocks_are_reproducible() -> None:
    schedule = balanced_trial_order(PLANNER_IDS, repetitions=10, seed=20260811)
    assert schedule == balanced_trial_order(
        PLANNER_IDS, repetitions=10, seed=20260811
    )
    assert all(set(block) == set(PLANNER_IDS) for block in schedule)
    for planner in PLANNER_IDS:
        position_counts = [
            sum(block[position] == planner for block in schedule)
            for position in range(len(PLANNER_IDS))
        ]
        assert max(position_counts) - min(position_counts) <= 1


def test_parameter_injection_preserves_unrelated_nav2_settings() -> None:
    base = {
        "planner_server": {
            "ros__parameters": {
                "expected_planner_frequency": 20.0,
                "planner_plugins": ["GridBased"],
                "GridBased": {"plugin": "default"},
            }
        }
    }
    merged = inject_planner_parameters(base)
    parameters = merged["planner_server"]["ros__parameters"]
    assert parameters["expected_planner_frequency"] == 20.0
    assert parameters["planner_plugins"] == list(PLANNER_IDS)
    assert "GridBased" not in parameters
    assert base["planner_server"]["ros__parameters"]["planner_plugins"] == [
        "GridBased"
    ]


def test_history_parameter_injection_isolates_history_representation() -> None:
    base = {
        "planner_server": {
            "ros__parameters": {
                "expected_planner_frequency": 20.0,
                "planner_plugins": ["GridBased"],
                "GridBased": {"plugin": "default"},
            }
        }
    }
    merged = inject_history_planner_parameters(
        base,
        safe_cell=(160, 190),
        trigger=((174, 189), (175, 189)),
        closure_cell=(181, 191),
        closure_probability=0.8,
        recoverability_weight=4.0,
    )
    parameters = merged["planner_server"]["ros__parameters"]
    assert parameters["planner_plugins"] == list(HISTORY_PLANNER_IDS)
    shortest = parameters["DynNavShortest"]
    history = parameters["DynNavHistory"]
    assert shortest["plugin"] == history["plugin"] == "dynnav_nav2_cpp::DynNavGlobalPlanner"
    assert not shortest.get("history_aware", False)
    assert history["history_aware"] is True
    assert history["history_safe_cells"] == "160:190"
    assert (
        history["history_hazards"]
        == "174:189>175:189@181:191@0.80000000000000004"
    )
    assert history["history_recoverability_weight"] == 4.0
    assert parameters["expected_planner_frequency"] == 20.0


def test_dynamic_suite_uses_configured_planners_and_frozen_events() -> None:
    suite = load_dynamic_suite(PACKAGE_ROOT / "config" / "sandbox_dynamic_events.yaml")
    assert {planner.planner_id for planner in suite.planners} <= set(PLANNER_IDS)
    configured = planner_parameter_overrides()
    for planner in suite.planners:
        if planner.family == "dynnav_ablation":
            assert configured[planner.planner_id]["risk_weight"] == planner.risk_weight
            assert (
                configured[planner.planner_id]["irreversibility_weight"]
                == planner.irreversibility_weight
            )
    assert len(suite.scenarios) == 2
    assert all(scenario.event.trigger_elapsed_s > 0.0 for scenario in suite.scenarios)
    model = ElementTree.parse(PACKAGE_ROOT / "models" / "dynamic_blocker.sdf")
    size_text = model.findtext(".//collision/geometry/box/size")
    assert size_text is not None
    assert tuple(float(value) for value in size_text.split()) == (
        suite.blocker_size.x,
        suite.blocker_size.y,
        suite.blocker_size.z,
    )


def test_frozen_history_scenario_is_pre_outcome_and_cell_consistent() -> None:
    text = (
        PACKAGE_ROOT / "config" / "sandbox_history_triggered_events.yaml"
    ).read_text(encoding="utf-8")
    assert "(174,189) -> (175,189)" in text
    assert "closure_probability: 0.8" in text
    assert "DynNavHistory" in text


def test_recovery_oracle_rejects_sealed_safe_region() -> None:
    costs = [0] * 25
    for y in range(5):
        costs[y * 5 + 2] = 254
    result = assess_recovery_reachability(
        costs=costs,
        width=5,
        height=5,
        resolution=1.0,
        origin_x=0.0,
        origin_y=0.0,
        start=Pose2D(0.5, 2.5),
        safe_region=SafeRegion(Pose2D(4.5, 2.5), radius_m=0.49),
        budget_m=10.0,
    )
    assert not result.reachable
    assert result.reason == "no_recovery_path"


def test_dynamic_behavior_tree_pins_planner_id() -> None:
    tree = planner_behavior_tree("DynNavJoint")
    assert 'planner_id="DynNavJoint"' in tree
