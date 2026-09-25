"""Canonical G1 V4 Gazebo launch with resettable odometry localization."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    EmitEvent,
    ExecuteProcess,
    IncludeLaunchDescription,
    OpaqueFunction,
    RegisterEventHandler,
    TimerAction,
)
from launch.event_handlers import OnProcessExit, OnShutdown
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import yaml

from dynnav_nav2_benchmark.configuration import (
    freeze_global_costmap_for_planner_comparison,
    inject_correlated_history_planner_parameters,
)
from dynnav_nav2_benchmark.correlated_history_execution import (
    blocker_footprint_cells,
    load_correlated_history_execution_suite,
    quantized_hazard_trigger_gates,
)
from dynnav_nav2_benchmark.history_execution import world_to_cell


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
    dependence = LaunchConfiguration("dependence").perform(context)
    headless = LaunchConfiguration("headless").perform(context)

    suite = load_correlated_history_execution_suite(scenario_path)
    scenario = suite.scenario
    map_payload = yaml.safe_load(map_file.read_text(encoding="utf-8"))
    resolution = float(map_payload["resolution"])
    origin_x = float(map_payload["origin"][0])
    origin_y = float(map_payload["origin"][1])

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
    payload = freeze_global_costmap_for_planner_comparison(payload)
    generated_params.parent.mkdir(parents=True, exist_ok=True)
    generated_params.write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )

    nav2_share = Path(get_package_share_directory("nav2_bringup"))
    sim_share = Path(get_package_share_directory("nav2_minimal_tb3_sim"))
    bringup_launch = nav2_share / "launch" / "bringup_launch.py"
    spawn_launch = sim_share / "launch" / "spawn_tb3.launch.py"
    robot_sdf = sim_share / "urdf" / "gz_waffle.sdf.xacro"
    robot_urdf = sim_share / "urdf" / "turtlebot3_waffle.urdf"

    world_sdf = tempfile.mktemp(prefix="dynnav_g1_v4_", suffix=".sdf")
    world_xacro = ExecuteProcess(
        cmd=[
            "xacro",
            "-o",
            world_sdf,
            f"headless:={headless}",
            world_file,
        ],
        output="screen",
    )
    gazebo_server = ExecuteProcess(
        cmd=["gz", "sim", "-r", "-s", world_sdf],
        output="screen",
    )
    cleanup_world = RegisterEventHandler(
        OnShutdown(
            on_shutdown=[
                OpaqueFunction(
                    function=lambda _: Path(world_sdf).unlink(missing_ok=True)
                )
            ]
        )
    )

    robot_description = robot_urdf.read_text(encoding="utf-8")
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[
            {
                "use_sim_time": True,
                "robot_description": robot_description,
            }
        ],
        remappings=[("/tf", "tf"), ("/tf_static", "tf_static")],
    )
    spawn_robot = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(str(spawn_launch)),
        launch_arguments={
            "use_sim_time": "True",
            "robot_name": suite.robot_entity,
            "robot_sdf": str(robot_sdf),
            "x_pose": str(scenario.start.x),
            "y_pose": str(scenario.start.y),
            "z_pose": "0.01",
            "roll": "0.0",
            "pitch": "0.0",
            "yaw": str(scenario.start.yaw),
        }.items(),
    )

    bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(str(bringup_launch)),
        launch_arguments={
            "namespace": "",
            "slam": "False",
            "use_localization": "False",
            "serve_static_map": "True",
            "map": str(map_file),
            "use_sim_time": "True",
            "params_file": str(generated_params),
            "autostart": "True",
            "use_composition": "False",
            "use_respawn": "False",
            "use_keepout_zones": "False",
            "use_speed_zones": "False",
            "container_name": "nav2_container",
        }.items(),
    )

    odom_localizer = Node(
        package="dynnav_nav2_benchmark",
        executable="resettable_odom_localizer",
        name="dynnav_resettable_odom_localizer",
        output="screen",
        parameters=[
            {
                "use_sim_time": True,
                "start_x": float(scenario.start.x),
                "start_y": float(scenario.start.y),
                "start_yaw": float(scenario.start.yaw),
                "map_frame": scenario.frame_id,
                "odom_frame": "odom",
                "odom_topic": "odom",
                "reset_topic": "dynnav/executed_transition",
            }
        ],
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

    runner_arguments = [
        "--scenario",
        str(scenario_path),
        "--blocker-sdf",
        blocker_sdf,
        "--output",
        output,
        "--repetitions",
        repetitions,
        "--localization-mode",
        "odom_reset",
    ]
    if dependence:
        runner_arguments.extend(["--dependence", dependence])

    runner = Node(
        package="dynnav_nav2_benchmark",
        executable="correlated_history_dynamic_execution_benchmark",
        name="dynnav_correlated_history_execution_benchmark",
        output="screen",
        arguments=runner_arguments,
    )
    delayed_runner = TimerAction(period=12.0, actions=[runner])
    shutdown = RegisterEventHandler(
        OnProcessExit(
            target_action=runner,
            on_exit=[
                EmitEvent(
                    event=Shutdown(
                        reason="G1 V4 correlated history benchmark completed"
                    )
                )
            ],
        )
    )

    return [
        world_xacro,
        cleanup_world,
        gazebo_server,
        spawn_robot,
        robot_state_publisher,
        bringup,
        odom_localizer,
        gazebo_services,
        delayed_runner,
        shutdown,
    ]


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
                default_value="/tmp/dynnav_g1_v4_nav2_params.yaml",
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
                    benchmark_share
                    / "models"
                    / "g1_parallel_corridor_blocker.sdf"
                ),
            ),
            DeclareLaunchArgument(
                "output_dir",
                default_value="/tmp/dynnav_g1_v4_benchmark",
            ),
            DeclareLaunchArgument("repetitions", default_value="1"),
            DeclareLaunchArgument("dependence", default_value=""),
            DeclareLaunchArgument("headless", default_value="true"),
            OpaqueFunction(function=_launch_setup),
        ]
    )
