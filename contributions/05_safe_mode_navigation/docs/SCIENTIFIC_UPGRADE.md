# C05 Scientific Upgrade Notes — Safe-Mode State Machine

## What was already strong

Contribution 05 already captured an important runtime-safety idea:

> When risk becomes too high, the robot should stop behaving normally and switch to a conservative navigation mode.

The existing result showed a clear safety-efficiency trade-off:

- total risk reduced from 1.2 to 0.4,
- maximum risk reduced from 0.9 to 0.2,
- risk reduction: 66.7%,
- maximum-risk reduction: 77.8%,
- distance increased by 263.6%,
- total cost increased by 112.2%.

This is scientifically honest because it does not claim safe mode is free. It reduces risk by paying extra distance and cost.

## Main weakness before this upgrade

The original safe-mode description was threshold-based, but real safe-mode controllers require more than a single threshold.

A reviewer could ask:

> What prevents the robot from rapidly switching between normal and safe mode when risk is noisy?

or:

> How is emergency stop different from conservative navigation?

or:

> How sensitive are the results to the chosen risk thresholds?

## New contribution added

C05 now includes an upgraded state machine in:

```text
code/safe_mode_controller.py
```

and a threshold-sensitivity benchmark in:

```text
experiments/eval_safe_mode_thresholds.py
```

The upgraded controller supports:

- activation threshold,
- deactivation threshold,
- hysteresis,
- activation persistence,
- recovery persistence,
- cooldown after leaving safe mode,
- emergency stop,
- transition logging,
- summary metrics.

## Why this matters scientifically

Safe mode should not activate on a single noisy risk spike unless the spike is critical.

A robust safe-mode policy must balance:

- early activation for safety,
- avoiding unnecessary conservative behaviour,
- avoiding mode flickering,
- emergency response to extreme risk,
- controlled recovery back to normal operation.

The upgraded C05 controller makes these design choices explicit and measurable.

## New benchmark

Run:

```bash
python contributions/05_safe_mode_navigation/experiments/eval_safe_mode_thresholds.py
```

Output:

```text
contributions/05_safe_mode_navigation/results/c05_safe_mode_thresholds.csv
```

The benchmark evaluates synthetic risk traces:

- nominal noise,
- temporary hazard,
- critical spike,
- chattering risk near the threshold.

For each trace, it reports:

- normal steps,
- safe-mode steps,
- emergency-stop steps,
- transitions,
- replans,
- operator alerts,
- mean commanded speed,
- maximum risk.

## Reviewer-safe claim

A stronger claim after this upgrade is:

> Contribution 05 implements safe mode as an explicit finite-state safety supervisor with hysteresis, persistence, cooldown, and emergency-stop handling. Its behaviour can be audited under noisy, temporary, critical, and chattering risk traces.

## Relationship to other contributions

C05 acts as a runtime supervisor for several other modules:

- C02 provides calibrated uncertainty.
- C03 provides risk metrics.
- C04 provides recoverability and irreversibility signals.
- C08 provides IDS/security alerts.
- C18 provides formal safety constraints.

Safe mode is therefore not a planner replacement. It is a supervisory layer that changes planner behaviour when risk or trust degrades.

## Limitations

- The benchmark uses synthetic risk traces for auditability.
- Real robot deployment requires integration with velocity limits, inflation radius, Nav2 parameters, and hardware emergency-stop policies.
- Thresholds are hand-selected; they should eventually be learned or adapted online.
- Emergency stop is represented logically, not as a hardware safety system.

## Next research step

The strongest extension is adaptive safe-mode thresholding:

```text
threshold = f(calibrated_uncertainty, recoverability, IDS_alerts, mission_context)
```

This would allow the robot to become more conservative when uncertainty rises, returnability drops, or cyber-physical trust decreases.
