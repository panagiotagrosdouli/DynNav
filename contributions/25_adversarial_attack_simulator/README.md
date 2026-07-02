# Contribution 25 — Adversarial Attack Simulator and Impact Evaluation

[![Module](https://img.shields.io/badge/Module-25-purple)](.) [![Type](https://img.shields.io/badge/Type-Cybersecurity%20%2F%20Robustness-blue)](.) [![Status](https://img.shields.io/badge/Status-Core%20Upgraded-brightgreen)](.)

## Plain-language summary

A robot navigation system should not only work on clean sensor data.

It should also be tested against manipulated inputs:

```text
phantom LiDAR obstacles,
removed obstacle points,
blinded sensor sectors,
odometry drift,
adversarial neural-input perturbations.
```

Contribution 25 generates adversarial attacks against DynNav's perception and navigation pipeline.

The upgraded version adds attack-impact evaluation:

> The simulator does not only generate attacks. It measures whether attacks are detectable, how severe they are, how they degrade navigation-relevant signals, and which mitigation should be triggered.

---

## Research Question

> **RQ25:** How robust is DynNav to adversarial sensor manipulation, and can attacks be detected before they cause unsafe navigation behaviour?

This contribution studies:

- FGSM attacks on neural inputs,
- PGD attacks on neural inputs,
- LiDAR phantom obstacle injection,
- LiDAR point removal,
- LiDAR sector blinding,
- odometry drift spoofing,
- attack severity scoring,
- detection precision/recall,
- mitigation recommendation.

---

## Attack Types

| Attack | Target | Method | Navigation Risk |
|---|---|---|---|
| FGSM | Neural input | ε·sign(∇L) finite-difference perturbation | Corrupts learned perception or policy input |
| PGD | Neural input | Iterative projected gradient perturbation | Stronger neural-input corruption |
| LiDAR spoof add | Point cloud | Inject phantom obstacle clusters | Planner may avoid nonexistent obstacle |
| LiDAR spoof remove | Point cloud | Remove points near target obstacle | Planner may collide with hidden obstacle |
| LiDAR blind | Point cloud | Zero out angular sector | Planner loses obstacle evidence |
| Odometry drift | Pose estimate | Accumulate biased pose error | Planner localizes robot incorrectly |

---

## Existing Components

The original C25 implementation includes:

- `AttackType`,
- `AttackConfig`,
- `GradientAttacker`,
- `LiDARAttacker`,
- `OdometrySpoofer`,
- `RobustnessEvaluator`,
- FGSM and PGD finite-difference attacks,
- LiDAR spoofing and blinding,
- odometry drift injection.

---

## New Upgrade Added

C25 now includes:

```text
attack_impact_evaluator.py
```

This evaluator measures:

- attack detection precision,
- attack detection recall,
- attack detection F1,
- severity score,
- minimum-distance degradation,
- LiDAR geometry change,
- odometry error,
- mitigation recommendation.

---

## Files

```text
25_adversarial_attack_simulator/
├── README.md
├── adversarial_attacks.py
├── attack_impact_evaluator.py
├── docs/
│   └── SCIENTIFIC_UPGRADE.md
├── experiments/
│   └── eval_attack_impact.py
└── results/
    └── c25_attack_impact.csv
```

---

## Quick Start

Run the basic robustness evaluator:

```python
from contributions.25_adversarial_attack_simulator.adversarial_attacks import RobustnessEvaluator, AttackConfig
import numpy as np

evaluator = RobustnessEvaluator(AttackConfig(epsilon=0.1, pgd_steps=20))
obs_samples = [np.random.rand(16) for _ in range(10)]
point_clouds = [np.random.rand(500, 3) * 10]
loss_fn = lambda x: float(-np.sum(x))
results = evaluator.evaluate(obs_samples, loss_fn, point_clouds)
print(results)
```

Run the new attack-impact benchmark:

```bash
python contributions/25_adversarial_attack_simulator/experiments/eval_attack_impact.py
```

This generates:

```text
contributions/25_adversarial_attack_simulator/results/c25_attack_impact.csv
```

---

## Attack-Impact Metrics

| Metric | Meaning |
|---|---|
| Detection precision | Fraction of detected attacks that are truly attacks |
| Detection recall | Fraction of true attacks that are detected |
| Detection F1 | Harmonic mean of precision and recall |
| Severity score | Normalized attack impact score |
| Min-distance degradation | How much a LiDAR attack reduces perceived nearest-obstacle distance |
| Geometry change | Point-cloud count and centroid-shift change |
| Odometry error | Pose error induced by odometry spoofing |
| Mitigation | Recommended response based on severity |

---

## Mitigation Levels

| Severity | Mitigation |
|---|---|
| Low | Continue with increased trust monitoring |
| Medium | Safe mode and sensor cross-check |
| High | Emergency stop and operator request |

---

## Scientific Contribution

The upgraded C25 contribution is not simply:

> Generate adversarial sensor perturbations.

It is stronger:

> Evaluate adversarial attacks by measuring detection quality, navigation impact, severity, and mitigation choice.

This makes the adversarial simulator useful for robustness evaluation rather than only attack demonstration.

---

## Integration

- **Tests:** C08 intrusion detection and trust-aware response
- **Explained by:** C14 causal risk attribution and C20 failure explanation
- **Can trigger:** C05 safe mode
- **Can tighten:** C18 formal safety shields
- **Can stress-test:** C21 learned policies and C23/C24 mapping layers

Recommended runtime interface:

```text
attack_report = {
    attack_type,
    affected_sensor,
    severity_score,
    detection_status,
    navigation_impact,
    mitigation
}
```

---

## Limitations

- The detector in the benchmark is threshold-based and intentionally simple.
- Attack scenarios are synthetic.
- Gradient attacks use finite differences, not autograd.
- LiDAR and odometry attacks are proxies for real cyber-physical attacks.
- Real deployment requires ROS 2 bag replay, real sensor logs, and stronger IDS models.

---

## Next Research Step

The strongest extension is closed-loop attack response:

```text
attack detected
      ↓
trust score decreases
      ↓
safe mode or shield tightening
      ↓
causal attribution
      ↓
operator explanation report
```

This would integrate C25 with C08, C14, C18, and C20.

---

## Conclusion

Contribution 25 establishes the adversarial robustness-testing layer of DynNav.

The upgraded version makes the module stronger by measuring attack detection, attack severity, navigation impact, and mitigation response.
