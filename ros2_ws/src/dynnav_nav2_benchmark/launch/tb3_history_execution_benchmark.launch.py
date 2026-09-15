"""Launch the frozen action-triggered history benchmark in Gazebo/Nav2."""

from __future__ import annotations

from pathlib import Path

import yaml
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node

from dynnav_nav2_benchmark.configuration import inject_history_planner_parameters
from dynnav_nav2_benchmark.history_execution import (
    load_history_execution_suite,
    transition_from_world_trigger,
    world_to_cell,
)
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    EmitEvent,
    IncludeLaunchDescription,
    OpaqueFunction,
    RegisterEventHandler,
    TimerAction,
)
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def _launch_setup(context):
    base_params = Path(LaunchConfiguration("base_params_file").perform(context))
    generated_params = Path(
        LaunchConfiguration("generated_params_file").perform(context)
    )
    scenario_path = Path(LaunchConfiguration("scenario_file").perform(context))
    map_file = Path(LaunchConfiguration("map_file").perform(context))
    blocker_sdf = LaunchConfiguration("blocker_sdf").perform(context)
    output = LaunchConfiguration("output_dir").perform(context)
    repetitions = LaunchConfiguration("repetitions").perform(context)
    headless_requested = LaunchConfiguration("headless").perform(context)
    headless = (
        "True"
        if headless_requested.lower() in {"1", "true", "yes", "on"}
        else "False"
    )

    suite = load_history_execution_suite(scenario_path)
    scenario = suite.scenario
    map_payload = yaml.safe_load(map_file.read_text(encoding="utf-8"))
    resolution = float(map_payload["resolution"])
    origin_x = float(map_payload["origin"][0])
    origin_y = float(map_payload["origin"][1])
    trigger = transition_from_world_trigger(
        scenario.trigger,
        origin_x=origin_x,
        origin_y=origin_y,
        resolution=resolution,
    )
    safe_cell = world_to_cell(
        scenario.safe_region.center,
        origin_x=origin_x,
        origin_y=origin_y,
        resolution=resolution,
    )
    # The physical blocker pose is the frozen closure location. Derive the
    # planner's grid-cell representation from the same world-space source so
    # the execution and planning configurations cannot silently diverge.
    closure_cell = world_to_cell(
        Pose2D(
            scenario.blocker_pose.x,
            scenario.blocker_pose.y,
            scenario.blocker_pose.yaw,
        ),
        origin_x=origin_x,
        origin_y=origin_y,
        resolution=resolution,
    )

    payload = yaml.safe_load(base_params.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"invalid Nav2 parameter file: {base_params}")
    payload = inject_history_planner_parameters(
        payload,
        safe_cell=safe_cell,
        trigger=trigger,
        closure_cell=closure_cell,
        closure_probability=scenario.trigger.closure_probability,
        recoverability_weight=scenario.recoverability_weight,
    )
    generated_params.parent.mkdir(parents=True, exist_ok=True)
    generated_params.write_text(
        yaml.safe_dump(payload, sort_keys=False), encoding="utf-8"
    )

    nav2_launch = Path(get_package_share_directory("nav2_bringup")) / "launch"
    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(str(nav2_launch / "tb3_simulation_launch.py")),
        launch_arguments={
            "params_file": str(generated_params),
            "map": str(map_file),
            "robot_name": suite.robot_entity,
            "headless": headless,
            "use_rviz": "False",
            "use_simulator": "True",
            "use_composition": "False",
            "autostart": "True",
            "use_sim_time": "True",
        }.items(),
    )
    gazebo_services = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="dynnav_history_gazebo_service_bridge",
        output="screen",
        arguments=[
            f"/world/{suite.world_name}/create@ros_gz_interfaces/srv/SpawnEntity",
            f"/world/{suite.world_name}/set_pose@ros_gz_interfaces/srv/SetEntityPose",
        ],
    )
    runner = Node(
        package="dynnav_nav2_benchmark",
        executable="history_dynamic_execution_benchmark",
        name="dynnav_history_execution_benchmark",
        output="screen",
        arguments=[
            "--scenario", str(scenario_path),
            "--blocker-sdf", blocker_sdf,
            "--output", output,
            "--repetitions", repetitions,
        ],
    )
    delayed_runner = TimerAction(period=10.0, actions=[runner])
    shutdown = RegisterEventHandler(
        OnProcessExit(
            target_action=runner,
            on_exit=[EmitEvent(event=Shutdown(reason="history benchmark completed"))],
        )
    )
    return [simulation, gazebo_services, delayed_runner, shutdown]


def generate_launch_description() -> LaunchDescription:
    benchmark_share = Path(get_package_share_directory("dynnav_nav2_benchmark"))
    nav2_share = Path(get_package_share_directory("nav2_bringup"))
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "base_params_file",
                default_value=str(nav2_share / "params" / "nav2_params.yaml"),
            ),
            DeclareLaunchArgument(
                "generated_params_file",
                default_value="/tmp/dynnav_history_nav2_params.yaml",
            ),
            DeclareLaunchArgument(
                "scenario_file",
                default_value=str(
                    benchmark_share
                    / "config"
                    / "sandbox_history_triggered_events.yaml"
                ),
            ),
            DeclareLaunchArgument(
                "map_file",
                default_value=str(nav2_share / "maps" / "tb3_sandbox.yaml"),
            ),
            DeclareLaunchArgument(
                "blocker_sdf",
                default_value=str(benchmark_share / "models" / "dynamic_blocker.sdf"),
            ),
            DeclareLaunchArgument(
                "output_dir", default_value="/tmp/dynnav_history_benchmark"
            ),
            DeclareLaunchArgument("repetitions", default_value="1"),
            DeclareLaunchArgument("headless", default_value="true"),
            OpaqueFunction(function=_launch_setup),
        ]
    )
