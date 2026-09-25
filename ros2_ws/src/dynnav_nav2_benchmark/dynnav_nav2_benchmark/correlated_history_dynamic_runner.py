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

from dynnav_nav2_benchmark.analysis import Pose2D, balanced_trial_order
from dynnav_nav2_benchmark.correlated_history_execution import (
    blocker_footprint_cells,
    load_correlated_history_execution_suite,
    quantized_hazard_transitions,
    quantized_hazard_trigger_gates,
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
from dynnav_nav2_benchmark.history_execution import (
    HISTORY_RESET_COMMAND,
    world_to_cell,
)


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


def _initial_plan_audit(
    navigator,
    *,
    scenario,
    planner_id: str,
    trigger_gates,
    metadata,
) -> dict[str, object]:
    """Record planner-server route choice before dynamic execution."""

    try:
        path = navigator.getPath(
            _pose_message(navigator, scenario.start, scenario.frame_id),
            _pose_message(navigator, scenario.goal, scenario.frame_id),
            planner_id=planner_id,
            use_start=True,
        )
    except Exception as exc:
        return {
            "success": False,
            "error": f"{type(exc).__name__}: {exc}",
            "path_length_m": None,
            "pose_count": 0,
            "route_class": None,
            "trigger_gate_crossings": [False, False],
            "path_cells": [],
        }

    if path is None or len(path.poses) < 2:
        return {
            "success": False,
            "error": "planner returned no valid path",
            "path_length_m": None,
            "pose_count": 0 if path is None else len(path.poses),
            "route_class": None,
            "trigger_gate_crossings": [False, False],
            "path_cells": [],
        }

    points = [
        (
            float(pose.pose.position.x),
            float(pose.pose.position.y),
        )
        for pose in path.poses
    ]
    path_length_m = sum(
        math.hypot(x1 - x0, y1 - y0)
        for (x0, y0), (x1, y1) in zip(points, points[1:], strict=False)
    )

    cells: list[tuple[int, int]] = []
    for x, y in points:
        cell = world_to_cell(
            Pose2D(x, y),
            origin_x=float(metadata.origin.position.x),
            origin_y=float(metadata.origin.position.y),
            resolution=float(metadata.resolution),
        )
        if not cells or cells[-1] != cell:
            cells.append(cell)

    path_edges = set(zip(cells, cells[1:], strict=False))
    gate_crossings = [
        any(edge in path_edges for edge in gate)
        for gate in trigger_gates
    ]
    blocker_mid_y = (
        scenario.hazards[0].blocker_pose.y
        + scenario.hazards[1].blocker_pose.y
    ) / 2.0
    route_class = (
        "lower_detour"
        if min(y for _x, y in points) < blocker_mid_y
        else "upper_direct"
    )
    return {
        "success": True,
        "error": None,
        "path_length_m": path_length_m,
        "pose_count": len(points),
        "route_class": route_class,
        "trigger_gate_crossings": gate_crossings,
        "path_cells": [list(cell) for cell in cells],
    }


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
    localization_mode: str,
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
    if localization_mode == "amcl":
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
    trigger_gates = quantized_hazard_trigger_gates(
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
    runtime_specs = tuple(
        CorrelatedHazardRuntimeSpec(
            hazard.trigger.hazard_id,
            transitions[index],
            p,
            trigger_edges=trigger_gates[index],
            gate_x=(hazard.trigger.source.x + hazard.trigger.target.x) / 2.0,
            gate_center_y=(hazard.trigger.source.y + hazard.trigger.target.y) / 2.0,
            gate_half_width_m=hazard.trigger_gate_half_width_m,
            origin_y=float(meta.origin.position.y),
            resolution=float(meta.resolution),
        )
        for index, hazard in enumerate(scenario.hazards)
    )
    state = CorrelatedHistoryRuntimeState(runtime_specs, latent)
    publisher.publish(String(data=HISTORY_RESET_COMMAND))
    rclpy.spin_once(navigator, timeout_sec=0.1)
    time.sleep(0.1)

    initial_plan = _initial_plan_audit(
        navigator,
        scenario=scenario,
        planner_id=planner_id,
        trigger_gates=trigger_gates,
        metadata=meta,
    )

    # BasicNavigator keeps the previous task feedback object. Clear it before
    # starting a new trial so an earlier timeout cannot immediately cancel the
    # next goal via a stale navigation_time value.
    navigator.feedback = None

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
            "initial_plan": initial_plan,
        }

    applied = [False, False]
    injection_error = None
    last_feedback = None
    navigation_time_s = None
    max_start_displacement_m = 0.0
    start_wall = time.monotonic()
    while not navigator.isTaskComplete():
        feedback = navigator.getFeedback()
        if feedback is not None:
            last_feedback = feedback
            pose = feedback.current_pose.pose.position
            max_start_displacement_m = max(
                max_start_displacement_m,
                math.hypot(
                    float(pose.x) - scenario.start.x,
                    float(pose.y) - scenario.start.y,
                ),
            )
            emitted = state.observe_world(float(pose.x), float(pose.y))
            for text in emitted:
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
            navigation_time_s = nav_s
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
        recovery_costs = list(cm.data)
        width = int(md.size_x)
        height = int(md.size_y)
        for index, hazard in enumerate(scenario.hazards):
            if not applied[index]:
                continue
            footprint = blocker_footprint_cells(
                center=hazard.blocker_pose,
                size_xy=(suite.blocker_size[0], suite.blocker_size[1]),
                origin_x=float(md.origin.position.x),
                origin_y=float(md.origin.position.y),
                resolution=float(md.resolution),
            )
            for x, y in footprint:
                if 0 <= x < width and 0 <= y < height:
                    recovery_costs[y * width + x] = 254

        recovery = assess_recovery_reachability(
            costs=recovery_costs,
            width=width,
            height=height,
            resolution=float(md.resolution),
            origin_x=float(md.origin.position.x),
            origin_y=float(md.origin.position.y),
            start=Pose2D(float(pose.x), float(pose.y)),
            safe_region=scenario.safe_region,
            budget_m=scenario.recovery_budget_m,
        ).to_dict()

    motion_valid = max_start_displacement_m >= 0.25
    valid = state.observation_valid and injection_error is None and motion_valid
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
        or ("localization_jump" if not state.observation_valid else None)
        or ("insufficient_motion" if not motion_valid else None),
        "navigation_success": success,
        "navigation_time_s": navigation_time_s,
        "initial_plan": initial_plan,
        "max_start_displacement_m": max_start_displacement_m,
        "result_error_code": error_code,
        "result_error_message": error_message,
        "latent_closures": list(latent),
        "hazards": state.hazard_outcomes(),
        "closures_applied": applied,
        "accepted_transitions": state.accepted_transitions,
        "sampling_gaps": state.sampling_gaps,
        "localization_jumps": state.localization_jumps,
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
    parser.add_argument(
        "--dependence",
        action="append",
        choices=("independent", "common_cause", "anti_correlated"),
        help="Run only selected frozen dependence condition(s).",
    )
    parser.add_argument("--reset-settle-s", type=float, default=2.0)
    parser.add_argument(
        "--localization-mode",
        choices=("amcl", "odom_reset"),
        default="amcl",
    )
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

        if args.localization_mode == "odom_reset":
            nav.waitUntilNav2Active(localizer="robot_localization")
        else:
            nav.waitUntilNav2Active()
        bts = _write_behavior_trees(args.output, suite.planner_ids)
        publisher = nav.create_publisher(String, "dynnav/executed_transition", 10)
        time.sleep(0.5)
        trials = []
        selected_dependence = (
            tuple(args.dependence)
            if args.dependence
            else suite.scenario.dependence_conditions
        )
        for dependence in selected_dependence:
            condition_index = suite.scenario.dependence_conditions.index(
                dependence
            )
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
                            localization_mode=args.localization_mode,
                        )
                    )

        payload = {
            "schema_version": 1,
            "benchmark_type": "correlated_action_triggered_history",
            "seed": suite.seed,
            "dependence_conditions": list(selected_dependence),
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
