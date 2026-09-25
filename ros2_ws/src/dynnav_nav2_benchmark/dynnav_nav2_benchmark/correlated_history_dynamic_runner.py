"""ROS runner for two-hazard dependence-aware action-triggered trials."""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import rclpy
from nav2_simple_commander.robot_navigator import BasicNavigator
from ros_gz_interfaces.srv import SetEntityPose, SpawnEntity
from std_msgs.msg import String

from dynnav_nav2_benchmark.analysis import balanced_trial_order, Pose2D
from dynnav_nav2_benchmark.correlated_history_execution import (
    load_correlated_history_execution_suite,
    quantized_hazard_transitions,
)
from dynnav_nav2_benchmark.correlated_history_runtime import (
    CorrelatedHazardRuntimeSpec,
    CorrelatedHistoryRuntimeState,
    paired_closure_outcomes,
)
from dynnav_nav2_benchmark.dynamic_analysis import assess_recovery_reachability
from dynnav_nav2_benchmark.dynamic_runner import (
    _call_service,
    _gazebo_pose,
    _pose_message,
    _result_details,
    _set_entity_pose,
    _wait_after_cancel,
    _wait_for_service,
    _write_behavior_trees,
)
from dynnav_nav2_benchmark.history_execution import HISTORY_RESET_COMMAND, world_to_cell


def _spawn_named_blocker(
    navigator,
    client,
    *,
    entity_name: str,
    parking_pose,
    sdf_path: Path,
) -> None:
    request = SpawnEntity.Request()
    request.entity_factory.name = entity_name
    request.entity_factory.allow_renaming = False
    request.entity_factory.sdf = sdf_path.read_text(encoding="utf-8")
    request.entity_factory.pose = _gazebo_pose(parking_pose)
    request.entity_factory.relative_to = "world"
    _call_service(navigator, client, request, f"spawning {entity_name}")


def _trial(
    navigator,
    set_pose_client,
    suite,
    *,
    dependence: str,
    planner_id: str,
    repetition: int,
    order_index: int,
    bt: Path,
    reset_s: float,
    publisher,
):
    scenario = suite.scenario
    for hazard in scenario.hazards:
        _set_entity_pose(
            navigator,
            set_pose_client,
            hazard.blocker_entity,
            suite.blocker_parking_pose,
        )
    _set_entity_pose(
        navigator,
        set_pose_client,
        suite.robot_entity,
        type(suite.blocker_parking_pose)(
            scenario.start.x,
            scenario.start.y,
            0.01,
            scenario.start.yaw,
        ),
    )
    navigator.setInitialPose(
        _pose_message(navigator, scenario.start, scenario.frame_id)
    )
    navigator.clearAllCostmaps()
    time.sleep(reset_s)

    costmap = navigator.getGlobalCostmap()
    meta = costmap.metadata
    transitions = quantized_hazard_transitions(
        suite,
        origin_x=float(meta.origin.position.x),
        origin_y=float(meta.origin.position.y),
        resolution=float(meta.resolution),
    )
    p = scenario.hazards[0].trigger.closure_probability
    latent = paired_closure_outcomes(
        seed=suite.seed,
        scenario_name=scenario.name,
        repetition=repetition,
        dependence=dependence,
        closure_probability=p,
    )
    runtime_specs = (
        CorrelatedHazardRuntimeSpec(
            scenario.hazards[0].trigger.hazard_id,
            transitions[0],
            p,
        ),
        CorrelatedHazardRuntimeSpec(
            scenario.hazards[1].trigger.hazard_id,
            transitions[1],
            p,
        ),
    )
    state = CorrelatedHistoryRuntimeState(runtime_specs, latent)
    publisher.publish(String(data=HISTORY_RESET_COMMAND))
    rclpy.spin_once(navigator, timeout_sec=0.1)
    time.sleep(0.1)

    accepted = navigator.goToPose(
        _pose_message(navigator, scenario.goal, scenario.frame_id),
        behavior_tree=str(bt),
    )
    if not accepted:
        return {
            "dependence": dependence,
            "planner_id": planner_id,
            "repetition": repetition,
            "order_index": order_index,
            "valid_trial": False,
            "invalid_reason": "navigation_goal_rejected",
        }

    applied = [False, False]
    injection_error = None
    last_feedback = None
    start_wall = time.monotonic()
    while not navigator.isTaskComplete():
        feedback = navigator.getFeedback()
        if feedback is not None:
            last_feedback = feedback
            pose = feedback.current_pose.pose.position
            cell = world_to_cell(
                Pose2D(float(pose.x), float(pose.y)),
                origin_x=float(meta.origin.position.x),
                origin_y=float(meta.origin.position.y),
                resolution=float(meta.resolution),
            )
            text = state.observe(cell)
            if text is not None:
                publisher.publish(String(data=text))

            for index, hazard in enumerate(scenario.hazards):
                if not state.closure_requested[index] or applied[index]:
                    continue
                clearance = math.hypot(
                    float(pose.x) - hazard.blocker_pose.x,
                    float(pose.y) - hazard.blocker_pose.y,
                )
                if clearance < scenario.minimum_injection_clearance_m:
                    injection_error = (
                        f"unsafe_injection_clearance:{hazard.trigger.hazard_id}"
                    )
                    break
                try:
                    _set_entity_pose(
                        navigator,
                        set_pose_client,
                        hazard.blocker_entity,
                        hazard.blocker_pose,
                    )
                except Exception as exc:
                    injection_error = (
                        f"event_injection_failed:{hazard.trigger.hazard_id}:"
                        f"{type(exc).__name__}:{exc}"
                    )
                    break
                applied[index] = True

            nav_s = float(feedback.navigation_time.sec) + (
                float(feedback.navigation_time.nanosec) / 1e9
            )
            if nav_s >= scenario.execution_timeout_s:
                navigator.cancelTask()
                _wait_after_cancel(navigator)
                break

        if injection_error is not None:
            navigator.cancelTask()
            _wait_after_cancel(navigator)
            break
        if time.monotonic() - start_wall >= scenario.wall_timeout_s:
            navigator.cancelTask()
            _wait_after_cancel(navigator)
            break
        rclpy.spin_once(navigator, timeout_sec=0.05)

    success, error_code, error_message = _result_details(navigator)
    recovery = None
    if last_feedback is not None:
        pose = last_feedback.current_pose.pose.position
        cm = navigator.getGlobalCostmap()
        md = cm.metadata
        recovery = assess_recovery_reachability(
            costs=cm.data,
            width=int(md.size_x),
            height=int(md.size_y),
            resolution=float(md.resolution),
            origin_x=float(md.origin.position.x),
            origin_y=float(md.origin.position.y),
            start=Pose2D(float(pose.x), float(pose.y)),
            safe_region=scenario.safe_region,
            budget_m=scenario.recovery_budget_m,
        ).to_dict()

    valid = state.observation_valid and injection_error is None
    recovery_feasible = (
        None if recovery is None else bool(recovery["within_budget"])
    )
    return {
        "dependence": dependence,
        "planner_id": planner_id,
        "repetition": repetition,
        "order_index": order_index,
        "valid_trial": valid,
        "invalid_reason": injection_error
        or ("sampling_gap" if not state.observation_valid else None),
        "navigation_success": success,
        "result_error_code": error_code,
        "result_error_message": error_message,
        "latent_closures": list(latent),
        "hazards": state.hazard_outcomes(),
        "closures_applied": applied,
        "accepted_transitions": state.accepted_transitions,
        "sampling_gaps": state.sampling_gaps,
        "recovery_assessment": recovery,
        "recovery_feasible": recovery_feasible,
        "operational_irreversible_failure": bool(
            valid
            and not success
            and any(applied)
            and recovery_feasible is False
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", type=Path, required=True)
    parser.add_argument("--blocker-sdf", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--reset-settle-s", type=float, default=2.0)
    args, ros_arguments = parser.parse_known_args(argv)

    suite = load_correlated_history_execution_suite(args.scenario)
    args.output.mkdir(parents=True, exist_ok=True)
    rclpy.init(args=ros_arguments)
    nav = BasicNavigator(node_name="dynnav_correlated_history_execution_benchmark")
    spawn = nav.create_client(
        SpawnEntity,
        f"/world/{suite.world_name}/create",
    )
    set_pose = nav.create_client(
        SetEntityPose,
        f"/world/{suite.world_name}/set_pose",
    )
    try:
        _wait_for_service(spawn, "spawn blocker")
        _wait_for_service(set_pose, "set entity pose")
        for hazard in suite.scenario.hazards:
            try:
                _spawn_named_blocker(
                    nav,
                    spawn,
                    entity_name=hazard.blocker_entity,
                    parking_pose=suite.blocker_parking_pose,
                    sdf_path=args.blocker_sdf,
                )
            except RuntimeError:
                pass

        nav.waitUntilNav2Active()
        bts = _write_behavior_trees(args.output, suite.planner_ids)
        publisher = nav.create_publisher(String, "dynnav/executed_transition", 10)
        time.sleep(0.5)
        trials = []
        for condition_index, dependence in enumerate(
            suite.scenario.dependence_conditions
        ):
            schedule = balanced_trial_order(
                suite.planner_ids,
                args.repetitions,
                suite.seed + condition_index,
            )
            for repetition, block in enumerate(schedule):
                for order_index, planner_id in enumerate(block):
                    trials.append(
                        _trial(
                            nav,
                            set_pose,
                            suite,
                            dependence=dependence,
                            planner_id=planner_id,
                            repetition=repetition,
                            order_index=order_index,
                            bt=bts[planner_id],
                            reset_s=args.reset_settle_s,
                            publisher=publisher,
                        )
                    )

        payload = {
            "schema_version": 1,
            "benchmark_type": "correlated_action_triggered_history",
            "seed": suite.seed,
            "dependence_conditions": list(
                suite.scenario.dependence_conditions
            ),
            "trials": trials,
        }
        (args.output / "results.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        nav.destroy_publisher(publisher)
        return 0 if all(item["valid_trial"] for item in trials) else 2
    finally:
        nav.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
