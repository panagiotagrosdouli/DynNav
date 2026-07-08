# DynNav Research Overview

DynNav studies navigation in unknown or partially observed environments where a shortest path may be unsafe because map and state estimates are uncertain. The repository is organized around a conservative research claim: the implemented stack is a deterministic prototype for risk-aware planning, rerouting, monitoring, and reproducible benchmarking. It is not presented as a fully validated autonomy system.

## Scientific motivation

Mobile robots often operate with incomplete occupancy information, noisy localization, and delayed perception updates. A planner that optimizes only geometric length can enter narrow passages, high-uncertainty regions, or locally irreversible states. DynNav introduces explicit risk and recoverability terms so that route selection accounts for uncertainty and the ability to return to a safer state.

## Engineering motivation

The project separates core algorithms from ROS 2 integration, visualization, benchmarking, and documentation. This makes the code testable in continuous integration while still leaving clear extension points for real robots.

## Current scope

Implemented in the research-grade scaffold:

- typed grid and trajectory primitives;
- deterministic synthetic scenario generation;
- risk-aware A* with occupancy and returnability penalties;
- CVaR-style risk utilities and uncertainty propagation prototypes;
- dynamic rerouting based on trajectory risk and recoverability;
- runtime monitoring and safe-mode supervision;
- CSV benchmark generation and Markdown summaries;
- static research figures and automated demo animation.

## Limitations

The current algorithms are intentionally lightweight and suitable for reproducible CI experiments. They do not replace a full SLAM stack, probabilistic occupancy mapper, nonlinear model-predictive controller, or formally verified safety shield. Hardware claims require separate logs under `results/hardware/`.
