"""ROS runner for frozen action-triggered history trials."""

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

from dynnav_nav2_benchmark.analysis import Pose2D, balanced_trial_order
from dynnav_nav2_benchmark.dynamic_analysis import (
    Pose3D,
    assess_recovery_reachability,
)
from dynnav_nav2_benchmark.dynamic_runner import (
    _pose_message,
    _result_details,
    _set_entity_pose,
    _spawn_blocker,
    _wait_after_cancel,
    _wait_for_service,
    _write_behavior_trees,
)
from dynnav_nav2_benchmark.history_execution import (
    HISTORY_RESET_COMMAND,
    deterministic_event_draw,
    load_history_execution_suite,
    transition_from_world_trigger,
    world_to_cell,
)
from dynnav_nav2_benchmark.history_runtime import HistoryRuntimeState


def _trial(
    navigator,
    set_pose_client,
    suite,
    planner_id,
    repetition,
    order_index,
    bt,
    reset_s,
    publisher,
):
    scenario = suite.scenario
    _set_entity_pose(
        navigator,
        set_pose_client,
        suite.blocker_entity,
        suite.blocker_parking_pose,
    )
    _set_entity_pose(
        navigator,
        set_pose_client,
        suite.robot_entity,
        Pose3D(scenario.start.x, scenario.start.y, 0.01, scenario.start.yaw),
    )
    navigator.setInitialPose(
        _pose_message(navigator, scenario.start, scenario.frame_id)
    )
    navigator.clearAllCostmaps()
    time.sleep(reset_s)
    costmap = navigator.getGlobalCostmap()
    meta = costmap.metadata
    origin_x = float(meta.origin.position.x)
    origin_y = float(meta.origin.position.y)
    resolution = float(meta.resolution)
    trigger = transition_from_world_trigger(
        scenario.trigger,
        origin_x=origin_x,
        origin_y=origin_y,
        resolution=resolution,
    )
    latent = deterministic_event_draw(
        suite.seed,
        scenario.name,
        repetition,
        scenario.trigger.hazard_id,
    )
    state = HistoryRuntimeState(
        trigger,
        latent,
        scenario.trigger.closure_probability,
    )
    publisher.publish(String(data=HISTORY_RESET_COMMAND))
    rclpy.spin_once(navigator, timeout_sec=0.1)
    time.sleep(0.1)
    navigator.feedback = None
    accepted = navigator.goToPose(
        _pose_message(navigator, scenario.goal, scenario.frame_id),
        behavior_tree=str(bt),
    )
    if not accepted:
        return {
            "planner_id": planner_id,
            "repetition": repetition,
            "order_index": order_index,
            "valid_trial": False,
            "invalid_reason": "navigation_goal_rejected",
        }

    start_wall = time.monotonic()
    closure_applied = False
    injection_error = None
    last_feedback = None
    while not navigator.isTaskComplete():
        feedback = navigator.getFeedback()
        if feedback is not None:
            last_feedback = feedback
            pose = feedback.current_pose.pose.position
            cell = world_to_cell(
                Pose2D(float(pose.x), float(pose.y)),
                origin_x=origin_x,
                origin_y=origin_y,
                resolution=resolution,
            )
            text = state.observe(cell)
            if text is not None:
                publisher.publish(String(data=text))
            if state.closure_requested and not closure_applied:
                clearance = math.hypot(
                    float(pose.x) - scenario.blocker_pose.x,
                    float(pose.y) - scenario.blocker_pose.y,
                )
                if clearance < scenario.minimum_injection_clearance_m:
                    injection_error = "unsafe_injection_clearance"
                else:
                    try:
                        _set_entity_pose(
                            navigator,
                            set_pose_client,
                            suite.blocker_entity,
                            scenario.blocker_pose,
                        )
                    except Exception as exc:
                        injection_error = (
                            "event_injection_failed:"
                            f"{type(exc).__name__}:{exc}"
                        )
                    else:
                        closure_applied = True
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
        current = Pose2D(float(pose.x), float(pose.y))
        cm = navigator.getGlobalCostmap()
        md = cm.metadata
        recovery = assess_recovery_reachability(
            costs=cm.data,
            width=int(md.size_x),
            height=int(md.size_y),
            resolution=float(md.resolution),
            origin_x=float(md.origin.position.x),
            origin_y=float(md.origin.position.y),
            start=current,
            safe_region=scenario.safe_region,
            budget_m=scenario.recovery_budget_m,
        ).to_dict()
    valid = state.observation_valid and injection_error is None
    recovery_feasible = (
        None if recovery is None else bool(recovery["within_budget"])
    )
    return {
        "planner_id": planner_id,
        "repetition": repetition,
        "order_index": order_index,
        "valid_trial": valid,
        "invalid_reason": injection_error
        or ("sampling_gap" if not state.observation_valid else None),
        "navigation_success": success,
        "result_error_code": error_code,
        "result_error_message": error_message,
        "latent_draw": latent,
        "closure_probability": scenario.trigger.closure_probability,
        "trigger_observed": state.trigger_observed,
        "closure_realized": state.closure_realized,
        "closure_applied": closure_applied,
        "event_outcome": state.event_outcome,
        "accepted_transitions": state.accepted_transitions,
        "sampling_gaps": state.sampling_gaps,
        "recovery_assessment": recovery,
        "recovery_feasible": recovery_feasible,
        "operational_irreversible_failure": bool(
            valid
            and not success
            and closure_applied
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
    suite = load_history_execution_suite(args.scenario)
    args.output.mkdir(parents=True, exist_ok=True)
    rclpy.init(args=ros_arguments)
    nav = BasicNavigator(node_name="dynnav_history_execution_benchmark")
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
        try:
            _spawn_blocker(nav, spawn, suite, args.blocker_sdf)
        except RuntimeError:
            pass
        nav.waitUntilNav2Active()
        bts = _write_behavior_trees(args.output, suite.planner_ids)
        publisher = nav.create_publisher(String, "dynnav/executed_transition", 10)
        time.sleep(0.5)
        schedule = balanced_trial_order(
            suite.planner_ids,
            args.repetitions,
            suite.seed,
        )
        trials = []
        for repetition, block in enumerate(schedule):
            for order_index, planner_id in enumerate(block):
                trials.append(
                    _trial(
                        nav,
                        set_pose,
                        suite,
                        planner_id,
                        repetition,
                        order_index,
                        bts[planner_id],
                        args.reset_settle_s,
                        publisher,
                    )
                )
        payload = {
            "schema_version": 1,
            "seed": suite.seed,
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
