# C06 — Actual recorded Dingo odometry, resource proxy and scientific evidence

**Validated CI:** [C06 recorded-odometry workflow #42715857462](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42715857462) passed **4 targeted tests**, source bag SHA-256 verification, real odometry decoding and independent report checks.

## Measured physical-world data, without fabricating energy sensors

The original LILocBench Clearpath Dingo ROS1 bag (SHA-256 `df4abb923df1bb1ff46326abab8667188f4bc17e7ae12ea16905e9d632470c58`) was retrieved and analyzed. The code selects one actual odometry topic and integrates finite, strictly chronological consecutive XY displacements while excluding steps beyond a configured jump threshold.

| Quantity | Verified observation or assumption |
|---|---|
| Physically recorded planar odometry distance | **53.0782208 m** |
| Time span of original recording | **159.930029 seconds** |
| Assumed energy intensity (NOT measured) | **20 joules / meter** |
| Assumed total budget (NOT Dingo telemetry) | **1000 joules** |
| Assumed reserve (NOT Dingo telemetry) | **150 joules** |
| Derived *hypothetical* energy | **1061.564416 J** |
| Energy/current/voltage measurements in available recording | **Not established** |
| Real RSSI/SNR or connectivity ground truth | **Not established** |
| C06 autonomous navigation on a physical Dingo | **0 verified trials** |

The energy formula is `E_proxy = distance_m * assumed_J_per_m`. **This estimated quantity is not observed battery usage**, does not account for motor load, terrain, acceleration, battery degradation, computer power, charging or radio transmission. The actual journal returns `BLOCKED_NO_PHYSICAL_BATTERY_OR_LINK_MEASUREMENT` and *never* turns the assumed budget into a certified mission-feasibility claim. Source odometry is physically recorded data, but no C06 algorithm controlled the original Dingo collection.

## Genuine code and tests

- `experiments/eval_real_dingo_odometry_resources.py`: actual ROS1 bag decoder, audited planar odometry integration, configurable energy assumptions, raw file hash and fail-closed evidence labels.
- `tests/test_real_odometry_resource_proxy.py`: real numerical edge-case regressions.
- `.github/workflows/c06-real-odometry.yml`: actual source download, hash verification, execution, report provenance checks and retained JSON artifact.
- This report is a separate source-bound companion to C06's synthetic energy and connectivity sweeps.

### Reproduce

```bash
python contributions/06_energy_connectivity/experiments/eval_real_dingo_odometry_resources.py \
  /path/to/official_original_dingo.bag \
  --output results/c06_recorded_odometry/summary.json \
  --joules-per-meter 20 --battery-budget-j 1000 --reserve-j 150
```

The official bag must be acquired from its legitimate host, respecting applicable license and access conditions. Do not commit the recording into Git history.

## Validation still missing

Physical battery voltage/current/power telemetry, calibrated kinematic energy per unit path under load, radio RSSI/SNR/bandwidth/packet-loss measurements, actually deployed relay communications, and C06-selected physical trajectories are not present. Future hardware tests require a named connected robot, operator-controlled emergency stop, ROS2/Nav2 engineering integration and synchronized source logs with baseline routes and measured return margins.

**Scientific verdict:** This run validates actual archived physical-world **odometry decoding and travel distance**, plus an explicitly hypothetical resource feasibility calculation; it cannot validate C06 real energy or radio-connectivity performance.
