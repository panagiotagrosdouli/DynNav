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

## Scientific limitation

These tests address numerical feasibility of **instantaneous, 2D, point-robot, static-obstacle, linearized** CBF constraints. They do **NOT** prove discrete-time forward invariance, safety under actuator latency, wheel slip, a unicycle's nonholonomic dynamics, moving humans, sensor noise, robot radius variation, collisions between timesteps, uncertainty-aware risk bounds or formal system verification. The existing STL monitor checks a sampled finite history, not a complete temporal model-checking proof.

Further physical validation requires a robot-specific `cmd_vel` output gate designed and reviewed by an onsite safety engineer, hard acceleration/velocity bounds, independent E-stop, obstacle sensor calibration, emergency fallback policy and actual hardware trajectory evidence.

**Physical C18 robot trials verified: zero.**
