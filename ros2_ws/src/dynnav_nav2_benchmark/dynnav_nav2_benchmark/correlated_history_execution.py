"""ROS-independent configuration contracts for two-hazard dependence execution."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from dynnav_nav2_benchmark.analysis import Pose2D
from dynnav_nav2_benchmark.dynamic_analysis import Pose3D, SafeRegion
from dynnav_nav2_benchmark.history_execution import (
    ActionTriggerSpec,
    transition_from_world_trigger,
)


@dataclass(frozen=True, slots=True)
class CorrelatedExecutionHazard:
    trigger: ActionTriggerSpec
    blocker_entity: str
    blocker_pose: Pose3D

    def validate(self) -> None:
        self.trigger.validate()
        self.blocker_pose.validate()
        if not self.blocker_entity:
            raise ValueError("blocker_entity cannot be empty")


@dataclass(frozen=True, slots=True)
class CorrelatedHistoryScenario:
    name: str
    frame_id: str
    start: Pose2D
    goal: Pose2D
    safe_region: SafeRegion
    hazards: tuple[CorrelatedExecutionHazard, CorrelatedExecutionHazard]
    dependence_conditions: tuple[str, ...]
    pairwise_joint_lower: float
    pairwise_joint_upper: float
    recoverability_weight: float
    minimum_injection_clearance_m: float
    recovery_budget_m: float
    reset_pose_tolerance_m: float
    execution_timeout_s: float
    wall_timeout_s: float

    def validate(self) -> None:
        if not self.name or not self.frame_id:
            raise ValueError("scenario name/frame cannot be empty")
        self.start.validate()
        self.goal.validate()
        self.safe_region.validate()
        if len(self.hazards) != 2:
            raise ValueError("correlated scenario requires exactly two hazards")
        for hazard in self.hazards:
            hazard.validate()
        if self.hazards[0].trigger.hazard_id == self.hazards[1].trigger.hazard_id:
            raise ValueError("hazard IDs must be unique")
        if self.hazards[0].blocker_entity == self.hazards[1].blocker_entity:
            raise ValueError("blocker entities must be unique")
        allowed = {"independent", "common_cause", "anti_correlated"}
        if not self.dependence_conditions:
            raise ValueError("at least one dependence condition is required")
        if any(item not in allowed for item in self.dependence_conditions):
            raise ValueError("unsupported dependence condition")
        probabilities = {
            round(hazard.trigger.closure_probability, 12)
            for hazard in self.hazards
        }
        if len(probabilities) != 1:
            raise ValueError("current paired benchmark requires equal hazard marginals")
        if "anti_correlated" in self.dependence_conditions:
            p = self.hazards[0].trigger.closure_probability
            if abs(p - 0.5) > 1.0e-12:
                raise ValueError("anti_correlated condition requires closure_probability=0.5")
        if not 0.0 <= self.pairwise_joint_lower <= self.pairwise_joint_upper <= 1.0:
            raise ValueError("invalid pairwise joint ambiguity interval")
        for value in (
            self.recoverability_weight,
            self.minimum_injection_clearance_m,
            self.recovery_budget_m,
            self.reset_pose_tolerance_m,
            self.execution_timeout_s,
            self.wall_timeout_s,
        ):
            if not math.isfinite(value) or value < 0.0:
                raise ValueError("scenario numeric values must be finite/non-negative")
        if self.execution_timeout_s <= 0.0 or self.wall_timeout_s < self.execution_timeout_s:
            raise ValueError("invalid execution/wall timeout")


@dataclass(frozen=True, slots=True)
class CorrelatedHistoryExecutionSuite:
    schema_version: int
    seed: int
    world_name: str
    robot_entity: str
    blocker_parking_pose: Pose3D
    blocker_size: tuple[float, float, float]
    planner_ids: tuple[str, ...]
    scenario: CorrelatedHistoryScenario

    def validate(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported correlated history schema")
        if not self.world_name or not self.robot_entity:
            raise ValueError("Gazebo identifiers cannot be empty")
        if not self.planner_ids or len(set(self.planner_ids)) != len(self.planner_ids):
            raise ValueError("planner IDs must be non-empty and unique")
        if any(not math.isfinite(v) or v <= 0.0 for v in self.blocker_size):
            raise ValueError("blocker size must be finite and positive")
        self.blocker_parking_pose.validate()
        self.scenario.validate()


def _pose2(payload: dict[str, Any]) -> Pose2D:
    return Pose2D(
        float(payload["x"]),
        float(payload["y"]),
        float(payload.get("yaw", 0.0)),
    )


def _pose3(payload: dict[str, Any]) -> Pose3D:
    return Pose3D(
        float(payload["x"]),
        float(payload["y"]),
        float(payload.get("z", 0.0)),
        float(payload.get("yaw", 0.0)),
    )


def load_correlated_history_execution_suite(
    path: str | Path,
) -> CorrelatedHistoryExecutionSuite:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("correlated history suite must be a YAML mapping")
    gazebo = payload["gazebo"]
    blocker = gazebo["blocker"]
    item = payload["scenario"]
    safe = item["safe_region"]

    hazards = []
    for raw in item["hazards"]:
        trigger = raw["action_trigger"]
        hazards.append(
            CorrelatedExecutionHazard(
                trigger=ActionTriggerSpec(
                    hazard_id=str(trigger["hazard_id"]),
                    source=_pose2(trigger["source"]),
                    target=_pose2(trigger["target"]),
                    closure_probability=float(trigger["closure_probability"]),
                ),
                blocker_entity=str(raw["blocker_entity"]),
                blocker_pose=_pose3(raw["blocker_pose"]),
            )
        )
    if len(hazards) != 2:
        raise ValueError("configuration must contain exactly two hazards")

    suite = CorrelatedHistoryExecutionSuite(
        schema_version=int(payload.get("schema_version", 0)),
        seed=int(payload["seed"]),
        world_name=str(gazebo["world_name"]),
        robot_entity=str(gazebo["robot_entity"]),
        blocker_parking_pose=_pose3(blocker["parking_pose"]),
        blocker_size=(
            float(blocker["size"]["x"]),
            float(blocker["size"]["y"]),
            float(blocker["size"]["z"]),
        ),
        planner_ids=tuple(str(value) for value in payload["planners"]),
        scenario=CorrelatedHistoryScenario(
            name=str(item["name"]),
            frame_id=str(item.get("frame_id", "map")),
            start=_pose2(item["start"]),
            goal=_pose2(item["goal"]),
            safe_region=SafeRegion(_pose2(safe["center"]), float(safe["radius_m"])),
            hazards=(hazards[0], hazards[1]),
            dependence_conditions=tuple(str(value) for value in item["dependence_conditions"]),
            pairwise_joint_lower=float(item["pairwise_joint_lower"]),
            pairwise_joint_upper=float(item["pairwise_joint_upper"]),
            recoverability_weight=float(item["recoverability_weight"]),
            minimum_injection_clearance_m=float(item["minimum_injection_clearance_m"]),
            recovery_budget_m=float(item["recovery_budget_m"]),
            reset_pose_tolerance_m=float(item["reset_pose_tolerance_m"]),
            execution_timeout_s=float(item["execution_timeout_s"]),
            wall_timeout_s=float(item["wall_timeout_s"]),
        ),
    )
    suite.validate()
    return suite


def quantized_hazard_transitions(
    suite: CorrelatedHistoryExecutionSuite,
    *,
    origin_x: float,
    origin_y: float,
    resolution: float,
) -> tuple[
    tuple[tuple[int, int], tuple[int, int]],
    tuple[tuple[int, int], tuple[int, int]],
]:
    return (
        transition_from_world_trigger(
            suite.scenario.hazards[0].trigger,
            origin_x=origin_x,
            origin_y=origin_y,
            resolution=resolution,
        ),
        transition_from_world_trigger(
            suite.scenario.hazards[1].trigger,
            origin_x=origin_x,
            origin_y=origin_y,
            resolution=resolution,
        ),
    )


def blocker_footprint_cells(
    *,
    center: Pose3D,
    size_xy: tuple[float, float],
    origin_x: float,
    origin_y: float,
    resolution: float,
) -> tuple[tuple[int, int], ...]:
    """Rasterize an axis-aligned physical blocker into map cells.

    The v2 canonical environment uses yaw=0 blockers, so the footprint can be
    represented exactly as an axis-aligned rectangle on the planning grid.
    """

    if resolution <= 0.0 or not math.isfinite(resolution):
        raise ValueError("resolution must be finite and positive")
    size_x, size_y = size_xy
    if size_x <= 0.0 or size_y <= 0.0:
        raise ValueError("blocker footprint dimensions must be positive")
    if abs(center.yaw) > 1.0e-12:
        raise ValueError("footprint rasterization currently requires blocker yaw=0")

    min_x = math.floor((center.x - size_x / 2.0 - origin_x) / resolution)
    max_x = math.floor((center.x + size_x / 2.0 - origin_x) / resolution)
    min_y = math.floor((center.y - size_y / 2.0 - origin_y) / resolution)
    max_y = math.floor((center.y + size_y / 2.0 - origin_y) / resolution)
    cells = tuple(
        (x, y)
        for y in range(min_y, max_y + 1)
        for x in range(min_x, max_x + 1)
    )
    if not cells:
        raise ValueError("blocker footprint rasterized to no cells")
    return cells
