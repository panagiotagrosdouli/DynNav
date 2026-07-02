# C21 Scientific Upgrade Notes — PPO Policy Safety Evaluation

## What was already strong

Contribution 21 already introduced a reinforcement-learning navigation layer:

> A PPO-style policy maps observations to velocity commands using risk-shaped rewards.

The existing module includes:

- PPO configuration,
- actor and critic network stubs,
- rollout buffer,
- Generalized Advantage Estimation,
- navigation environment stub,
- PPO training loop,
- risk-shaped reward components.

This is useful because RL policies can learn reactive behaviour in dynamic environments where classical graph planning may be too slow or too rigid.

## Main weakness before this upgrade

The original contribution described training, but it did not evaluate policy outcomes against baselines.

A reviewer could ask:

> Does the learned/reactive policy reach goals safely?

or:

> What happens if we wrap the policy with a safety shield?

or:

> How does PPO compare with a simple greedy goal-directed baseline?

## New contribution added

C21 now includes:

```text
ppo_policy_evaluator.py
experiments/eval_policy_safety.py
```

The new benchmark compares:

- PPO actor,
- shielded PPO actor,
- greedy goal-directed baseline.

It reports:

- success rate,
- collision rate,
- mean episode reward,
- mean episode length,
- mean minimum obstacle distance,
- mean final goal distance,
- shield intervention rate.

## New benchmark

Run:

```bash
python contributions/21_ppo_navigation_agent/experiments/eval_policy_safety.py
```

Output:

```text
contributions/21_ppo_navigation_agent/results/c21_policy_safety.csv
```

## Reviewer-safe claim

A stronger claim after this upgrade is:

> Contribution 21 evaluates PPO navigation policies with safety-oriented outcome metrics and compares unshielded PPO, shielded PPO, and a greedy goal-directed baseline.

## Relationship to other contributions

C21 connects directly to:

- C18 formal safety shields as a runtime wrapper around learned policies,
- C12 diffusion occupancy maps for risk-shaped rewards,
- C13 latent world models for predictive policy screening,
- C22 curriculum RL for staged training,
- C05 safe mode when learned policies become unsafe.

## Limitations

- The PPO implementation is a lightweight numpy skeleton, not a production PyTorch PPO agent.
- Actor parameters are not truly optimized in the stub update step.
- The environment is synthetic and low-dimensional.
- The shielded policy uses a lightweight action correction, not a full CBF/QP solver.

## Next research step

The strongest extension is shielded PPO training:

```text
policy action -> formal shield -> safe executed action -> PPO update
```

This would train the policy under the same safety constraints used at deployment time.
