# Contribution 13 — Latent World Model and Imagined Rollout Audit

[![Module](https://img.shields.io/badge/Module-13-purple)](.) [![Type](https://img.shields.io/badge/Type-Model--Based%20RL-blue)](.) [![Status](https://img.shields.io/badge/Status-Core%20Upgraded-brightgreen)](.)

## Plain-language summary

A robot should not always learn from mistakes only after making them.

Contribution 13 gives DynNav a lightweight world-model layer. The robot maintains a latent belief state and imagines possible future action sequences before executing them.

The upgraded version adds an audit layer that explains why one imagined sequence is preferred over another.

The key idea is:

> Before the robot commits to an action, it should simulate possible futures and reject futures that look unrecoverable or irreversible.

---

## Research Question

> **RQ13:** Can latent mental rollouts reduce irreversible navigation failures compared with purely reactive replanning?

This contribution studies:

- latent world models,
- RSSM-style belief states,
- imagined rollouts,
- random shooting / model-predictive planning,
- recoverability-aware sequence scoring,
- irreversibility penalties,
- rollout auditability.

---

## Conceptual Pipeline

```text
real observation
      ↓
RSSM posterior update
      ↓
latent belief state (h, z)
      ↓
imagine candidate action sequences
      ↓
score return + effort + recoverability + irreversibility
      ↓
execute best sequence or trigger safe mode
```

---

## Existing World Model

The existing C13 implementation includes:

- `RSSMConfig`,
- `RSSM`,
- `WorldModelPlanner`,
- latent posterior update,
- prior rollout,
- reward prediction,
- discounted imagined return,
- random action-sequence generation.

This provides a compact model-based planning skeleton similar in spirit to Dreamer-style planning, while remaining lightweight and numpy-only.

---

## New Upgrade Added

C13 now includes:

```text
rollout_auditor.py
```

The new audit layer evaluates candidate imagined sequences using:

- imagined discounted return,
- action effort,
- terminal latent norm,
- recoverability proxy,
- irreversibility flag,
- final rollout score,
- selected sequence.

This makes world-model planning more explainable and scientifically auditable.

---

## Files

```text
13_latent_world_model/
├── README.md
├── latent_world_model.py
├── rollout_auditor.py
├── docs/
│   └── SCIENTIFIC_UPGRADE.md
├── experiments/
│   └── eval_rollout_audit.py
└── results/
    └── c13_rollout_audit.csv
```

---

## Quick Start

Run the rollout audit benchmark:

```bash
python contributions/13_latent_world_model/experiments/eval_rollout_audit.py
```

This generates:

```text
contributions/13_latent_world_model/results/c13_rollout_audit.csv
```

---

## Benchmark Sequences

The benchmark compares:

| Sequence | Meaning |
|---|---|
| `cautious_forward` | Low-effort forward motion |
| `aggressive_forward` | High-speed forward commitment |
| `turning_probe` | Exploratory turning motion |
| `retreat_recover` | Conservative recovery-oriented action |
| `oscillatory_uncertain` | Unstable high-effort sequence |

---

## Rollout Audit Metrics

| Metric | Meaning |
|---|---|
| Imagined return | Discounted reward predicted by the world model |
| Action effort | Average action magnitude |
| Terminal latent norm | Proxy for how unfamiliar/extreme the imagined terminal state is |
| Recoverability proxy | Interpretable proxy for future recovery freedom |
| Irreversible flag | Whether recoverability falls below threshold |
| Final score | Combined selection score |

---

## Scientific Contribution

The upgraded C13 contribution is not simply:

> Imagine future trajectories and pick the highest reward.

It is stronger:

> Audit imagined futures using return, effort, latent familiarity, recoverability, and irreversibility before selecting an action sequence.

This makes the world model useful for safety-aware planning rather than only reward prediction.

---

## Integration

- **Uses:** C04 recoverability and irreversibility concepts
- **Can trigger:** C05 safe mode when imagined futures degrade
- **Can consume:** C12 diffusion occupancy risk maps as future-risk priors
- **Supports:** C22 reinforcement learning and curriculum learning
- **Production extension:** replace numpy RSSM with PyTorch GRU / RSSM / Dreamer-style components

Recommended runtime interface:

```text
world_model_input = {
    observation,
    previous_action,
    candidate_sequences,
    recoverability_checker,
    risk_prior
}
```

---

## Limitations

- The RSSM is a lightweight numpy stub, not a trained DreamerV3 implementation.
- The recoverability proxy is based on terminal latent magnitude, not formal reachability.
- The benchmark is synthetic and intended for auditability.
- Real use requires training on logged trajectories and validating imagined rollouts against real futures.
- Random shooting should eventually be replaced with CEM or MPC-style optimization.

---

## Next Research Step

The strongest extension is recoverability-aware latent MPC:

```text
candidate action sequences
      ↓
imagined futures
      ↓
recoverability-aware MPC selection
      ↓
execution or safe-mode fallback
```

This would connect the world model directly to C04 and C05.

---

## Conclusion

Contribution 13 establishes the latent predictive-planning layer of DynNav.

The upgraded version makes the module more research-ready by adding auditable rollout metrics for return, effort, recoverability, and irreversibility.
