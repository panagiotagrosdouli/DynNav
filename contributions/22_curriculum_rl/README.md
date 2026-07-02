# Contribution 22 — Curriculum RL Training and Strategy Evaluation

[![Module](https://img.shields.io/badge/Module-22-purple)](.) [![Type](https://img.shields.io/badge/Type-Reinforcement%20Learning-blue)](.) [![Status](https://img.shields.io/badge/Status-Core%20Upgraded-brightgreen)](.)

## Plain-language summary

Training a navigation policy directly in a very hard environment can fail.

Curriculum learning starts with easier tasks and gradually increases difficulty:

```text
easy → medium → hard → expert → extreme
```

Contribution 22 implements adaptive difficulty scheduling for RL navigation. The upgraded version adds a strategy benchmark that compares adaptive, fixed, and reverse curriculum schedules.

The key idea is:

> A curriculum should be judged by how efficiently and stably it moves the agent toward harder tasks, not only by whether it produces a training log.

---

## Research Question

> **RQ22:** Does curriculum training reduce sample complexity and improve generalization to unseen navigation environments?

This contribution studies:

- adaptive curriculum scheduling,
- fixed curriculum scheduling,
- reverse curriculum concepts,
- stage progression,
- success-rate trends,
- training stability,
- held-out transfer,
- sample-efficiency proxies.

---

## Difficulty Dimensions

| Stage | Obstacles | Map Size | Obstacle Speed | Sensor Noise |
|---|---:|---:|---:|---:|
| easy | 2 | 5×5 m | static | 0.00 |
| medium | 5 | 8×8 m | static | 0.05 |
| hard | 10 | 10×10 m | 0.1 m/s | 0.10 |
| expert | 18 | 15×15 m | 0.3 m/s | 0.20 |
| extreme | 25 | 20×20 m | 0.5 m/s | 0.30 |

---

## Existing Components

The original C22 implementation includes:

- `DifficultyLevel`,
- `CURRICULUM_STAGES`,
- `CurriculumStrategy`,
- `CurriculumScheduler`,
- `CurriculumNavEnv`,
- `run_curriculum_training`.

---

## New Upgrade Added

C22 now includes:

```text
curriculum_evaluator.py
```

This evaluator compares curriculum strategies using:

- final stage reached,
- number of stage transitions,
- episodes needed to reach hard stage,
- mean success in final window,
- success trend,
- stability score,
- held-out transfer success,
- sample-efficiency score.

---

## Files

```text
22_curriculum_rl/
├── README.md
├── curriculum_rl.py
├── curriculum_evaluator.py
├── docs/
│   └── SCIENTIFIC_UPGRADE.md
├── experiments/
│   └── eval_curriculum_strategies.py
└── results/
    └── c22_curriculum_strategies.csv
```

---

## Quick Start

Run the original curriculum training stub:

```bash
python -c "
from contributions.22_curriculum_rl.curriculum_rl import run_curriculum_training
run_curriculum_training(n_episodes=500, out_csv='contributions/22_curriculum_rl/results/curriculum.csv')
"
```

Run the new curriculum strategy benchmark:

```bash
python contributions/22_curriculum_rl/experiments/eval_curriculum_strategies.py
```

This generates:

```text
contributions/22_curriculum_rl/results/c22_curriculum_strategies.csv
```

---

## Curriculum Strategies

| Strategy | Meaning |
|---|---|
| `adaptive` | Advance when rolling success rate crosses the stage threshold |
| `fixed` | Advance after a fixed number of episodes |
| `reverse` | Represents reverse-curriculum style training from easier start states |

---

## Strategy Evaluation Metrics

| Metric | Meaning |
|---|---|
| Final stage | Highest curriculum stage reached by the end |
| Stage transitions | Number of difficulty increases |
| Episodes to hard | How many episodes were needed to reach hard difficulty |
| Final-window success | Mean success rate in the last evaluation window |
| Success trend | Final-window success minus early-window success |
| Stability score | Penalizes unstable or excessive stage switching |
| Held-out transfer success | Simulated success on unseen difficulty setting |
| Sample-efficiency score | Stage-progress and success normalized by episode budget |

---

## Scientific Contribution

The upgraded C22 contribution is not simply:

> Schedule RL training difficulty.

It is stronger:

> Evaluate curriculum strategies using progression, stability, sample-efficiency, and held-out transfer metrics.

This makes curriculum learning auditable and comparable.

---

## Integration

- **Wraps:** C21 PPO navigation agent environment
- **Uses:** C18 safety shields for safe policy execution during training
- **Can use:** C12 diffusion risk maps for progressively harder risk fields
- **Can extend:** C16 federated learning for fleet-wide curriculum adaptation
- **Can trigger:** C05 safe mode when difficulty rises faster than safety competence

Recommended runtime interface:

```text
curriculum_state = {
    current_stage,
    rolling_success_rate,
    rolling_violation_rate,
    shield_intervention_rate,
    next_stage_candidate
}
```

---

## Limitations

- The benchmark uses a synthetic learning-curve simulator for reproducibility.
- It does not replace full PPO training with vectorized environments.
- Reverse curriculum is represented as a strategy label, not a full start-state generator.
- Real evaluation should use multiple random seeds, held-out maps, and actual PPO learning curves.

---

## Next Research Step

The strongest extension is safety-aware curriculum adaptation:

```text
success rate + violation rate + shield interventions
      ↓
advance, hold, or reduce difficulty
```

This would ensure the agent progresses only when it is both successful and safe.

---

## Conclusion

Contribution 22 establishes the curriculum-learning layer of DynNav.

The upgraded version makes the module stronger by comparing curriculum strategies through measurable progression, stability, and transfer metrics.
