"""ROS-independent contracts and reachability oracle for dynamic trials."""

from __future__ import annotations

import heapq
import math
import re
import statistics
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree
from xml.sax.saxutils import escape

import yaml

from dynnav_nav2_benchmark.analysis import PlannerSpec, Pose2D


@dataclass(frozen=True, slots=True)
class Pose3D:
    """Pose used to move a Gazebo entity."""

    x: float
    y: float
    z: float
    yaw: float = 0.0

    def validate(self) -> None:
        if not all(math.isfinite(value) for value in (self.x, self.y, self.z, self.yaw)):
            raise ValueError("Gazebo pose coordinates must be finite")


@dataclass(frozen=True, slots=True)
class BoxSize:
    """Axis-aligned dimensions of the blocker in its local frame."""

    x: float
    y: float
    z: float

    def validate(self) -> None:
        if not all(
            math.isfinite(value) and value > 0.0 for value in (self.x, self.y, self.z)
        ):
            raise ValueError("blocker dimensions must be finite and positive")


@dataclass(frozen=True, slots=True)
class SafeRegion:
    """Circular recovery target in the map frame."""

    center: Pose2D
    radius_m: float

    def validate(self) -> None:
        self.center.validate()
        if not math.isfinite(self.radius_m) or self.radius_m <= 0.0:
            raise ValueError("safe-region radius must be finite and positive")


@dataclass(frozen=True, slots=True)
class ObstacleEvent:
    """Frozen Gazebo obstacle event relative to navigation start."""

    trigger_elapsed_s: float
    observation_settle_s: float
    minimum_injection_clearance_m: float
    observation_margin_m: float
    minimum_lethal_cell_increase: int
    require_forward_path_invalidation: bool
    blocker_pose: Pose3D

    def validate(self) -> None:
        for value in (
            self.trigger_elapsed_s,
            self.observation_settle_s,
            self.minimum_injection_clearance_m,
            self.observation_margin_m,
        ):
            if not math.isfinite(value) or value < 0.0:
                raise ValueError("event timing and clearance must be finite and non-negative")
        if self.trigger_elapsed_s <= 0.0:
            raise ValueError("event trigger time must be positive")
        if self.minimum_lethal_cell_increase <= 0:
            raise ValueError("minimum lethal-cell increase must be positive")
        self.blocker_pose.validate()


@dataclass(frozen=True, slots=True)
class DynamicScenarioSpec:
    """One navigation trial with a fixed route-invalidation event."""

    name: str
    start: Pose2D
    goal: Pose2D
    safe_region: SafeRegion
    event: ObstacleEvent
    recovery_budget_m: float
    reset_pose_tolerance_m: float
    execution_timeout_s: float
    wall_timeout_s: float
    frame_id: str = "map"

    def validate(self) -> None:
        if not self.name or not self.frame_id:
            raise ValueError("dynamic scenario name and frame must be non-empty")
        self.start.validate()
        self.goal.validate()
        self.safe_region.validate()
        self.event.validate()
        if math.hypot(self.goal.x - self.start.x, self.goal.y - self.start.y) <= 0.0:
            raise ValueError("dynamic scenario start and goal must differ")
        for value in (
            self.recovery_budget_m,
            self.reset_pose_tolerance_m,
            self.execution_timeout_s,
            self.wall_timeout_s,
        ):
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError("scenario budgets and timeouts must be positive")
        if self.wall_timeout_s < self.execution_timeout_s:
            raise ValueError("wall timeout cannot be shorter than simulation timeout")


@dataclass(frozen=True, slots=True)
class DynamicBenchmarkSuite:
    """Versioned dynamic-execution benchmark definition."""

    schema_version: int
    seed: int
    world_name: str
    robot_entity: str
    blocker_entity: str
    blocker_parking_pose: Pose3D
    blocker_size: BoxSize
    planners: tuple[PlannerSpec, ...]
    scenarios: tuple[DynamicScenarioSpec, ...]

    def validate(self) -> None:
        if self.schema_version != 1:
            raise ValueError(f"unsupported dynamic schema_version: {self.schema_version}")
        if not all((self.world_name, self.robot_entity, self.blocker_entity)):
            raise ValueError("Gazebo world and entity names must be non-empty")
        self.blocker_parking_pose.validate()
        self.blocker_size.validate()
        if not self.planners or not self.scenarios:
            raise ValueError("dynamic benchmark requires planners and scenarios")
        planner_ids = [planner.planner_id for planner in self.planners]
        scenario_names = [scenario.name for scenario in self.scenarios]
        if len(set(planner_ids)) != len(planner_ids):
            raise ValueError("dynamic planner IDs must be unique")
        if len(set(scenario_names)) != len(scenario_names):
            raise ValueError("dynamic scenario names must be unique")
        identifiers = [
            self.world_name,
            self.robot_entity,
            self.blocker_entity,
            *planner_ids,
            *scenario_names,
        ]
        if any(re.fullmatch(r"[A-Za-z0-9_.-]+", item) is None for item in identifiers):
            raise ValueError("dynamic identifiers must be filesystem-safe")
        for planner in self.planners:
            planner.validate()
        for scenario in self.scenarios:
            scenario.validate()


@dataclass(frozen=True, slots=True)
class RecoveryAssessment:
    """Independent grid reachability result on one global-costmap snapshot."""

    reachable: bool
    within_budget: bool
    path_length_m: float | None
    expanded_cells: int
    safe_cell_count: int
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _pose2(payload: dict[str, Any]) -> Pose2D:
    return Pose2D(
        x=float(payload["x"]),
        y=float(payload["y"]),
        yaw=float(payload.get("yaw", 0.0)),
    )


def _pose3(payload: dict[str, Any]) -> Pose3D:
    return Pose3D(
        x=float(payload["x"]),
        y=float(payload["y"]),
        z=float(payload.get("z", 0.0)),
        yaw=float(payload.get("yaw", 0.0)),
    )


def path_intersects_oriented_box(
    points: Sequence[Pose2D], center: Pose3D, size: BoxSize
) -> bool:
    """Return whether any path pose lies inside a yaw-oriented blocker box."""

    center.validate()
    size.validate()
    cosine = math.cos(center.yaw)
    sine = math.sin(center.yaw)
    half_x = size.x / 2.0
    half_y = size.y / 2.0
    for point in points:
        point.validate()
        dx = point.x - center.x
        dy = point.y - center.y
        local_x = cosine * dx + sine * dy
        local_y = -sine * dx + cosine * dy
        if abs(local_x) <= half_x and abs(local_y) <= half_y:
            return True
    return False


def load_dynamic_suite(path: str | Path) -> DynamicBenchmarkSuite:
    """Load and validate a frozen dynamic benchmark YAML."""

    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("dynamic benchmark must be a YAML mapping")
    gazebo = payload.get("gazebo", {})
    blocker = gazebo.get("blocker", {}) if isinstance(gazebo, dict) else {}
    planners = tuple(
        PlannerSpec(
            planner_id=str(item["planner_id"]),
            family=str(item["family"]),
            risk_weight=(
                float(item["risk_weight"]) if "risk_weight" in item else None
            ),
            irreversibility_weight=(
                float(item["irreversibility_weight"])
                if "irreversibility_weight" in item
                else None
            ),
        )
        for item in payload.get("planners", [])
    )
    scenarios: list[DynamicScenarioSpec] = []
    for item in payload.get("scenarios", []):
        start = _pose2(item["start"])
        safe_payload = item.get("safe_region", {})
        safe_center = _pose2(safe_payload.get("center", item["start"]))
        event_payload = item["event"]
        scenarios.append(
            DynamicScenarioSpec(
                name=str(item["name"]),
                frame_id=str(item.get("frame_id", "map")),
                start=start,
                goal=_pose2(item["goal"]),
                safe_region=SafeRegion(
                    center=safe_center,
                    radius_m=float(safe_payload["radius_m"]),
                ),
                event=ObstacleEvent(
                    trigger_elapsed_s=float(event_payload["trigger_elapsed_s"]),
                    observation_settle_s=float(
                        event_payload["observation_settle_s"]
                    ),
                    minimum_injection_clearance_m=float(
                        event_payload["minimum_injection_clearance_m"]
                    ),
                    observation_margin_m=float(
                        event_payload["observation_margin_m"]
                    ),
                    minimum_lethal_cell_increase=int(
                        event_payload["minimum_lethal_cell_increase"]
                    ),
                    require_forward_path_invalidation=bool(
                        event_payload.get("require_forward_path_invalidation", True)
                    ),
                    blocker_pose=_pose3(event_payload["blocker_pose"]),
                ),
                recovery_budget_m=float(item["recovery_budget_m"]),
                reset_pose_tolerance_m=float(item["reset_pose_tolerance_m"]),
                execution_timeout_s=float(item["execution_timeout_s"]),
                wall_timeout_s=float(item["wall_timeout_s"]),
            )
        )
    suite = DynamicBenchmarkSuite(
        schema_version=int(payload.get("schema_version", 0)),
        seed=int(payload.get("seed", 0)),
        world_name=str(gazebo.get("world_name", "")),
        robot_entity=str(gazebo.get("robot_entity", "")),
        blocker_entity=str(blocker.get("entity_name", "")),
        blocker_parking_pose=_pose3(blocker.get("parking_pose", {})),
        blocker_size=BoxSize(
            x=float(blocker.get("size", {})["x"]),
            y=float(blocker.get("size", {})["y"]),
            z=float(blocker.get("size", {})["z"]),
        ),
        planners=planners,
        scenarios=tuple(scenarios),
    )
    suite.validate()
    return suite


def assess_recovery_reachability(
    *,
    costs: Sequence[int],
    width: int,
    height: int,
    resolution: float,
    origin_x: float,
    origin_y: float,
    start: Pose2D,
    safe_region: SafeRegion,
    budget_m: float,
    lethal_cost_threshold: int = 253,
    allow_unknown: bool = False,
) -> RecoveryAssessment:
    """Find an eight-connected path to a safe region on an inflated costmap."""

    if width <= 0 or height <= 0 or len(costs) != width * height:
        raise ValueError("costmap dimensions do not match data")
    if not math.isfinite(resolution) or resolution <= 0.0:
        raise ValueError("costmap resolution must be positive")
    if not math.isfinite(budget_m) or budget_m <= 0.0:
        raise ValueError("recovery budget must be positive")

    def world_to_index(pose: Pose2D) -> int | None:
        x = math.floor((pose.x - origin_x) / resolution)
        y = math.floor((pose.y - origin_y) / resolution)
        if x < 0 or x >= width or y < 0 or y >= height:
            return None
        return y * width + x

    def traversable(index: int) -> bool:
        value = int(costs[index])
        if value == 255:
            return allow_unknown
        return value < lethal_cost_threshold

    start_index = world_to_index(start)
    if start_index is None:
        return RecoveryAssessment(False, False, None, 0, 0, "start_outside_costmap")
    if not traversable(start_index):
        return RecoveryAssessment(False, False, None, 0, 0, "start_not_traversable")

    safe_cells: set[int] = set()
    for y in range(height):
        world_y = origin_y + (y + 0.5) * resolution
        if abs(world_y - safe_region.center.y) > safe_region.radius_m:
            continue
        for x in range(width):
            world_x = origin_x + (x + 0.5) * resolution
            if (
                math.hypot(
                    world_x - safe_region.center.x,
                    world_y - safe_region.center.y,
                )
                <= safe_region.radius_m
            ):
                index = y * width + x
                if traversable(index):
                    safe_cells.add(index)
    if not safe_cells:
        return RecoveryAssessment(False, False, None, 0, 0, "safe_region_blocked")

    if start_index in safe_cells:
        return RecoveryAssessment(True, True, 0.0, 0, len(safe_cells), "already_safe")

    distances = [math.inf] * (width * height)
    distances[start_index] = 0.0
    queue: list[tuple[float, int]] = [(0.0, start_index)]
    expanded = 0
    directions = (
        (-1, 0, 1.0),
        (1, 0, 1.0),
        (0, -1, 1.0),
        (0, 1, 1.0),
        (-1, -1, math.sqrt(2.0)),
        (-1, 1, math.sqrt(2.0)),
        (1, -1, math.sqrt(2.0)),
        (1, 1, math.sqrt(2.0)),
    )
    while queue:
        distance, index = heapq.heappop(queue)
        if distance != distances[index]:
            continue
        expanded += 1
        if index in safe_cells:
            path_length = distance * resolution
            return RecoveryAssessment(
                True,
                path_length <= budget_m,
                path_length,
                expanded,
                len(safe_cells),
                "reachable_within_budget"
                if path_length <= budget_m
                else "recovery_budget_exceeded",
            )
        y, x = divmod(index, width)
        for delta_y, delta_x, step in directions:
            neighbor_y = y + delta_y
            neighbor_x = x + delta_x
            if not (0 <= neighbor_x < width and 0 <= neighbor_y < height):
                continue
            neighbor = neighbor_y * width + neighbor_x
            if not traversable(neighbor):
                continue
            if delta_x and delta_y:
                side_x = y * width + neighbor_x
                side_y = neighbor_y * width + x
                if not traversable(side_x) or not traversable(side_y):
                    continue
            candidate = distance + step
            if candidate < distances[neighbor]:
                distances[neighbor] = candidate
                heapq.heappush(queue, (candidate, neighbor))
    return RecoveryAssessment(
        False,
        False,
        None,
        expanded,
        len(safe_cells),
        "no_recovery_path",
    )


def maximum_cost_near(
    *,
    costs: Sequence[int],
    width: int,
    height: int,
    resolution: float,
    origin_x: float,
    origin_y: float,
    point: Pose2D,
    radius_m: float,
) -> int:
    """Return the maximum cost around an injected obstacle location."""

    if width <= 0 or height <= 0 or len(costs) != width * height:
        raise ValueError("costmap dimensions do not match data")
    if resolution <= 0.0 or radius_m < 0.0:
        raise ValueError("resolution must be positive and radius non-negative")
    radius_cells = math.ceil(radius_m / resolution)
    center_x = math.floor((point.x - origin_x) / resolution)
    center_y = math.floor((point.y - origin_y) / resolution)
    values: list[int] = []
    for y in range(max(0, center_y - radius_cells), min(height, center_y + radius_cells + 1)):
        for x in range(max(0, center_x - radius_cells), min(width, center_x + radius_cells + 1)):
            world_x = origin_x + (x + 0.5) * resolution
            world_y = origin_y + (y + 0.5) * resolution
            if math.hypot(world_x - point.x, world_y - point.y) <= radius_m:
                values.append(int(costs[y * width + x]))
    return max(values) if values else -1


def count_costs_in_oriented_box(
    *,
    costs: Sequence[int],
    width: int,
    height: int,
    resolution: float,
    origin_x: float,
    origin_y: float,
    center: Pose3D,
    size: BoxSize,
    minimum_cost: int = 253,
) -> int:
    """Count high-cost cell centers inside a blocker's planar footprint."""

    if width <= 0 or height <= 0 or len(costs) != width * height:
        raise ValueError("costmap dimensions do not match data")
    if resolution <= 0.0:
        raise ValueError("resolution must be positive")
    center.validate()
    size.validate()
    cosine = math.cos(center.yaw)
    sine = math.sin(center.yaw)
    half_x = size.x / 2.0
    half_y = size.y / 2.0
    count = 0
    for y in range(height):
        world_y = origin_y + (y + 0.5) * resolution
        for x in range(width):
            world_x = origin_x + (x + 0.5) * resolution
            delta_x = world_x - center.x
            delta_y = world_y - center.y
            local_x = cosine * delta_x + sine * delta_y
            local_y = -sine * delta_x + cosine * delta_y
            if (
                abs(local_x) <= half_x
                and abs(local_y) <= half_y
                and int(costs[y * width + x]) >= minimum_cost
            ):
                count += 1
    return count


def terminal_failure_class(
    *, succeeded: bool, timed_out: bool, error_code: int
) -> str:
    """Classify Nav2 terminal state without conflating it with irreversibility."""

    if succeeded:
        return "succeeded"
    if timed_out:
        return "execution_timeout"
    if 200 <= error_code < 300:
        return "planning_failure"
    if 100 <= error_code < 200:
        return "controller_failure"
    return "navigation_failure_unattributed"


def planner_behavior_tree(planner_id: str) -> str:
    """Return a standard recovery BT with an explicit immutable planner ID."""

    if not planner_id:
        raise ValueError("planner ID must be non-empty")
    planner = escape(planner_id, {'"': "&quot;"})
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<root BTCPP_format="4" main_tree_to_execute="MainTree">
  <BehaviorTree ID="MainTree">
    <RecoveryNode number_of_retries="6" name="NavigateRecovery">
      <PipelineSequence name="NavigateWithReplanning">
        <ControllerSelector selected_controller="{{selected_controller}}"
          default_controller="FollowPath" topic_name="controller_selector"/>
        <RateController hz="1.0">
          <RecoveryNode number_of_retries="1" name="ComputePathToPose">
            <ComputePathToPose goal="{{goal}}" path="{{path}}"
              planner_id="{planner}" error_code_id="{{compute_path_error_code}}"/>
            <Sequence>
              <WouldAPlannerRecoveryHelp error_code="{{compute_path_error_code}}"/>
              <ClearEntireCostmap name="ClearGlobalCostmap-Context"
                service_name="global_costmap/clear_entirely_global_costmap"/>
            </Sequence>
          </RecoveryNode>
        </RateController>
        <RecoveryNode number_of_retries="1" name="FollowPath">
          <FollowPath path="{{path}}" controller_id="{{selected_controller}}"
            error_code_id="{{follow_path_error_code}}"/>
          <Sequence>
            <WouldAControllerRecoveryHelp error_code="{{follow_path_error_code}}"/>
            <ClearEntireCostmap name="ClearLocalCostmap-Context"
              service_name="local_costmap/clear_entirely_local_costmap"/>
          </Sequence>
        </RecoveryNode>
      </PipelineSequence>
      <Sequence>
        <Fallback>
          <WouldAControllerRecoveryHelp error_code="{{follow_path_error_code}}"/>
          <WouldAPlannerRecoveryHelp error_code="{{compute_path_error_code}}"/>
        </Fallback>
        <ReactiveFallback name="RecoveryFallback">
          <GoalUpdated/>
          <RoundRobin name="RecoveryActions">
            <Sequence name="ClearingActions">
              <ClearEntireCostmap name="ClearLocalCostmap-Subtree"
                service_name="local_costmap/clear_entirely_local_costmap"/>
              <ClearEntireCostmap name="ClearGlobalCostmap-Subtree"
                service_name="global_costmap/clear_entirely_global_costmap"/>
            </Sequence>
            <Spin spin_dist="1.57" error_code_id="{{spin_error_code}}"/>
            <Wait wait_duration="5.0"/>
            <BackUp backup_dist="0.30" backup_speed="0.15" error_code_id="{{backup_error_code}}"/>
          </RoundRobin>
        </ReactiveFallback>
      </Sequence>
    </RecoveryNode>
  </BehaviorTree>
</root>
"""
    ElementTree.fromstring(xml)
    return xml


def summarize_dynamic_trials(records: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Summarize valid dynamic trials while explicitly retaining invalid trials."""

    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        grouped.setdefault(str(record["planner_id"]), []).append(record)
    summary: dict[str, dict[str, Any]] = {}
    for planner_id, rows in sorted(grouped.items()):
        valid = [row for row in rows if row["valid_trial"]]
        assessed = [
            row
            for row in valid
            if row.get("operational_irreversible_failure") is not None
        ]
        successful = [row for row in valid if row["navigation_success"]]
        classes = Counter(str(row["terminal_failure_class"]) for row in valid)
        summary[planner_id] = {
            "trials": len(rows),
            "valid_trials": len(valid),
            "invalid_trials": len(rows) - len(valid),
            "navigation_success_rate": (
                len(successful) / len(valid) if valid else None
            ),
            "operational_irreversibility_assessed": len(assessed),
            "operational_irreversible_failure_rate": (
                sum(bool(row["operational_irreversible_failure"]) for row in assessed)
                / len(assessed)
                if assessed
                else None
            ),
            "terminal_failure_classes": dict(sorted(classes.items())),
            "simulation_duration_s_mean": (
                statistics.fmean(float(row["simulation_duration_s"]) for row in valid)
                if valid
                else None
            ),
            "recoveries_mean": (
                statistics.fmean(int(row["number_of_recoveries"]) for row in valid)
                if valid
                else None
            ),
        }
    return summary
