# Contribution 21 — PPO Navigation Agent and Policy Safety Evaluation

[![Module](https://img.shields.io/badge/Module-21-purple)](.) [![Type](https://img.shields.io/badge/Type-Reinforcement%20Learning-blue)](.) [![Status](https://img.shields.io/badge/Status-Core%20Upgraded-brightgreen)](.)

## Plain-language summary

A reinforcement-learning navigation policy should not be judged only by training reward.

It should be evaluated by whether it:

```text
reaches the goal,
avoids collisions,
keeps reasonable distance from obstacles,
benefits from a safety shield,
and outperforms simple baselines.
```

Contribution 21 implements a PPO-style navigation agent with risk-shaped rewards. The upgraded version adds policy safety evaluation against a greedy baseline and a shielded PPO variant.

---

## Research Question

> **RQ21:** Can PPO-style reinforcement learning produce navigation policies that are effective and safe under risk-shaped rewards and runtime shielding?

This contribution studies:

- PPO-style actor-critic navigation,
- risk-shaped rewards,
- Generalized Advantage Estimation,
- rollout-based policy evaluation,
- shielded learned policies,
- safety and success metrics.

---

## Reward Structure

```text
r = r_progress - λ_risk · r_risk - λ_collision · r_collision + r_goal
```

| Component | Value / Meaning |
|---|---|
| Step penalty | small cost per step |
| Progress reward | reward for reducing goal distance |
| Obstacle penalty | penalty when obstacle distance becomes small |
| Collision penalty | strong penalty for unsafe contact |
| Goal reward | reward for reaching the goal |

---

## Existing Components

The original C21 implementation includes:

- `PPOConfig`,
- `ActorNetwork`,
- `CriticNetwork`,
- `RolloutBuffer`,
- `NavEnv`,
- `PPOAgent`,
- rollout collection,
- GAE computation,
- PPO-style loss logging.

---

## New Upgrade Added

C21 now includes:

```text
ppo_policy_evaluator.py
```

This evaluator compares:

- PPO actor,
- shielded PPO actor,
- greedy goal-directed baseline.

It reports:

- success rate,
- collision rate,
- mean reward,
- mean episode length,
- mean minimum obstacle distance,
- mean final goal distance,
- shield intervention rate.

---

## Files

```text
21_ppo_navigation_agent/
├── README.md
├── ppo_nav_agent.py
├── ppo_policy_evaluator.py
├── docs/
│   └── SCIENTIFIC_UPGRADE.md
├── experiments/
│   └── eval_policy_safety.py
└── results/
    └── c21_policy_safety.csv
```

---

## Quick Start

Train the PPO skeleton:

```python
from contributions.21_ppo_navigation_agent.ppo_nav_agent import PPOAgent, PPOConfig, NavEnv

cfg = PPOConfig(obs_dim=14, hidden_dim=128, rollout_len=512)
agent = PPOAgent(cfg)
env = NavEnv(cfg)

training_log = agent.train(env, n_updates=100)
print(f"Final reward: {training_log[-1]['mean_ep_reward']:.2f}")
```

Run the new policy-safety benchmark:

```bash
python contributions/21_ppo_navigation_agent/experiments/eval_policy_safety.py
```

This generates:

```text
contributions/21_ppo_navigation_agent/results/c21_policy_safety.csv
```

---

## Policy Evaluation Metrics

| Metric | Meaning |
|---|---|
| Success rate | Fraction of episodes reaching the goal |
| Collision rate | Fraction of episodes entering collision distance |
| Mean reward | Average episode reward |
| Mean episode length | Average number of executed steps |
| Mean minimum obstacle distance | Average closest approach to obstacles |
| Final goal distance | Remaining distance to the goal at episode end |
| Shield intervention rate | Fraction of steps where the safety wrapper modifies action |

---

## Scientific Contribution

The upgraded C21 contribution is not simply:

> Implement a PPO training loop.

It is stronger:

> Evaluate learned and baseline navigation policies using safety-relevant outcomes and quantify the effect of runtime shielding.

This makes the RL contribution experimentally auditable.

---

## Integration

- **Uses:** C12 diffusion risk maps for future risk-shaped rewards
- **Wrapped by:** C18 formal safety shields during deployment
- **Extended by:** C22 curriculum RL for staged training
- **Can be screened by:** C13 latent world-model imagined rollouts
- **Can trigger:** C05 safe mode when policy confidence or safety margins degrade

Recommended runtime interface:

```text
policy_input = {
    observation,
    local_risk_map,
    goal_direction,
    shield_state,
    safety_margin
}
```

---

## Limitations

- The PPO implementation is a lightweight numpy skeleton.
- The actor is not truly optimized by gradient descent in the stub update.
- The environment is synthetic and low-dimensional.
- The shielded benchmark uses a lightweight correction rule, not a certified CBF/QP solver.
- Real deployment requires PyTorch PPO, vectorized environments, ROS 2 bridge, and safety validation.

---

## Next Research Step

The strongest extension is shielded PPO training:

```text
policy action
      ↓
formal shield
      ↓
safe executed action
      ↓
PPO update from shielded experience
```

This would align training-time and deployment-time safety constraints.

---

## Conclusion

Contribution 21 establishes the reinforcement-learning navigation layer of DynNav.

The upgraded version makes it stronger by adding policy-safety evaluation and baseline comparison rather than relying only on training reward.
