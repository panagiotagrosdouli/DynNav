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

from dynnav.planners import GridMap, self_aware_astar
from dynnav_nav2.path_conversion import build_nav_path_message


@dataclass(frozen=True)
class PlannerBridgeConfig:
    width: int
    height: int
    start: tuple[int, int]
    goal: tuple[int, int]
    obstacles: tuple[tuple[int, int], ...]
    resolution_m: float = 1.0
    frame_id: str = "map"


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
    grid = GridMap.from_obstacles(width=config.width, height=config.height, obstacles=config.obstacles)
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
        self.declare_parameter("resolution_m", 1.0)
        self.declare_parameter("frame_id", "map")
        self.declare_parameter("publish_period_s", 1.0)

        self.debug_publisher = self.create_publisher(String, "dynnav/planned_path", 10)
        self.path_publisher = self.create_publisher(Path, "dynnav/path", 10)
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
        )

    def publish_plan_once(self) -> None:
        config = self.read_config()
        path = plan_grid_path(config)
        debug_msg = String()
        debug_msg.data = format_path(path) if path else "NO_PATH"
        self.debug_publisher.publish(debug_msg)
        if path:
            self.path_publisher.publish(build_nav_path_message(path, config.frame_id, config.resolution_m, self.get_clock().now().to_msg()))
        self.get_logger().info(f"DynNav planned path: {debug_msg.data}")


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
