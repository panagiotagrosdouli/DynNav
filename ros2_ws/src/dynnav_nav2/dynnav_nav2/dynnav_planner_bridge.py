"""ROS 2 bridge node for DynNav planners."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

try:
    import rclpy
    from nav_msgs.msg import OccupancyGrid, Path
    from rclpy.node import Node
    from std_msgs.msg import String
except ImportError:  # pragma: no cover
    rclpy = None
    Node = object
    String = None
    Path = None
    OccupancyGrid = None

from dynnav_nav2.live_map_planning import LiveMapPlanningConfig, plan_with_optional_live_grid
from dynnav_nav2.occupancy_grid_conversion import occupancy_grid_msg_to_spec, occupancy_grid_spec_to_grid_map
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
    use_live_map: bool = True
    occupied_threshold: int = 65
    unknown_is_obstacle: bool = False


def parse_cells(raw: str) -> tuple[tuple[int, int], ...]:
    if not raw.strip():
        return ()
    cells = []
    for item in raw.split(","):
        x_str, y_str = item.strip().split(":", maxsplit=1)
        cells.append((int(x_str), int(y_str)))
    return tuple(cells)


def planning_config_from_bridge(config: PlannerBridgeConfig) -> LiveMapPlanningConfig:
    return LiveMapPlanningConfig(
        start=config.start,
        goal=config.goal,
        fallback_width=config.width,
        fallback_height=config.height,
        fallback_obstacles=config.obstacles,
        use_live_map=config.use_live_map,
    )


def plan_grid_path(config: PlannerBridgeConfig, live_grid=None) -> list[tuple[int, int]]:
    return plan_with_optional_live_grid(planning_config_from_bridge(config), live_grid)


def format_path(path: Iterable[tuple[int, int]]) -> str:
    return " -> ".join(f"({x},{y})" for x, y in path)


class DynNavPlannerBridge(Node):  # type: ignore[misc]
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
        self.declare_parameter("use_live_map", True)
        self.declare_parameter("map_topic", "/map")
        self.declare_parameter("occupied_threshold", 65)
        self.declare_parameter("unknown_is_obstacle", False)

        self.latest_grid = None
        self.debug_publisher = self.create_publisher(String, "dynnav/planned_path", 10)
        self.path_publisher = self.create_publisher(Path, "dynnav/path", 10)
        self.map_subscription = self.create_subscription(
            OccupancyGrid,
            str(self.get_parameter("map_topic").value),
            self.on_map,
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
            use_live_map=bool(self.get_parameter("use_live_map").value),
            occupied_threshold=int(self.get_parameter("occupied_threshold").value),
            unknown_is_obstacle=bool(self.get_parameter("unknown_is_obstacle").value),
        )

    def on_map(self, msg) -> None:
        config = self.read_config()
        spec = occupancy_grid_msg_to_spec(
            msg,
            occupied_threshold=config.occupied_threshold,
            unknown_is_obstacle=config.unknown_is_obstacle,
        )
        self.latest_grid = occupancy_grid_spec_to_grid_map(spec)
        self.get_logger().info("DynNav received live OccupancyGrid map")

    def publish_plan_once(self) -> None:
        config = self.read_config()
        path = plan_grid_path(config, self.latest_grid)
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
