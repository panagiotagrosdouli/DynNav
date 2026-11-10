# C18 — Executable 2D instantaneous CBF feasibility audit

## Engineering defect and research motivation

The original C18 filter repeatedly applied small gradient steps and then returned the final velocity as a nominally safe command. It did not verify that **all** obstacle constraints were satisfied after the finite iteration budget, and its prose claimed a *provable physical safety guarantee* that such a numerical heuristic cannot establish.

The updated C18 filter enumerates the feasible active sets for 2D linearized point-robot Control Barrier Function (CBF) halfspaces and returns the closest feasible velocity to the requested 2D velocity. It reports **constraint_feasible**, **minimum_cbf_margin**, **status**, and **instantaneous_only** for each operation.

If constraints are infeasible (e.g., overlapping physical safety margins around obstacles enclosing a robot), the fallback returns a zero command with `constraint_feasible=false` and the explicit status `INFEASIBLE_CBF_ZERO_COMMAND_NOT_CERTIFIED_SAFE`. Zero is a conservative command, **not mathematical proof of a safe state when the robot already violates a minimum-distance condition**.

The implementation rejects non-finite or incorrectly shaped robot states, obstacle coordinates or commands rather than propagating invalid floating-point commands.

## Actually executable evidence

[Dedicated C18 GitHub Actions workflow](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/c18-cbf-feasibility.yml) runs tests for:

- Exact projection against one obstacle's linearized inequality.
- Simultaneous feasibility across multiple obstacle constraints.
- Explicit infeasible-state detection, zero command and *non-certified* classification.
- Rejection of NaN, infinity and invalid state dimensions.
- 100 independently randomized obstacle configurations with direct numerical verification of every CBF inequality.
- Re-execution of the original C18 synthetic stress benchmark, with six shielded/unshielded scenario outcomes and uploaded CSV.

## Verified actual CI results

[Successful GitHub Actions run #42801003690](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42801003690) passed **5/5 numerical CBF tests** and executed the original three stress scenarios with/without the shield.

| Synthetic case | Unshielded constraint violations | Shielded violations | Final goal distance, unshielded | Final goal distance, shielded |
|---|---:|---:|---:|---:|
| Single direct obstacle | 6 | 0 | 0.100 m | **2.950 m** |
| Narrow gap | 0 | 0 | 0.100 m | **2.500 m** |
| Offset hazard | 6 | 0 | 0.075 m | 0.045 m |

**Important negative performance result:** The shield eliminated sampled distance violations on two cases but prevented meaningful goal progress in the direct-obstacle and narrow-gap cases. This is a *safety-efficiency tradeoff*, not demonstrated superior autonomous navigation. The original benchmark is synthetic with simplified point dynamics, and its 0 sampled violations are not a formal continuous-time collision guarantee.

## Actual ROS 2 Jazzy gate integration (isolated, no physical robot)

[Successful ROS2 DDS workflow #42801508579](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42801508579) executed two separate genuine ROS2 `rclpy` nodes and subscribers with isolated topics. Real serialized `geometry_msgs/msg/Twist` messages were published, filtered by the actual C18 algorithm and received through ROS2 middleware. The result is **not** a physical differential-drive command: `linear.x/y` encode a synthetic two-dimensional point velocity, not a deployable unicycle controller.

- **Feasible one-obstacle case:** requested x velocity 2.0 (proxy m/s); filtered x velocity **0.9**, with `constraint_feasible=true` and nonnegative instantaneous CBF margin.
- **Infeasible two-obstacle overlap:** filtered output **(0.0, 0.0)**, with `constraint_feasible=false`, status `INFEASIBLE_CBF_ZERO_COMMAND_NOT_CERTIFIED_SAFE`.

All published topics were under `/c18/isolated_sim/`; **no actuator topic** such as hardware `/cmd_vel` was published. There is no physical robot or full closed-loop navigation in this workflow. The code and workflow save independent JSON reports, verified with a separate acceptance step.

## Scientific limitation

These tests address numerical feasibility of **instantaneous, 2D, point-robot, static-obstacle, linearized** CBF constraints. They do **NOT** prove discrete-time forward invariance, safety under actuator latency, wheel slip, a unicycle's nonholonomic dynamics, moving humans, sensor noise, robot radius variation, collisions between timesteps, uncertainty-aware risk bounds or formal system verification. The existing STL monitor checks a sampled finite history, not a complete temporal model-checking proof.

Further physical validation requires a robot-specific `cmd_vel` output gate designed and reviewed by an onsite safety engineer, hard acceleration/velocity bounds, independent E-stop, obstacle sensor calibration, emergency fallback policy and actual hardware trajectory evidence.

**Physical C18 robot trials verified: zero.**
