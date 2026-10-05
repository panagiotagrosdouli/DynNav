"""Execute frozen route-invalidation trials through Nav2 and Gazebo Harmonic."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import os
import shutil
import sys
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import rclpy
from geometry_msgs.msg import Pose, PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from nav_msgs.msg import Path as NavPath
from rclpy.client import Client
from rclpy.parameter import Parameter
from ros_gz_interfaces.msg import Entity
from ros_gz_interfaces.srv import SetEntityPose, SpawnEntity

from dynnav_nav2_benchmark.analysis import (
    Pose2D,
    balanced_trial_order,
    resolve_map_image,
)
from dynnav_nav2_benchmark.dynamic_analysis import (
    BoxSize,
    DynamicBenchmarkSuite,
    DynamicScenarioSpec,
    Pose3D,
    assess_recovery_reachability,
    count_costs_in_oriented_box,
    load_dynamic_suite,
    path_intersects_oriented_box,
    planner_behavior_tree,
    summarize_dynamic_trials,
    terminal_failure_class,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    temporary.replace(path)


def _atomic_gzip_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with gzip.open(temporary, "wt", encoding="utf-8") as handle:
        json.dump(payload, handle, separators=(",", ":"))
    temporary.replace(path)


def _pose_message(navigator: BasicNavigator, pose: Pose2D, frame_id: str) -> PoseStamped:
    message = PoseStamped()
    message.header.frame_id = frame_id
    message.header.stamp = navigator.get_clock().now().to_msg()
    message.pose.position.x = pose.x
    message.pose.position.y = pose.y
    message.pose.orientation.z = math.sin(pose.yaw / 2.0)
    message.pose.orientation.w = math.cos(pose.yaw / 2.0)
    return message


def _gazebo_pose(pose: Pose3D) -> Pose:
    message = Pose()
    message.position.x = pose.x
    message.position.y = pose.y
    message.position.z = pose.z
    message.orientation.z = math.sin(pose.yaw / 2.0)
    message.orientation.w = math.cos(pose.yaw / 2.0)
    return message


def _duration_seconds(duration: Any) -> float:
    return float(duration.sec) + float(duration.nanosec) / 1_000_000_000.0


def _wait_for_service(client: Client, name: str, timeout_s: float = 30.0) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if client.wait_for_service(timeout_sec=1.0):
            return
    raise RuntimeError(f"Gazebo bridge service unavailable: {name}")


def _call_service(
    navigator: BasicNavigator,
    client: Client,
    request: Any,
    description: str,
    timeout_s: float = 15.0,
) -> Any:
    future = client.call_async(request)
    rclpy.spin_until_future_complete(navigator, future, timeout_sec=timeout_s)
    if not future.done():
        raise RuntimeError(f"timed out while {description}")
    response = future.result()
    if response is None or not response.success:
        raise RuntimeError(f"Gazebo rejected request while {description}")
    return response


def _spawn_blocker(
    navigator: BasicNavigator,
    client: Client,
    suite: DynamicBenchmarkSuite,
    sdf_path: Path,
) -> None:
    request = SpawnEntity.Request()
    request.entity_factory.name = suite.blocker_entity
    request.entity_factory.allow_renaming = False
    request.entity_factory.sdf = sdf_path.read_text(encoding="utf-8")
    request.entity_factory.pose = _gazebo_pose(suite.blocker_parking_pose)
    request.entity_factory.relative_to = "world"
    _call_service(navigator, client, request, "spawning route blocker")


def _set_entity_pose(
    navigator: BasicNavigator,
    client: Client,
    entity_name: str,
    pose: Pose3D,
) -> None:
    request = SetEntityPose.Request()
    request.entity.name = entity_name
    request.entity.type = Entity.MODEL
    request.pose = _gazebo_pose(pose)
    _call_service(navigator, client, request, f"moving {entity_name}")


def _feedback_row(feedback: Any) -> dict[str, Any]:
    return {
        "navigation_time_s": _duration_seconds(feedback.navigation_time),
        "x": float(feedback.current_pose.pose.position.x),
        "y": float(feedback.current_pose.pose.position.y),
        "distance_remaining_m": float(feedback.distance_remaining),
        "estimated_time_remaining_s": _duration_seconds(
            feedback.estimated_time_remaining
        ),
        "number_of_recoveries": int(feedback.number_of_recoveries),
    }


def _plan_record(message: NavPath, received_sim_time_s: float) -> dict[str, Any]:
    points = [
        {"x": float(pose.pose.position.x), "y": float(pose.pose.position.y)}
        for pose in message.poses
    ]
    length = sum(
        math.hypot(right["x"] - left["x"], right["y"] - left["y"])
        for left, right in zip(points, points[1:], strict=False)
    )
    return {
        "received_sim_time_s": received_sim_time_s,
        "frame_id": message.header.frame_id,
        "pose_count": len(points),
        "path_length_m": length,
        "points": points,
    }


def _costmap_payload(costmap: Any) -> dict[str, Any]:
    metadata = costmap.metadata
    return {
        "resolution": float(metadata.resolution),
        "size_x": int(metadata.size_x),
        "size_y": int(metadata.size_y),
        "origin": {
            "x": float(metadata.origin.position.x),
            "y": float(metadata.origin.position.y),
            "z": float(metadata.origin.position.z),
            "orientation": {
                "x": float(metadata.origin.orientation.x),
                "y": float(metadata.origin.orientation.y),
                "z": float(metadata.origin.orientation.z),
                "w": float(metadata.origin.orientation.w),
            },
        },
        "data": [int(value) for value in costmap.data],
    }


def _blocker_observation_size(
    suite: DynamicBenchmarkSuite, scenario: DynamicScenarioSpec
) -> BoxSize:
    margin = 2.0 * scenario.event.observation_margin_m
    return BoxSize(
        suite.blocker_size.x + margin,
        suite.blocker_size.y + margin,
        suite.blocker_size.z,
    )


def _capture_recovery_assessment(
    *,
    navigator: BasicNavigator,
    suite: DynamicBenchmarkSuite,
    scenario: DynamicScenarioSpec,
    feedback: Any,
    planner_id: str,
    repetition: int,
    output: Path,
    navigation_time_s: float,
    pre_event_lethal_cells: int,
) -> tuple[dict[str, Any], bool, bool, int, str, str]:
    costmap = navigator.getGlobalCostmap()
    snapshot = _costmap_payload(costmap)
    metadata = costmap.metadata
    current = Pose2D(
        float(feedback.current_pose.pose.position.x),
        float(feedback.current_pose.pose.position.y),
    )
    post_event_lethal_cells = count_costs_in_oriented_box(
        costs=costmap.data,
        width=int(metadata.size_x),
        height=int(metadata.size_y),
        resolution=float(metadata.resolution),
        origin_x=float(metadata.origin.position.x),
        origin_y=float(metadata.origin.position.y),
        center=scenario.event.blocker_pose,
        size=_blocker_observation_size(suite, scenario),
    )
    blocker_observed = (
        post_event_lethal_cells - pre_event_lethal_cells
        >= scenario.event.minimum_lethal_cell_increase
    )
    assessment = assess_recovery_reachability(
        costs=costmap.data,
        width=int(metadata.size_x),
        height=int(metadata.size_y),
        resolution=float(metadata.resolution),
        origin_x=float(metadata.origin.position.x),
        origin_y=float(metadata.origin.position.y),
        start=current,
        safe_region=scenario.safe_region,
        budget_m=scenario.recovery_budget_m,
    )
    snapshot_name = f"costmap_{scenario.name}_{planner_id}_r{repetition}.json.gz"
    snapshot["captured_at_navigation_time_s"] = navigation_time_s
    snapshot["robot_pose"] = asdict(current)
    snapshot["blocker_pose"] = asdict(scenario.event.blocker_pose)
    snapshot["pre_event_lethal_cells_in_blocker_footprint"] = (
        pre_event_lethal_cells
    )
    snapshot["post_event_lethal_cells_in_blocker_footprint"] = (
        post_event_lethal_cells
    )
    _atomic_gzip_json(output / snapshot_name, snapshot)
    return (
        assessment.to_dict(),
        not assessment.within_budget,
        blocker_observed,
        post_event_lethal_cells,
        snapshot_name,
        _sha256(output / snapshot_name),
    )


def _wait_for_sim_clock(
    navigator: BasicNavigator, target_s: float, wall_timeout_s: float
) -> bool:
    deadline = time.monotonic() + wall_timeout_s
    while (
        navigator.get_clock().now().nanoseconds / 1_000_000_000.0 < target_s
        and time.monotonic() < deadline
    ):
        rclpy.spin_once(navigator, timeout_sec=0.1)
    return navigator.get_clock().now().nanoseconds / 1_000_000_000.0 >= target_s


def _write_behavior_trees(
    output: Path, planner_ids: tuple[str, ...]
) -> dict[str, Path]:
    directory = output / "behavior_trees"
    directory.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for planner_id in planner_ids:
        path = directory / f"navigate_{planner_id}.xml"
        path.write_text(planner_behavior_tree(planner_id), encoding="utf-8")
        paths[planner_id] = path
    return paths


def _result_details(navigator: BasicNavigator) -> tuple[bool, int, str]:
    task_result = navigator.getResult()
    succeeded = task_result == TaskResult.SUCCEEDED
    wrapped = navigator.result_future.result() if navigator.result_future else None
    raw = getattr(wrapped, "result", None)
    return (
        succeeded,
        int(getattr(raw, "error_code", 0)),
        str(getattr(raw, "error_msg", "")),
    )


def _wait_after_cancel(navigator: BasicNavigator, timeout_s: float = 10.0) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline and not navigator.isTaskComplete():
        pass


def _run_dynamic_trial(
    navigator: BasicNavigator,
    set_pose_client: Client,
    suite: DynamicBenchmarkSuite,
    scenario: DynamicScenarioSpec,
    planner_id: str,
    behavior_tree: Path,
    repetition: int,
    order_index: int,
    output: Path,
    reset_settle_s: float,
) -> dict[str, Any]:
    _set_entity_pose(
        navigator,
        set_pose_client,
        suite.blocker_entity,
        suite.blocker_parking_pose,
    )
    robot_pose = Pose3D(
        scenario.start.x,
        scenario.start.y,
        0.01,
        scenario.start.yaw,
    )
    _set_entity_pose(
        navigator,
        set_pose_client,
        suite.robot_entity,
        robot_pose,
    )
    navigator.setInitialPose(_pose_message(navigator, scenario.start, scenario.frame_id))
    navigator.clearAllCostmaps()
    time.sleep(reset_settle_s)

    plan_trace: list[dict[str, Any]] = []

    def on_plan(message: NavPath) -> None:
        plan_trace.append(
            _plan_record(
                message,
                navigator.get_clock().now().nanoseconds / 1_000_000_000.0,
            )
        )

    plan_subscription = navigator.create_subscription(NavPath, "/plan", on_plan, 10)

    # BasicNavigator retains the previous task's last feedback between goals.
    navigator.feedback = None
    accepted = navigator.goToPose(
        _pose_message(navigator, scenario.goal, scenario.frame_id),
        behavior_tree=str(behavior_tree),
    )
    if not accepted:
        navigator.destroy_subscription(plan_subscription)
        return {
            "scenario": scenario.name,
            "planner_id": planner_id,
            "repetition": repetition,
            "order_index": order_index,
            "valid_trial": False,
            "invalid_reason": "navigation_goal_rejected",
            "navigation_success": False,
            "terminal_failure_class": "invalid_trial",
            "result_error_code": 0,
            "result_error_message": "goal rejected",
            "simulation_duration_s": 0.0,
            "wall_duration_s": 0.0,
            "number_of_recoveries": 0,
            "initial_pose_error_m": None,
            "event_applied": False,
            "event_elapsed_s": None,
            "event_not_applied_reason": "navigation_goal_rejected",
            "event_robot_clearance_m": None,
            "blocker_observed": False,
            "pre_event_lethal_cells_in_blocker_footprint": None,
            "post_event_lethal_cells_in_blocker_footprint": None,
            "recovery_assessment": None,
            "operational_irreversible_failure": None,
            "pre_event_path_invalidated": None,
            "planner_path_count": 0,
            "replan_count": 0,
            "planner_paths": [],
            "costmap_snapshot": None,
            "costmap_snapshot_sha256": None,
            "trace": [],
        }

    started_wall = time.monotonic()
    started_sim = navigator.get_clock().now().nanoseconds / 1_000_000_000.0
    trace: list[dict[str, Any]] = []
    last_feedback: Any | None = None
    initial_pose_error: float | None = None
    last_trace_time = -math.inf
    event_applied = False
    event_elapsed: float | None = None
    event_sim_clock: float | None = None
    event_robot_clearance: float | None = None
    event_error: str | None = None
    recovery_assessment: dict[str, Any] | None = None
    irreversible: bool | None = None
    blocker_observed = False
    pre_event_lethal_cells: int | None = None
    post_event_lethal_cells: int | None = None
    snapshot_name: str | None = None
    snapshot_sha256: str | None = None
    timed_out = False
    pre_event_path_invalidated: bool | None = None

    def capture_recovery(feedback: Any, navigation_time_s: float) -> None:
        nonlocal recovery_assessment
        nonlocal irreversible
        nonlocal blocker_observed
        nonlocal post_event_lethal_cells
        nonlocal snapshot_name
        nonlocal snapshot_sha256
        nonlocal event_error
        try:
            (
                recovery_assessment,
                irreversible,
                blocker_observed,
                post_event_lethal_cells,
                snapshot_name,
                snapshot_sha256,
            ) = _capture_recovery_assessment(
                navigator=navigator,
                suite=suite,
                scenario=scenario,
                feedback=feedback,
                planner_id=planner_id,
                repetition=repetition,
                output=output,
                navigation_time_s=navigation_time_s,
                pre_event_lethal_cells=int(pre_event_lethal_cells),
            )
        except Exception as exc:
            event_error = f"recovery_assessment_failed: {type(exc).__name__}: {exc}"
        else:
            if not blocker_observed:
                event_error = "blocker_not_observed_in_global_costmap"

    while not navigator.isTaskComplete():
        wall_elapsed = time.monotonic() - started_wall
        sim_elapsed = (
            navigator.get_clock().now().nanoseconds / 1_000_000_000.0 - started_sim
        )
        feedback = navigator.getFeedback()
        if feedback is not None:
            last_feedback = feedback
            if initial_pose_error is None:
                initial_pose_error = math.hypot(
                    float(feedback.current_pose.pose.position.x) - scenario.start.x,
                    float(feedback.current_pose.pose.position.y) - scenario.start.y,
                )
                if initial_pose_error > scenario.reset_pose_tolerance_m:
                    event_error = "reset_pose_mismatch"
            feedback_elapsed = _duration_seconds(feedback.navigation_time)
            if feedback_elapsed - last_trace_time >= 0.2:
                trace.append(_feedback_row(feedback))
                last_trace_time = feedback_elapsed
            sim_elapsed = feedback_elapsed

        if (
            not event_applied
            and event_error is None
            and sim_elapsed >= scenario.event.trigger_elapsed_s
        ):
            if last_feedback is None:
                event_error = "no_navigation_feedback_at_event"
            else:
                robot_x = float(last_feedback.current_pose.pose.position.x)
                robot_y = float(last_feedback.current_pose.pose.position.y)
                event_robot_clearance = math.hypot(
                    robot_x - scenario.event.blocker_pose.x,
                    robot_y - scenario.event.blocker_pose.y,
                )
                if (
                    event_robot_clearance
                    < scenario.event.minimum_injection_clearance_m
                ):
                    event_error = "unsafe_injection_clearance"
                else:
                    try:
                        pre_event_costmap = navigator.getGlobalCostmap()
                        pre_metadata = pre_event_costmap.metadata
                        pre_event_lethal_cells = count_costs_in_oriented_box(
                            costs=pre_event_costmap.data,
                            width=int(pre_metadata.size_x),
                            height=int(pre_metadata.size_y),
                            resolution=float(pre_metadata.resolution),
                            origin_x=float(pre_metadata.origin.position.x),
                            origin_y=float(pre_metadata.origin.position.y),
                            center=scenario.event.blocker_pose,
                            size=_blocker_observation_size(suite, scenario),
                        )
                        if not plan_trace:
                            raise RuntimeError("no planner path received before event")
                        latest_points = tuple(
                            Pose2D(float(point["x"]), float(point["y"]))
                            for point in plan_trace[-1]["points"]
                        )
                        pre_event_path_invalidated = path_intersects_oriented_box(
                            latest_points,
                            scenario.event.blocker_pose,
                            _blocker_observation_size(suite, scenario),
                        )
                        if (
                            scenario.event.require_forward_path_invalidation
                            and not pre_event_path_invalidated
                        ):
                            raise RuntimeError(
                                "event does not intersect pre-event planner path"
                            )
                        _set_entity_pose(
                            navigator,
                            set_pose_client,
                            suite.blocker_entity,
                            scenario.event.blocker_pose,
                        )
                    except Exception as exc:
                        event_error = (
                            f"event_injection_failed: {type(exc).__name__}: {exc}"
                        )
                    else:
                        event_applied = True
                        event_elapsed = sim_elapsed
                        event_sim_clock = (
                            navigator.get_clock().now().nanoseconds
                            / 1_000_000_000.0
                        )

        if event_error is not None:
            navigator.cancelTask()
            _wait_after_cancel(navigator)
            break

        assessment_due = (
            event_applied
            and recovery_assessment is None
            and event_error is None
            and navigator.get_clock().now().nanoseconds / 1_000_000_000.0
            >= float(event_sim_clock) + scenario.event.observation_settle_s
        )
        if assessment_due:
            if last_feedback is None:
                event_error = "no_navigation_feedback_for_recovery_assessment"
            else:
                capture_recovery(last_feedback, sim_elapsed)

        if event_error is not None:
            navigator.cancelTask()
            _wait_after_cancel(navigator)
            break

        if sim_elapsed >= scenario.execution_timeout_s or wall_elapsed >= scenario.wall_timeout_s:
            timed_out = True
            navigator.cancelTask()
            _wait_after_cancel(navigator)
            break

    wall_duration = time.monotonic() - started_wall
    succeeded, error_code, error_message = _result_details(navigator)
    final_sim_duration = (
        _duration_seconds(last_feedback.navigation_time)
        if last_feedback is not None
        else navigator.get_clock().now().nanoseconds / 1_000_000_000.0 - started_sim
    )
    recoveries = (
        int(last_feedback.number_of_recoveries) if last_feedback is not None else 0
    )
    pre_event_terminal_failure = (
        not event_applied and not succeeded and not timed_out and event_error is None
    )
    event_not_applied_reason: str | None = None
    if event_error is None and not event_applied:
        if pre_event_terminal_failure:
            # A genuine method failure before the event is a valid outcome for
            # that planner, but it has no post-event irreversibility assessment.
            event_not_applied_reason = "navigation_failed_before_event"
        elif timed_out:
            event_error = "event_not_reached_before_timeout"
        else:
            event_error = "navigation_succeeded_before_event"

    if (
        event_error is None
        and event_applied
        and recovery_assessment is None
        and last_feedback is not None
    ):
        target_clock = float(event_sim_clock) + scenario.event.observation_settle_s
        if _wait_for_sim_clock(
            navigator,
            target_clock,
            wall_timeout_s=scenario.event.observation_settle_s * 3.0 + 5.0,
        ):
            capture_recovery(last_feedback, final_sim_duration)
        else:
            event_error = "simulation_clock_stalled_before_recovery_assessment"
    if event_error is None and event_applied and recovery_assessment is None:
        event_error = "navigation_completed_before_post_event_assessment"

    valid_event_trial = (
        event_error is None
        and event_applied
        and blocker_observed
        and (
            not scenario.event.require_forward_path_invalidation
            or pre_event_path_invalidated is True
        )
        and recovery_assessment is not None
    )
    valid_trial = pre_event_terminal_failure or valid_event_trial
    failure_class = (
        terminal_failure_class(
            succeeded=succeeded,
            timed_out=timed_out,
            error_code=error_code,
        )
        if valid_trial
        else "invalid_trial"
    )
    replans = (
        sum(
            float(path["received_sim_time_s"]) > float(event_sim_clock)
            for path in plan_trace
        )
        if event_sim_clock is not None
        else 0
    )
    record = {
        "scenario": scenario.name,
        "planner_id": planner_id,
        "repetition": repetition,
        "order_index": order_index,
        "valid_trial": valid_trial,
        "invalid_reason": event_error,
        "navigation_success": succeeded,
        "terminal_failure_class": failure_class,
        "result_error_code": error_code,
        "result_error_message": error_message,
        "simulation_duration_s": final_sim_duration,
        "wall_duration_s": wall_duration,
        "number_of_recoveries": recoveries,
        "initial_pose_error_m": initial_pose_error,
        "recovery_exhausted": (not succeeded and recoveries > 0),
        "event_applied": event_applied,
        "event_elapsed_s": event_elapsed,
        "event_not_applied_reason": event_not_applied_reason,
        "event_robot_clearance_m": event_robot_clearance,
        "blocker_observed": blocker_observed,
        "pre_event_lethal_cells_in_blocker_footprint": pre_event_lethal_cells,
        "post_event_lethal_cells_in_blocker_footprint": post_event_lethal_cells,
        "recovery_assessment": recovery_assessment,
        "recovery_feasible": (
            bool(recovery_assessment["within_budget"])
            if valid_trial and recovery_assessment is not None
            else None
        ),
        "operational_irreversible_failure": (
            bool(not succeeded and irreversible)
            if valid_trial and irreversible is not None
            else None
        ),
        "pre_event_path_invalidated": pre_event_path_invalidated,
        "planner_path_count": len(plan_trace),
        "replan_count": replans,
        "planner_paths": plan_trace,
        "costmap_snapshot": snapshot_name,
        "costmap_snapshot_sha256": snapshot_sha256,
        "trace": trace,
    }
    navigator.destroy_subscription(plan_subscription)
    return record


def _summary_by_scenario(
    records: list[dict[str, Any]],
) -> dict[str, dict[str, dict[str, Any]]]:
    scenario_names = sorted({str(record["scenario"]) for record in records})
    return {
        scenario: summarize_dynamic_trials(
            record for record in records if record["scenario"] == scenario
        )
        for scenario in scenario_names
    }


def _result_payload(
    *,
    status: str,
    parsed: argparse.Namespace,
    suite: DynamicBenchmarkSuite,
    records: list[dict[str, Any]],
    scenario_path: Path,
    params_path: Path,
    map_path: Path,
    map_image_path: Path,
    blocker_sdf: Path,
    behavior_trees: dict[str, Path],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "benchmark_type": "dynamic_navigate_to_pose_route_invalidation",
        "status": status,
        "evidence_boundary": (
            "Operational irreversibility is eight-connected reachability to the "
            "frozen safe region on an inflated Nav2 global-costmap snapshot within "
            "the declared distance budget. It is not kinodynamic viability, a "
            "formal safety proof, collision evidence, or physical-robot evidence."
        ),
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "environment": parsed.environment,
        "ros_distro": os.environ.get("ROS_DISTRO", "unknown"),
        "source_revision": os.environ.get("GITHUB_SHA", "unrecorded"),
        "repetitions": parsed.repetitions,
        "scenario_sha256": _sha256(scenario_path),
        "params_sha256": _sha256(params_path),
        "map_yaml_sha256": _sha256(map_path),
        "map_image_sha256": _sha256(map_image_path),
        "blocker_sdf_sha256": _sha256(blocker_sdf),
        "behavior_tree_sha256": {
            planner_id: _sha256(path)
            for planner_id, path in sorted(behavior_trees.items())
        },
        "gazebo": {
            "world_name": suite.world_name,
            "robot_entity": suite.robot_entity,
            "blocker_entity": suite.blocker_entity,
            "blocker_parking_pose": asdict(suite.blocker_parking_pose),
        },
        "planners": [asdict(planner) for planner in suite.planners],
        "scenarios": [asdict(scenario) for scenario in suite.scenarios],
        "trials": records,
        "summary": summarize_dynamic_trials(records),
        "summary_by_scenario": _summary_by_scenario(records),
    }


def _write_trials_csv(path: Path, records: list[dict[str, Any]]) -> None:
    fields = [
        "scenario",
        "planner_id",
        "repetition",
        "order_index",
        "valid_trial",
        "invalid_reason",
        "navigation_success",
        "terminal_failure_class",
        "result_error_code",
        "simulation_duration_s",
        "wall_duration_s",
        "number_of_recoveries",
        "initial_pose_error_m",
        "recovery_exhausted",
        "event_elapsed_s",
        "event_not_applied_reason",
        "event_robot_clearance_m",
        "blocker_observed",
        "pre_event_path_invalidated",
        "planner_path_count",
        "replan_count",
        "pre_event_lethal_cells_in_blocker_footprint",
        "post_event_lethal_cells_in_blocker_footprint",
        "operational_irreversible_failure",
        "recovery_feasible",
        "costmap_snapshot",
        "costmap_snapshot_sha256",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow({field: record.get(field) for field in fields})


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", required=True, type=Path)
    parser.add_argument("--params-file", required=True, type=Path)
    parser.add_argument("--map-file", required=True, type=Path)
    parser.add_argument("--blocker-sdf", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--world-name", required=True)
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--reset-settle-seconds", type=float, default=3.0)
    parser.add_argument("--environment", default="gazebo_harmonic_nav2_minimal_tb3")
    return parser


def main(argv: list[str] | None = None) -> int:
    parsed, ros_arguments = _parser().parse_known_args(argv)
    if parsed.repetitions <= 0 or parsed.reset_settle_seconds < 0.0:
        raise SystemExit("repetitions must be positive and reset settle time non-negative")

    scenario_path = parsed.scenario.resolve()
    params_path = parsed.params_file.resolve()
    map_path = parsed.map_file.resolve()
    map_image_path = resolve_map_image(map_path)
    blocker_sdf = parsed.blocker_sdf.resolve()
    suite = load_dynamic_suite(scenario_path)
    if parsed.world_name != suite.world_name:
        raise SystemExit(
            f"launch world {parsed.world_name!r} does not match suite {suite.world_name!r}"
        )
    output = parsed.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    planner_ids = tuple(planner.planner_id for planner in suite.planners)
    behavior_trees = _write_behavior_trees(output, planner_ids)
    _atomic_json(
        output / "run_manifest.json",
        {
            "schema_version": 1,
            "created_at_utc": datetime.now(UTC).isoformat(),
            "command_argv": list(sys.argv),
            "source_revision": os.environ.get("GITHUB_SHA", "unrecorded"),
            "github_ref": os.environ.get("GITHUB_REF", "unrecorded"),
            "github_run_id": os.environ.get("GITHUB_RUN_ID", "unrecorded"),
            "github_workflow": os.environ.get("GITHUB_WORKFLOW", "unrecorded"),
            "ros_distro": os.environ.get("ROS_DISTRO", "unknown"),
            "scenario_sha256": _sha256(scenario_path),
            "params_sha256": _sha256(params_path),
            "map_yaml_sha256": _sha256(map_path),
            "map_image_sha256": _sha256(map_image_path),
            "blocker_sdf_sha256": _sha256(blocker_sdf),
            "seed": suite.seed,
            "repetitions": parsed.repetitions,
            "planner_ids": list(planner_ids),
        },
    )
    records: list[dict[str, Any]] = []

    rclpy.init(args=ros_arguments)
    navigator = BasicNavigator(node_name="dynnav_dynamic_execution_benchmark")
    navigator.set_parameters([Parameter("use_sim_time", value=True)])
    spawn_service = f"/world/{suite.world_name}/create"
    set_pose_service = f"/world/{suite.world_name}/set_pose"
    spawn_client = navigator.create_client(SpawnEntity, spawn_service)
    set_pose_client = navigator.create_client(SetEntityPose, set_pose_service)
    try:
        navigator.setInitialPose(
            _pose_message(navigator, suite.scenarios[0].start, "map")
        )
        navigator.waitUntilNav2Active()
        _wait_for_service(spawn_client, spawn_service)
        _wait_for_service(set_pose_client, set_pose_service)
        _spawn_blocker(navigator, spawn_client, suite, blocker_sdf)

        for scenario_index, scenario in enumerate(suite.scenarios):
            schedule = balanced_trial_order(
                planner_ids,
                parsed.repetitions,
                suite.seed + scenario_index * 100_000,
            )
            for repetition, block in enumerate(schedule):
                for order_index, planner_id in enumerate(block):
                    navigator.get_logger().info(
                        f"Starting {scenario.name}/{planner_id}/r{repetition}"
                    )
                    record = _run_dynamic_trial(
                        navigator,
                        set_pose_client,
                        suite,
                        scenario,
                        planner_id,
                        behavior_trees[planner_id],
                        repetition,
                        order_index,
                        output,
                        parsed.reset_settle_seconds,
                    )
                    records.append(record)
                    checkpoint = _result_payload(
                        status="running",
                        parsed=parsed,
                        suite=suite,
                        records=records,
                        scenario_path=scenario_path,
                        params_path=params_path,
                        map_path=map_path,
                        map_image_path=map_image_path,
                        blocker_sdf=blocker_sdf,
                        behavior_trees=behavior_trees,
                    )
                    _atomic_json(output / "results.partial.json", checkpoint)
                    _write_trials_csv(output / "trials.partial.csv", records)
    finally:
        try:
            _set_entity_pose(
                navigator,
                set_pose_client,
                suite.blocker_entity,
                suite.blocker_parking_pose,
            )
        except Exception as exc:
            navigator.get_logger().warning(f"Could not park blocker: {exc}")
        navigator.destroyNode()
        rclpy.shutdown()

    payload = _result_payload(
        status="completed",
        parsed=parsed,
        suite=suite,
        records=records,
        scenario_path=scenario_path,
        params_path=params_path,
        map_path=map_path,
        map_image_path=map_image_path,
        blocker_sdf=blocker_sdf,
        behavior_trees=behavior_trees,
    )
    _atomic_json(output / "results.json", payload)
    _write_trials_csv(output / "trials.csv", records)
    shutil.copyfile(scenario_path, output / "scenario_snapshot.yaml")
    shutil.copyfile(params_path, output / "nav2_params_snapshot.yaml")
    shutil.copyfile(map_path, output / "map_snapshot.yaml")
    shutil.copyfile(map_image_path, output / f"map_image_snapshot{map_image_path.suffix}")
    shutil.copyfile(blocker_sdf, output / "blocker_snapshot.sdf")

    invalid = [record for record in records if not record["valid_trial"]]
    if invalid:
        print(f"Dynamic benchmark completed with {len(invalid)} invalid trials")
        return 2
    print(f"Dynamic benchmark complete: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
