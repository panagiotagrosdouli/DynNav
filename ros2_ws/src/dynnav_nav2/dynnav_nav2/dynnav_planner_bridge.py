"""ROS 2 bridge node for DynNav planners."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

try:
    import rclpy
    from nav_msgs.msg import Path
    from rclpy.node import Node
    from std_msgs.msg import String
except ImportError:  # pragma: no cover
    rclpy = None
    Node = object
    String = None
    Path = None

from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.planners import GridMap, self_aware_astar
from dynnav.planners.commitment_aware_astar import (
    CommitmentAwareAStarConfig,
    CommitmentPlannerMode,
    commitment_aware_astar,
)
from .path_conversion import build_nav_path_message

GridCell = tuple[int, int]
DirectedTransition = tuple[GridCell, GridCell]


@dataclass(frozen=True)
class PlannerBridgeConfig:
    width: int
    height: int
    start: GridCell
    goal: GridCell
    obstacles: tuple[GridCell, ...]
    resolution_m: float = 1.0
    frame_id: str = "map"
    planner_mode: str = "self_aware"
    safe_cells: tuple[GridCell, ...] = ()
    commitment_hazards: tuple[CommitmentClosure, ...] = ()
    recoverability_weight: float = 4.0
    max_hazard_cells: int = 16


@dataclass(frozen=True)
class ExecutionHistory:
    """Online execution state retained across replanning calls."""

    current_cell: GridCell
    activated_hazards: frozenset[int] = frozenset()


def parse_cells(raw: str) -> tuple[GridCell, ...]:
    """Parse `x:y,x:y` cell strings into grid cells."""
    if not raw.strip():
        return ()
    cells = []
    for item in raw.split(","):
        x_str, y_str = item.strip().split(":", maxsplit=1)
        cells.append((int(x_str), int(y_str)))
    return tuple(cells)


def parse_transition(raw: str) -> DirectedTransition:
    """Parse a directed transition encoded as ``x:y>x:y``."""
    source_raw, target_raw = raw.strip().split(">", maxsplit=1)
    source = parse_cells(source_raw)
    target = parse_cells(target_raw)
    if len(source) != 1 or len(target) != 1:
        raise ValueError("transition endpoints must each contain one x:y cell")
    return source[0], target[0]


def parse_commitment_hazards(raw: str) -> tuple[CommitmentClosure, ...]:
    """Parse ``trigger@closure@probability`` hazards separated by semicolons.

    Example: ``1:1>2:1@0:1@0.8;3:1>4:1@2:1@0.4``.
    """
    if not raw.strip():
        return ()
    hazards: list[CommitmentClosure] = []
    for item in raw.split(";"):
        trigger_raw, closure_raw, probability_raw = item.strip().split("@", maxsplit=2)
        closure = parse_cells(closure_raw)
        if len(closure) != 1:
            raise ValueError("closure must contain exactly one x:y cell")
        hazards.append(
            CommitmentClosure(
                trigger=parse_transition(trigger_raw),
                closure_cell=closure[0],
                closure_probability=float(probability_raw),
            )
        )
    return tuple(hazards)


def advance_execution_history(
    history: ExecutionHistory,
    transition: DirectedTransition,
    model: CommitmentHazardModel,
) -> ExecutionHistory:
    """Advance online history after one observed robot transition.

    The source must match the retained current cell. This prevents dropped or
    out-of-order transition messages from silently corrupting hazard history.
    """
    source, target = transition
    if source != history.current_cell:
        raise ValueError(
            f"executed transition source {source} does not match current cell {history.current_cell}"
        )
    additions = {
        index
        for index, closure in enumerate(model.closures)
        if closure.trigger == transition
    }
    return ExecutionHistory(
        current_cell=target,
        activated_hazards=history.activated_hazards | frozenset(additions),
    )


def plan_grid_path(config: PlannerBridgeConfig) -> list[GridCell]:
    """Plan a path using the legacy research-core SelfAwareAStar implementation."""
    grid = GridMap.from_obstacles(width=config.width, height=config.height, obstacles=config.obstacles)
    result = self_aware_astar(grid, config.start, config.goal)
    return result.path if result.success else []


def plan_history_conditioned_grid_path(
    config: PlannerBridgeConfig,
    history: ExecutionHistory,
) -> tuple[list[GridCell], float, int]:
    """Plan from retained execution history using augmented-state A*."""
    grid = GridMap.from_obstacles(width=config.width, height=config.height, obstacles=config.obstacles)
    model = CommitmentHazardModel(config.commitment_hazards)
    safe_cells = set(config.safe_cells or (config.start,))
    result = commitment_aware_astar(
        grid,
        history.current_cell,
        config.goal,
        safe_cells=safe_cells,
        hazard_model=model,
        mode=CommitmentPlannerMode.HISTORY_AWARE,
        config=CommitmentAwareAStarConfig(
            recoverability_weight=config.recoverability_weight,
            max_hazard_cells=config.max_hazard_cells,
        ),
        initial_activated_closures=history.activated_hazards,
    )
    path = list(result.path) if result.success else []
    return path, result.minimum_return_probability, result.activated_closure_count


def format_path(path: Iterable[GridCell]) -> str:
    return " -> ".join(f"({x},{y})" for x, y in path)


class DynNavPlannerBridge(Node):  # type: ignore[misc]
    """ROS 2 node wrapping DynNav planners with optional persistent hazard history."""

    def __init__(self) -> None:
        super().__init__("dynnav_planner_bridge")
        self.declare_parameter("grid_width", 10)
        self.declare_parameter("grid_height", 10)
        self.declare_parameter("start", "0:0")
        self.declare_parameter("goal", "9:9")
        self.declare_parameter("obstacles", "")
        self.declare_parameter("resolution_m", 1.0)
        self.declare_parameter("frame_id", "map")
        self.declare_parameter("publish_period_s", 1.0)
        self.declare_parameter("planner_mode", "self_aware")
        self.declare_parameter("safe_cells", "")
        self.declare_parameter("commitment_hazards", "")
        self.declare_parameter("recoverability_weight", 4.0)
        self.declare_parameter("max_hazard_cells", 16)

        config = self.read_config()
        self.execution_history = ExecutionHistory(config.start)
        self.debug_publisher = self.create_publisher(String, "dynnav/planned_path", 10)
        self.path_publisher = self.create_publisher(Path, "dynnav/path", 10)
        self.history_publisher = self.create_publisher(String, "dynnav/history_state", 10)
        self.transition_subscription = self.create_subscription(
            String,
            "dynnav/executed_transition",
            self.executed_transition_callback,
            10,
        )
        self.timer = self.create_timer(float(self.get_parameter("publish_period_s").value), self.publish_plan_once)

    def read_config(self) -> PlannerBridgeConfig:
        start = parse_cells(str(self.get_parameter("start").value))
        goal = parse_cells(str(self.get_parameter("goal").value))
        if len(start) != 1 or len(goal) != 1:
            raise ValueError("start and goal parameters must each contain one x:y cell")
        return PlannerBridgeConfig(
            width=int(self.get_parameter("grid_width").value),
            height=int(self.get_parameter("grid_height").value),
            start=start[0],
            goal=goal[0],
            obstacles=parse_cells(str(self.get_parameter("obstacles").value)),
            resolution_m=float(self.get_parameter("resolution_m").value),
            frame_id=str(self.get_parameter("frame_id").value),
            planner_mode=str(self.get_parameter("planner_mode").value),
            safe_cells=parse_cells(str(self.get_parameter("safe_cells").value)),
            commitment_hazards=parse_commitment_hazards(
                str(self.get_parameter("commitment_hazards").value)
            ),
            recoverability_weight=float(self.get_parameter("recoverability_weight").value),
            max_hazard_cells=int(self.get_parameter("max_hazard_cells").value),
        )

    def executed_transition_callback(self, message: String) -> None:
        config = self.read_config()
        model = CommitmentHazardModel(config.commitment_hazards)
        try:
            self.execution_history = advance_execution_history(
                self.execution_history,
                parse_transition(message.data),
                model,
            )
        except ValueError as exc:
            self.get_logger().error(str(exc))
            return
        self.publish_plan_once()

    def publish_plan_once(self) -> None:
        config = self.read_config()
        if config.planner_mode == "history_aware":
            path, min_return, active_count = plan_history_conditioned_grid_path(
                config,
                self.execution_history,
            )
            diagnostics = f" min_return={min_return:.6f} active_hazards={active_count}"
        elif config.planner_mode == "self_aware":
            runtime_config = PlannerBridgeConfig(**{**config.__dict__, "start": self.execution_history.current_cell})
            path = plan_grid_path(runtime_config)
            diagnostics = ""
        else:
            raise ValueError(f"unsupported planner_mode: {config.planner_mode}")

        debug_message = String()
        debug_message.data = format_path(path) + diagnostics
        self.debug_publisher.publish(debug_message)
        self.path_publisher.publish(
            build_nav_path_message(path, frame_id=config.frame_id, resolution_m=config.resolution_m)
        )
        history_message = String()
        history_message.data = (
            f"cell={self.execution_history.current_cell[0]}:{self.execution_history.current_cell[1]} "
            f"activated={','.join(str(i) for i in sorted(self.execution_history.activated_hazards))}"
        )
        self.history_publisher.publish(history_message)


def main(args: list[str] | None = None) -> None:
    if rclpy is None:
        raise RuntimeError("ROS 2 dependencies are not installed")
    rclpy.init(args=args)
    node = DynNavPlannerBridge()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
