# C25 Scientific Upgrade Notes — Adversarial Attack Impact Evaluation

## What was already strong

Contribution 25 already implemented a useful adversarial testing layer:

> Generate sensor and neural-input attacks to stress-test DynNav's perception, localization, and intrusion-detection assumptions.

The existing module includes:

- FGSM attacks,
- PGD attacks,
- LiDAR phantom obstacle injection,
- LiDAR point removal,
- LiDAR sensor blinding,
- odometry drift spoofing,
- a basic robustness evaluator.

This is valuable because navigation robustness should be tested against manipulated inputs, not only clean sensor streams.

## Main weakness before this upgrade

The original module generated attacks, but did not quantify their navigation impact or detection quality.

A reviewer could ask:

> How severe is each attack?

or:

> Does a detector notice the attack?

or:

> Which mitigation should the robot choose after an attack is detected?

## New contribution added

C25 now includes:

```text
attack_impact_evaluator.py
experiments/eval_attack_impact.py
```

The new benchmark evaluates:

- attack detection precision,
- attack detection recall,
- attack detection F1,
- attack severity score,
- LiDAR geometry change,
- minimum-distance degradation,
- odometry error,
- mitigation recommendation.

## New benchmark

Run:

```bash
python contributions/25_adversarial_attack_simulator/experiments/eval_attack_impact.py
```

Output:

```text
contributions/25_adversarial_attack_simulator/results/c25_attack_impact.csv
```

The benchmark evaluates:

- FGSM,
- PGD,
- LiDAR phantom injection,
- LiDAR point removal,
- LiDAR sector blinding,
- odometry drift.

## Reviewer-safe claim

A stronger claim after this upgrade is:

> Contribution 25 evaluates adversarial attacks by measuring detection quality, navigation-relevant degradation, attack severity, and mitigation recommendations across gradient, LiDAR, and odometry attacks.

## Relationship to other contributions

C25 connects directly to:

- C08 intrusion detection and trust-aware response,
- C14 causal risk attribution,
- C18 formal safety shields,
- C20 failure explanation,
- C05 safe mode.

## Limitations

- The detector is intentionally simple and threshold-based.
- Attack scenarios are synthetic and designed for reproducible evaluation.
- Gradient attacks use finite differences, not full autograd.
- LiDAR and odometry attacks are proxies for real cyber-physical attacks.
- Real deployment requires ROS 2 bag replay, hardware sensor logs, and stronger IDS models.

## Next research step

The strongest extension is closed-loop attack response:

```text
attack detected -> trust decreases -> safe mode / shield tightening -> causal explanation -> operator report
```

This would integrate C25 with C08, C14, C18, and C20.
