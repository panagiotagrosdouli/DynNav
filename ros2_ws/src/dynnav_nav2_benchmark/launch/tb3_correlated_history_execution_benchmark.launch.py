"""Launch the two-hazard dependence-aware Gazebo/Nav2 benchmark."""

from __future__ import annotations

from pathlib import Path

import yaml
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node

from dynnav_nav2_benchmark.configuration import (
    inject_correlated_history_planner_parameters,
)
from dynnav_nav2_benchmark.correlated_history_execution import (
    blocker_footprint_cells,
    load_correlated_history_execution_suite,
    quantized_hazard_trigger_gates,
    quantized_hazard_transitions,
)
from dynnav_nav2_benchmark.history_execution import world_to_cell
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
    world_file = LaunchConfiguration("world_file").perform(context)
    output = LaunchConfiguration("output_dir").perform(context)
    repetitions = LaunchConfiguration("repetitions").perform(context)
    headless_requested = LaunchConfiguration("headless").perform(context)
    headless = (
        "True"
        if headless_requested.lower() in {"1", "true", "yes", "on"}
        else "False"
    )

    suite = load_correlated_history_execution_suite(scenario_path)
    scenario = suite.scenario
    map_payload = yaml.safe_load(map_file.read_text(encoding="utf-8"))
    resolution = float(map_payload["resolution"])
    origin_x = float(map_payload["origin"][0])
    origin_y = float(map_payload["origin"][1])

    triggers = quantized_hazard_transitions(
        suite,
        origin_x=origin_x,
        origin_y=origin_y,
        resolution=resolution,
    )
    trigger_gates = quantized_hazard_trigger_gates(
        suite,
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
    hazards = tuple(
        (
            trigger_gates[index],
            blocker_footprint_cells(
                center=hazard.blocker_pose,
                size_xy=(suite.blocker_size[0], suite.blocker_size[1]),
                origin_x=origin_x,
                origin_y=origin_y,
                resolution=resolution,
            ),
            hazard.trigger.closure_probability,
        )
        for index, hazard in enumerate(scenario.hazards)
    )

    payload = yaml.safe_load(base_params.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"invalid Nav2 parameter file: {base_params}")
    payload = inject_correlated_history_planner_parameters(
        payload,
        safe_cell=safe_cell,
        hazards=hazards,
        recoverability_weight=scenario.recoverability_weight,
        pairwise_joint_lower=scenario.pairwise_joint_lower,
        pairwise_joint_upper=scenario.pairwise_joint_upper,
    )
    generated_params.parent.mkdir(parents=True, exist_ok=True)
    generated_params.write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )

    nav2_launch = Path(get_package_share_directory("nav2_bringup")) / "launch"
    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(str(nav2_launch / "tb3_simulation_launch.py")),
        launch_arguments={
            "params_file": str(generated_params),
            "map": str(map_file),
            "world": world_file,
            "robot_name": suite.robot_entity,
            "x_pose": str(scenario.start.x),
            "y_pose": str(scenario.start.y),
            "yaw": str(scenario.start.yaw),
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
        name="dynnav_correlated_history_gazebo_service_bridge",
        output="screen",
        arguments=[
            f"/world/{suite.world_name}/create@ros_gz_interfaces/srv/SpawnEntity",
            f"/world/{suite.world_name}/set_pose@ros_gz_interfaces/srv/SetEntityPose",
        ],
    )
    runner = Node(
        package="dynnav_nav2_benchmark",
        executable="correlated_history_dynamic_execution_benchmark",
        name="dynnav_correlated_history_execution_benchmark",
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
            on_exit=[
                EmitEvent(event=Shutdown(reason="correlated history benchmark completed"))
            ],
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
                default_value="/tmp/dynnav_correlated_history_nav2_params.yaml",
            ),
            DeclareLaunchArgument(
                "scenario_file",
                default_value=str(
                    benchmark_share
                    / "config"
                    / "sandbox_correlated_history_events.yaml"
                ),
            ),
            DeclareLaunchArgument(
                "map_file",
                default_value=str(
                    benchmark_share / "maps" / "g1_parallel_corridor.yaml"
                ),
            ),
            DeclareLaunchArgument(
                "world_file",
                default_value=str(
                    benchmark_share / "worlds" / "g1_parallel_corridor.sdf.xacro"
                ),
            ),
            DeclareLaunchArgument(
                "blocker_sdf",
                default_value=str(
                    benchmark_share / "models" / "g1_parallel_corridor_blocker.sdf"
                ),
            ),
            DeclareLaunchArgument(
                "output_dir",
                default_value="/tmp/dynnav_correlated_history_benchmark",
            ),
            DeclareLaunchArgument("repetitions", default_value="1"),
            DeclareLaunchArgument("headless", default_value="true"),
            OpaqueFunction(function=_launch_setup),
        ]
    )
