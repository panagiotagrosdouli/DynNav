# C01 ROS 2 planning-only interface

## Evidence status

This interface exists in the C01 contribution, but has **NOT** been executed
against a physical robot or validated as a drop-in Nav2 GlobalPlanner plugin.
The verified C01 real-data experiment is offline use of an official LILocBench
occupancy map. **Physical C01 trials verified: 0.**

## Purpose and precise boundary

`experiments/ros2_get_plan_node.py` is an optional ROS 2 Jazzy node exposing
`nav_msgs/srv/GetPlan`, with source in the C01 directory. It consumes a
`nav_msgs/msg/OccupancyGrid` and computes routes using the actual C01
Manhattan or saved neural heuristic. It also publishes a
`nav_msgs/msg/Path` and JSON `std_msgs/msg/String` diagnostics to
`c01/plan` and `c01/diagnostics`.

This is **planning only**: no `/cmd_vel` publication, no NavigateToPose action,
no Nav2 plugin registration, no autonomous physical movement. It cannot be used
as proof that C01 controlled an actual robot.

## Requirements

- ROS 2 Jazzy with `rclpy`, `nav_msgs`, `geometry_msgs` and `std_msgs`.
- Python 3.12 compatible dependencies from the repository environment.
- Optional PyTorch and existing C01 `.pt` checkpoint for learned modes.
- A 2D map/costmap published as `OccupancyGrid` with nonempty frame ID.
- Pre-inflated costmap for a physical footprint, or deliberately chosen
  conservative `inflation_cells` for **non-actuating planning tests**.

Do not connect this prototype to a motor controller without a separate
robot-specific integration review and independent emergency-stop mechanism.

## Planning-only startup (no robot movement)

From the repository root after sourcing the ROS and Python environments:

```bash
source /opt/ros/jazzy/setup.bash

python contributions/01_learned_astar/experiments/ros2_get_plan_node.py \
  --ros-args \
  -p mode:=astar_manhattan \
  -p map_topic:=/global_costmap/costmap \
  -p lethal_threshold:=50 \
  -p inflation_cells:=0
```

For the saved learned model:

```bash
python contributions/01_learned_astar/experiments/ros2_get_plan_node.py \
  --ros-args \
  -p mode:=learned_raw \
  -p checkpoint:=/absolute/path/DynNav/contributions/01_learned_astar/models/heuristic_net_rich.pt \
  -p map_topic:=/global_costmap/costmap
```

The node refuses to start if the selected neural checkpoint is unavailable or
cannot be loaded. It reports the checkpoint SHA-256 in diagnostics.

Call `/c01/get_plan` using a properly framed `GetPlan` request. Start and
goal must both be expressed in **exactly the same coordinate frame** as the
received occupancy grid; this prototype does not resolve transforms
automatically. Goal tolerance is not used: the requested goal cell must be
unblocked and the path terminates in that cell. Empty paths indicate
unavailable maps, frame mismatch, invalid targets or no route.

## Coordinate, occupancy and safety assumptions

- ROS OccupancyGrid is row-major with increasing grid Y. Do not apply the
  image-axis reversal used for ROS YAML map images a second time.
- Unknown cells (occupancy -1) are always non-traversable.
- Values above the declared lethal threshold are blocked.
- Origin position and planar quaternion are included in conversions.
- `inflation_cells=0` assumes the subscribed costmap has already applied the
  physical footprint / safety inflation. A raw map with no inflation may
  produce a geometrically valid but physically infeasible plan.
- Uses four-connected unit-cost grid search; no diagonal, kinodynamic,
  curvature, controller, wheel-slip or obstacle-velocity model.
- The service does not check whether the incoming map is fresh or whether the
  robot's localization is reliable; those safety checks belong to the
  authorized ROS integration and must be independently validated.
- The service itself can compute a raw learned path that is suboptimal or
  unsafe relative to physical controller constraints. Never send it directly
  to robot actuators.

## Auditable diagnostics

Each completed query logs:

- Planner mode and checkpoint SHA-256 (if learned).
- Map frame and start/goal cells.
- Computed path cost in cells.
- Expanded nodes.
- Measured planning time.
- Whether a path was returned.
- Explicit evidence label `planning_only_not_robot_motion`.

The diagnostics prove only what the process reported. To support a physical
experiment, one must separately establish correct node/robot identity, capture
synchronized ROS 2 motion and planner traces, and independently verify actual
C01 control. See [PHYSICAL_ROBOT_PROTOCOL.md](PHYSICAL_ROBOT_PROTOCOL.md).

## Tests

Run the pure Python geometry tests without ROS:

```bash
python -m pytest -q contributions/01_learned_astar/tests/test_ros2_grid_geometry.py
```

They cover ROS grid orientation, obstacle/unknown handling, inflation, origin
rotation, coordinate roundtrip, invalid inputs and path integrity.

**Not yet performed:** real ROS Jazzy message-level integration tests,
GetPlan service functional tests on a running robot, Nav2 plugin integration,
Gazebo closed-loop C01 trials and physical-robot trials.

## Read-only sensor-readiness probe for an actual ROS network

From a machine connected to the *actual* robot's ROS 2 domain, an onsite
operator can run:

```bash
source /opt/ros/jazzy/setup.bash
python contributions/01_learned_astar/experiments/ros2_hardware_readiness.py \
  --seconds 15 \
  --output /absolute/path/to/trial_evidence/ros_readiness.json
```

This node **only subscribes** to `/scan`, `/odom` and `/tf`. It also
inspects advertised topic names/types and returns a JSON report; it does
not start Nav2 or send velocity, action or navigation commands. Receiving
these topics is **not** proof that a real robot moved, that the data
originated from hardware, that emergency-stop works, or that C01 was
executed. A direct human safety review remains mandatory.

The test command (which runs without a robot) is:

```bash
python -m pytest -q contributions/01_learned_astar/tests/test_ros2_hardware_readiness.py
```

An accessible physical platform and onsite operator are required before
the live probe can produce real sensor evidence. No such probe has been
executed on physical hardware during this review.
