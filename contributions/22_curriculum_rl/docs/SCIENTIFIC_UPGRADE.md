# C22 Scientific Upgrade Notes — Curriculum Strategy Evaluation

## What was already strong

Contribution 22 already introduced a useful reinforcement-learning training idea:

> Start the navigation agent in easy environments and progressively increase task difficulty as competence improves.

The existing module includes:

- difficulty levels,
- adaptive curriculum scheduler,
- fixed schedule option,
- reverse curriculum option,
- curriculum-aware navigation environment,
- training log generation.

This is important because direct RL training on difficult navigation tasks can be sample-inefficient and unstable.

## Main weakness before this upgrade

The original module described curriculum scheduling, but did not evaluate the curriculum itself.

A reviewer could ask:

> Does the curriculum actually progress through difficulty stages?

or:

> Which strategy is better: adaptive, fixed, or reverse?

or:

> Does the learned competence transfer to a held-out difficulty setting?

## New contribution added

C22 now includes:

```text
curriculum_evaluator.py
experiments/eval_curriculum_strategies.py
```

The new benchmark compares:

- adaptive curriculum,
- fixed curriculum,
- reverse curriculum.

It reports:

- final stage reached,
- number of stage transitions,
- episodes needed to reach hard stage,
- mean success in the final window,
- success trend,
- stability score,
- held-out transfer success,
- sample-efficiency score.

## New benchmark

Run:

```bash
python contributions/22_curriculum_rl/experiments/eval_curriculum_strategies.py
```

Output:

```text
contributions/22_curriculum_rl/results/c22_curriculum_strategies.csv
```

## Reviewer-safe claim

A stronger claim after this upgrade is:

> Contribution 22 evaluates curriculum RL strategies using progression, stability, sample-efficiency, and held-out transfer metrics, rather than only logging curriculum episodes.

## Relationship to other contributions

C22 connects directly to:

- C21 PPO navigation agent as the underlying policy learner,
- C18 safety shields for safe policy execution during training,
- C12 diffusion risk maps for progressively harder risk shaping,
- C16 federated learning for fleet-wide policy adaptation.

## Limitations

- The benchmark uses a synthetic learning-curve simulator for reproducibility.
- It does not replace full PPO training on real environments.
- Reverse curriculum is represented as a strategy label, not a full start-state generator.
- Real validation should use vectorized training environments and multiple random seeds.

## Next research step

The strongest extension is safety-aware curriculum adaptation:

```text
success rate + violation rate + shield interventions -> next difficulty stage
```

This would connect C22 directly to C18 and ensure that advancement requires both performance and safety.
