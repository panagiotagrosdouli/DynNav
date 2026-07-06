"""ROS 2 bridge node for DynNav planners.

This node is a scaffold: it exposes ROS 2 parameters and basic publishers so the
research planner core can later be connected to Nav2 actions/plugins without
entangling the pure-Python algorithms with ROS-specific message types.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import String
except ImportError:  # pragma: no cover - allows non-ROS unit imports
    rclpy = None
    Node = object
    String = None

from dynnav.planners import GridMap, self_aware_astar


@dataclass(frozen=True)
class PlannerBridgeConfig:
    width: int
    height: int
    start: tuple[int, int]
    goal: tuple[int, int]
    obstacles: tuple[tuple[int, int], ...]


def parse_cells(raw: str) -> tuple[tuple[int, int], ...]:
    """Parse `x:y,x:y` cell strings into grid cells."""
    if not raw.strip():
        return ()
    cells = []
    for item in raw.split(","):
        x_str, y_str = item.strip().split(":", maxsplit=1)
        cells.append((int(x_str), int(y_str)))
    return tuple(cells)


def plan_grid_path(config: PlannerBridgeConfig) -> list[tuple[int, int]]:
    """Plan a path using the research-core SelfAwareAStar implementation."""
    grid = GridMap.from_obstacles(
        width=config.width,
        height=config.height,
        obstacles=config.obstacles,
    )
    result = self_aware_astar(grid, config.start, config.goal)
    return result.path if result.success else []


def format_path(path: Iterable[tuple[int, int]]) -> str:
    return " -> ".join(f"({x},{y})" for x, y in path)


class DynNavPlannerBridge(Node):  # type: ignore[misc]
    """Minimal ROS 2 node wrapping the DynNav planner core."""

    def __init__(self) -> None:
        super().__init__("dynnav_planner_bridge")
        self.declare_parameter("grid_width", 10)
        self.declare_parameter("grid_height", 10)
        self.declare_parameter("start", "0:0")
        self.declare_parameter("goal", "9:9")
        self.declare_parameter("obstacles", "")
        self.declare_parameter("publish_period_s", 1.0)

        self.publisher = self.create_publisher(String, "dynnav/planned_path", 10)
        period = float(self.get_parameter("publish_period_s").value)
        self.timer = self.create_timer(period, self.publish_plan_once)

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
        )

    def publish_plan_once(self) -> None:
        config = self.read_config()
        path = plan_grid_path(config)
        msg = String()
        msg.data = format_path(path) if path else "NO_PATH"
        self.publisher.publish(msg)
        self.get_logger().info(f"DynNav planned path: {msg.data}")


def main(args=None) -> None:
    if rclpy is None:
        raise RuntimeError("rclpy is required to run the DynNav ROS 2 bridge")
    rclpy.init(args=args)
    node = DynNavPlannerBridge()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
