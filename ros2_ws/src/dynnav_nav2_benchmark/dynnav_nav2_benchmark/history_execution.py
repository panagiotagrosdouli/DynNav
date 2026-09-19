"""ROS-independent contracts for action-triggered history validation."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml

from dynnav_nav2_benchmark.analysis import Pose2D
from dynnav_nav2_benchmark.dynamic_analysis import Pose3D, SafeRegion

GridCell = tuple[int, int]
DirectedTransition = tuple[GridCell, GridCell]
ObservationKind = Literal["same_cell", "adjacent_transition", "sampling_gap"]


@dataclass(frozen=True, slots=True)
class ActionTriggerSpec:
    hazard_id: str
    source: Pose2D
    target: Pose2D
    closure_probability: float

    def validate(self) -> None:
        if not self.hazard_id:
            raise ValueError("hazard_id must be non-empty")
        self.source.validate()
        self.target.validate()
        if math.hypot(self.target.x - self.source.x, self.target.y - self.source.y) <= 0.0:
            raise ValueError("action trigger source and target must differ")
        if not math.isfinite(self.closure_probability) or not 0.0 <= self.closure_probability <= 1.0:
            raise ValueError("closure_probability must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class HistoryScenarioSpec:
    name: str
    start: Pose2D
    goal: Pose2D
    safe_region: SafeRegion
    trigger: ActionTriggerSpec
    blocker_pose: Pose3D
    observation_settle_s: float
    minimum_injection_clearance_m: float
    observation_margin_m: float
    minimum_lethal_cell_increase: int
    recovery_budget_m: float
    reset_pose_tolerance_m: float
    execution_timeout_s: float
    wall_timeout_s: float
    recoverability_weight: float = 4.0
    frame_id: str = "map"

    def validate(self) -> None:
        if not self.name or not self.frame_id:
            raise ValueError("scenario name and frame must be non-empty")
        self.start.validate()
        self.goal.validate()
        self.safe_region.validate()
        self.trigger.validate()
        self.blocker_pose.validate()
        for value in (
            self.observation_settle_s,
            self.minimum_injection_clearance_m,
            self.observation_margin_m,
            self.recovery_budget_m,
            self.reset_pose_tolerance_m,
            self.execution_timeout_s,
            self.wall_timeout_s,
            self.recoverability_weight,
        ):
            if not math.isfinite(value) or value < 0.0:
                raise ValueError("history scenario numeric values must be finite and non-negative")
        if self.minimum_lethal_cell_increase <= 0:
            raise ValueError("minimum_lethal_cell_increase must be positive")
        if self.execution_timeout_s <= 0.0 or self.wall_timeout_s < self.execution_timeout_s:
            raise ValueError("invalid execution/wall timeout")


@dataclass(frozen=True, slots=True)
class HistoryExecutionSuite:
    schema_version: int
    seed: int
    world_name: str
    robot_entity: str
    blocker_entity: str
    blocker_parking_pose: Pose3D
    blocker_size: tuple[float, float, float]
    planner_ids: tuple[str, ...]
    scenario: HistoryScenarioSpec

    def validate(self) -> None:
        if self.schema_version != 1:
            raise ValueError(f"unsupported history execution schema: {self.schema_version}")
        if not self.world_name or not self.robot_entity or not self.blocker_entity:
            raise ValueError("Gazebo identifiers must be non-empty")
        if not self.planner_ids or len(set(self.planner_ids)) != len(self.planner_ids):
            raise ValueError("planner IDs must be non-empty and unique")
        if any(not math.isfinite(v) or v <= 0.0 for v in self.blocker_size):
            raise ValueError("blocker size must be finite and positive")
        self.blocker_parking_pose.validate()
        self.scenario.validate()


@dataclass(frozen=True, slots=True)
class ObservedTransition:
    source: GridCell
    target: GridCell
    kind: ObservationKind

    @property
    def accepted(self) -> bool:
        return self.kind == "adjacent_transition"

    @property
    def transition(self) -> DirectedTransition | None:
        if not self.accepted:
            return None
        return self.source, self.target


@dataclass(frozen=True, slots=True)
class TriggerDecision:
    trigger_observed: bool
    closure_realized: bool
    event_should_apply: bool
    outcome: str


def _pose2(payload: dict[str, Any]) -> Pose2D:
    return Pose2D(float(payload["x"]), float(payload["y"]), float(payload.get("yaw", 0.0)))


def _pose3(payload: dict[str, Any]) -> Pose3D:
    return Pose3D(
        float(payload["x"]), float(payload["y"]), float(payload.get("z", 0.0)), float(payload.get("yaw", 0.0))
    )


def load_history_execution_suite(path: str | Path) -> HistoryExecutionSuite:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("history execution suite must be a YAML mapping")
    gazebo = payload["gazebo"]
    blocker = gazebo["blocker"]
    item = payload["scenario"]
    safe_payload = item["safe_region"]
    trigger_payload = item["action_trigger"]
    suite = HistoryExecutionSuite(
        schema_version=int(payload.get("schema_version", 0)),
        seed=int(payload["seed"]),
        world_name=str(gazebo["world_name"]),
        robot_entity=str(gazebo["robot_entity"]),
        blocker_entity=str(blocker["entity_name"]),
        blocker_parking_pose=_pose3(blocker["parking_pose"]),
        blocker_size=(float(blocker["size"]["x"]), float(blocker["size"]["y"]), float(blocker["size"]["z"])),
        planner_ids=tuple(str(value) for value in payload["planners"]),
        scenario=HistoryScenarioSpec(
            name=str(item["name"]),
            frame_id=str(item.get("frame_id", "map")),
            start=_pose2(item["start"]),
            goal=_pose2(item["goal"]),
            safe_region=SafeRegion(_pose2(safe_payload["center"]), float(safe_payload["radius_m"])),
            trigger=ActionTriggerSpec(
                hazard_id=str(trigger_payload["hazard_id"]),
                source=_pose2(trigger_payload["source"]),
                target=_pose2(trigger_payload["target"]),
                closure_probability=float(trigger_payload["closure_probability"]),
            ),
            blocker_pose=_pose3(item["blocker_pose"]),
            observation_settle_s=float(item["observation_settle_s"]),
            minimum_injection_clearance_m=float(item["minimum_injection_clearance_m"]),
            observation_margin_m=float(item["observation_margin_m"]),
            minimum_lethal_cell_increase=int(item["minimum_lethal_cell_increase"]),
            recovery_budget_m=float(item["recovery_budget_m"]),
            reset_pose_tolerance_m=float(item["reset_pose_tolerance_m"]),
            execution_timeout_s=float(item["execution_timeout_s"]),
            wall_timeout_s=float(item["wall_timeout_s"]),
            recoverability_weight=float(item.get("recoverability_weight", 4.0)),
        ),
    )
    suite.validate()
    return suite


def world_to_cell(pose: Pose2D, *, origin_x: float, origin_y: float, resolution: float) -> GridCell:
    if not math.isfinite(resolution) or resolution <= 0.0:
        raise ValueError("resolution must be finite and positive")
    return (math.floor((pose.x - origin_x) / resolution), math.floor((pose.y - origin_y) / resolution))


def transition_from_world_trigger(
    trigger: ActionTriggerSpec, *, origin_x: float, origin_y: float, resolution: float
) -> DirectedTransition:
    source = world_to_cell(trigger.source, origin_x=origin_x, origin_y=origin_y, resolution=resolution)
    target = world_to_cell(trigger.target, origin_x=origin_x, origin_y=origin_y, resolution=resolution)
    if abs(source[0] - target[0]) + abs(source[1] - target[1]) != 1:
        raise ValueError(f"quantized action trigger is not 4-connected: {source}>{target}")
    return source, target


def classify_observed_cells(source: GridCell, target: GridCell) -> ObservedTransition:
    """Classify observations; only genuine 4-connected moves are transitions."""
    if source == target:
        return ObservedTransition(source, target, "same_cell")
    dx = abs(target[0] - source[0])
    dy = abs(target[1] - source[1])
    if dx + dy == 1:
        return ObservedTransition(source, target, "adjacent_transition")
    return ObservedTransition(source, target, "sampling_gap")


def trigger_decision(
    *, observed: DirectedTransition | None, trigger: DirectedTransition, latent_draw: float, closure_probability: float
) -> TriggerDecision:
    """Resolve a frozen latent draw after observing an executed transition."""
    if not 0.0 <= latent_draw < 1.0:
        raise ValueError("latent_draw must be in [0, 1)")
    if not 0.0 <= closure_probability <= 1.0:
        raise ValueError("closure_probability must be in [0, 1]")
    trigger_observed = observed == trigger
    closure_realized = latent_draw < closure_probability
    event_should_apply = trigger_observed and closure_realized
    if not trigger_observed:
        outcome = "trigger_avoided"
    elif closure_realized:
        outcome = "closure_should_apply"
    else:
        outcome = "trigger_observed_no_closure"
    return TriggerDecision(
        trigger_observed=trigger_observed,
        closure_realized=closure_realized,
        event_should_apply=event_should_apply,
        outcome=outcome,
    )


def deterministic_event_draw(seed: int, scenario: str, repetition: int, hazard_id: str) -> float:
    """Stable event-index draw shared across planner conditions."""
    payload = f"{seed}|{scenario}|{repetition}|{hazard_id}".encode()
    integer = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
    return integer / float(1 << 64)


def transition_text(transition: DirectedTransition) -> str:
    (sx, sy), (tx, ty) = transition
    return f"{sx}:{sy}>{tx}:{ty}"
