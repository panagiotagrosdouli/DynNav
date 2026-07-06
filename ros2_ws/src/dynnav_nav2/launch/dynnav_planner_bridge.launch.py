from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from pathlib import Path


def generate_launch_description():
    package_share = Path(get_package_share_directory("dynnav_nav2"))
    config_path = package_share / "config" / "dynnav_planner_bridge.yaml"

    return LaunchDescription(
        [
            Node(
                package="dynnav_nav2",
                executable="dynnav_planner_bridge",
                name="dynnav_planner_bridge",
                output="screen",
                parameters=[str(config_path)],
            )
        ]
    )
