# C13 Scientific Upgrade Notes — Imagined Rollout Audit

## What was already strong

Contribution 13 already introduced a strong model-based planning idea:

> Before executing an action, the robot imagines possible future trajectories in latent space and selects the sequence with the best predicted outcome.

The existing module includes:

- a lightweight RSSM-style latent dynamics model,
- posterior and prior latent updates,
- imagined rollouts,
- discounted imagined return,
- irreversibility penalty support,
- random action-sequence generation.

This gives DynNav a bridge from reactive replanning to predictive model-based decision making.

## Main weakness before this upgrade

The planner could select a best action sequence, but the selection was not very auditable.

A reviewer could ask:

> Why was this imagined future selected?

or:

> Did the world model avoid irreversible futures, or did it only maximize predicted reward?

## New contribution added

C13 now includes:

```text
rollout_auditor.py
experiments/eval_rollout_audit.py
```

The new rollout audit layer reports:

- imagined discounted return,
- action effort,
- terminal latent norm,
- recoverability proxy,
- irreversibility flag,
- final rollout score,
- selected sequence.

## New benchmark

Run:

```bash
python contributions/13_latent_world_model/experiments/eval_rollout_audit.py
```

Output:

```text
contributions/13_latent_world_model/results/c13_rollout_audit.csv
```

The benchmark compares candidate imagined sequences such as:

- cautious forward,
- aggressive forward,
- turning probe,
- retreat / recover,
- oscillatory uncertain motion.

## Reviewer-safe claim

A stronger claim after this upgrade is:

> Contribution 13 evaluates imagined action sequences using explicit rollout-level audit metrics, including predicted return, action effort, terminal latent familiarity, recoverability proxy, and irreversibility penalty.

## Relationship to other contributions

C13 connects directly to:

- C04 recoverability and irreversibility,
- C05 safe mode as a fallback when imagined futures degrade,
- C12 future occupancy risk maps as latent rollout priors,
- C22 reinforcement learning as a policy-learning extension.

## Limitations

- The RSSM is a lightweight numpy stub, not a trained DreamerV3 model.
- The recoverability proxy is based on terminal latent magnitude, not formal reachability.
- Real robot validation requires learned dynamics from logged trajectories.
- Random shooting is simple; production planning should use CEM, MPC, or gradient-based latent optimization.

## Next research step

The strongest extension is recoverability-aware latent MPC:

```text
candidate action sequences -> imagined futures -> recoverability-aware MPC selection
```

This would connect the world model directly to C04 and C05, letting the robot reject risky futures before executing them.
