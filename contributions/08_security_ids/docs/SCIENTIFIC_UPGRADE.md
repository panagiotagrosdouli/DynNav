# C08 Scientific Upgrade Notes — Trust-Aware IDS Response

## What was already strong

Contribution 08 already implemented the core idea of monitoring innovation sequences for security and fault detection.

The existing module includes:

- Mahalanobis innovation scoring,
- approximate chi-square thresholds,
- consecutive and k-of-n trigger policies,
- support for anomaly monitoring before safe-mode activation.

This is important because robot navigation should not assume that sensors, localization, or external signals are always trustworthy.

## Main weakness before this upgrade

The original IDS could detect anomalies, but detection alone is not enough.

A reviewer could ask:

> What does the robot actually do after an IDS alert?

or:

> How does an anomaly flag become a planner-level mitigation decision?

Without an explicit response policy, IDS remains a diagnostic tool rather than a navigation safety component.

## New contribution added

C08 now includes:

```text
code/ids_response_policy.py
experiments/eval_ids_response_policy.py
```

The new response layer maps innovation-monitor outputs to:

- alert severity,
- trust score,
- planner mitigation,
- explanatory reason.

## Alert levels

| Severity | Meaning | Planner response |
|---|---|---|
| NORMAL | Innovation is expected | No mitigation |
| WATCH | Innovation is elevated | Increase caution |
| WARNING | IDS trigger or high anomaly evidence | Trigger safe mode |
| CRITICAL | Sustained or extreme anomaly | Emergency stop |

## New benchmark

Run:

```bash
python contributions/08_security_ids/experiments/eval_ids_response_policy.py
```

Output:

```text
contributions/08_security_ids/results/c08_ids_response_policy.csv
```

The benchmark evaluates scenarios such as:

- normal noise,
- elevated innovation,
- single large spike,
- gradual spoofing,
- sustained attack.

## Reviewer-safe claim

A stronger claim after this upgrade is:

> Contribution 08 connects innovation-based intrusion detection to navigation behaviour by converting anomaly evidence into trust scores, alert severities, and planner mitigation actions.

## Relationship to other contributions

C08 now directly supports:

- C05 safe-mode activation,
- C03 risk-aware planning under degraded trust,
- C14 causal root-cause attribution,
- C25 adversarial attack simulation.

## Limitations

- The response policy is interpretable and rule-based, not learned.
- The benchmark uses synthetic monitor outputs for auditability.
- Real robot deployment should validate thresholds under sensor-specific noise and attack models.
- Emergency stop here is a planner mitigation recommendation, not a certified hardware safety system.

## Next research step

The strongest extension is attack-conditioned mitigation:

```text
mitigation = f(sensor_type, anomaly_source, d2_ratio, attack_duration, navigation_context)
```

This would allow different responses for GPS spoofing, LiDAR corruption, IMU drift, map tampering, and communication attacks.
