# Navigation Pipeline

DynNav uses a closed-loop navigation pipeline:

1. **Sense**: receive or simulate occupancy observations.
2. **Represent belief**: store obstacle likelihoods as a probability grid.
3. **Propagate uncertainty**: drift stale cells toward higher uncertainty between observations.
4. **Plan**: search for a trajectory that trades geometric cost against risk and returnability.
5. **Monitor**: evaluate local occupancy, trajectory risk, and recoverability.
6. **Reroute or supervise**: replan or enter safe mode when thresholds are violated.
7. **Evaluate**: log path length, risk, recoverability, success, and node expansions.

## Scientific motivation

Unknown environments produce partial and uncertain state information. A pipeline that exposes uncertainty throughout planning and monitoring is easier to analyze than one that hides uncertainty inside a binary costmap.

## Engineering motivation

Each step maps to a testable Python module. This makes failures easier to isolate and permits CI execution without ROS 2.

## Limitations

The current pipeline operates on a grid-world abstraction. Continuous dynamics, velocity obstacles, perception latency, localization covariance, and actuator limits require additional integration work.
