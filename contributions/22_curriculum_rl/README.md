# Contribution 22 — Curriculum RL Training and Strategy Evaluation

[Back to the repository README](../../README.md)

## Purpose

This contribution studies adaptive difficulty scheduling for navigation reinforcement learning and compares curriculum strategies using synthetic evaluation metrics.

## Maturity

**Research Prototype / Synthetic Validation.** The repository includes curriculum scheduling and evaluation code. It does not establish sample-efficiency improvements for a production PPO policy, ROS2 deployment, or real-robot generalization.

## Difficulty dimensions

Curriculum stages may vary obstacle count, map size, obstacle speed, and sensor noise. The scheduler can advance, hold, or reduce difficulty based on measured training signals.

## Implementation

- [`curriculum_rl.py`](curriculum_rl.py)
- [`curriculum_evaluator.py`](curriculum_evaluator.py)
- [`experiments/eval_curriculum_strategies.py`](experiments/eval_curriculum_strategies.py)
- [`docs/SCIENTIFIC_UPGRADE.md`](docs/SCIENTIFIC_UPGRADE.md)

## Run the curriculum training stub

The directory name begins with a number, so use `importlib` rather than a direct Python import statement:

```bash
python -c "import importlib; module = importlib.import_module('contributions.22_curriculum_rl.curriculum_rl'); module.run_curriculum_training(n_episodes=500, out_csv='contributions/22_curriculum_rl/results/curriculum.csv')"
```

## Run the strategy benchmark

```bash
python contributions/22_curriculum_rl/experiments/eval_curriculum_strategies.py
```

Expected generated output:

```text
contributions/22_curriculum_rl/results/c22_curriculum_strategies.csv
```

## Evaluation fields

- final stage reached;
- number of stage transitions;
- episodes required to reach a target stage;
- final-window success;
- success trend;
- stability score;
- held-out synthetic transfer;
- sample-efficiency proxy.

## Limitations

- The committed benchmark uses synthetic learning-curve behavior.
- Reverse curriculum is not a full start-state generator here.
- Multiple seeds and actual policy-learning curves are required for stronger claims.
- No hardware or ROS2 validation is claimed.
