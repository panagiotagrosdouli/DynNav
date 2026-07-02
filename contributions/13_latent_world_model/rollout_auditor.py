"""Imagined rollout auditing for Contribution 13.

World-model planning should not only return the best action sequence. It should
also explain why that sequence was selected and whether imagined futures preserve
recovery freedom.

This module scores candidate action sequences using interpretable rollout-level
metrics:

- imagined discounted return,
- action effort,
- terminal latent norm,
- recoverability proxy,
- irreversibility penalty,
- final rollout score.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class RolloutAuditConfig:
    gamma: float = 0.99
    effort_weight: float = 0.05
    latent_norm_weight: float = 0.02
    recoverability_weight: float = 2.0
    irreversibility_penalty: float = 5.0
    recoverability_threshold: float = 0.35


@dataclass(frozen=True)
class RolloutAuditRow:
    sequence_name: str
    horizon: int
    imagined_return: float
    action_effort: float
    terminal_latent_norm: float
    recoverability_proxy: float
    irreversible: bool
    final_score: float
    selected: bool = False

    def to_dict(self) -> dict[str, float | int | bool | str]:
        return asdict(self)


def discounted_return(rewards: Iterable[float], gamma: float = 0.99) -> float:
    total = 0.0
    discount = 1.0
    for reward in rewards:
        total += discount * float(reward)
        discount *= gamma
    return float(total)


def action_effort(action_sequence: Iterable[np.ndarray]) -> float:
    actions = [np.asarray(a, dtype=float) for a in action_sequence]
    if not actions:
        return 0.0
    return float(sum(np.linalg.norm(a) for a in actions) / len(actions))


def recoverability_proxy_from_latent(terminal_h: np.ndarray, terminal_z: np.ndarray) -> float:
    """Map terminal latent magnitude to a simple [0, 1] recovery proxy.

    This is not a formal safety guarantee. It is an interpretable audit signal:
    larger latent magnitudes are treated as less familiar / less recoverable.
    """
    norm = float(np.linalg.norm(np.concatenate([terminal_h, terminal_z])))
    return float(1.0 / (1.0 + norm))


def audit_rollouts(
    rssm,
    h0: np.ndarray,
    z0: np.ndarray,
    named_sequences: dict[str, list[np.ndarray]],
    cfg: RolloutAuditConfig | None = None,
) -> list[RolloutAuditRow]:
    cfg = cfg or RolloutAuditConfig()
    rows: list[RolloutAuditRow] = []

    for name, seq in named_sequences.items():
        rollout = rssm.imagine_rollout(h0, z0, seq)
        rewards = rollout["rewards"]
        states = rollout["states"]
        terminal_h, terminal_z = states[-1] if states else (h0, z0)
        imagined = discounted_return(rewards, gamma=cfg.gamma)
        effort = action_effort(seq)
        latent_norm = float(np.linalg.norm(np.concatenate([terminal_h, terminal_z])))
        recoverability = recoverability_proxy_from_latent(terminal_h, terminal_z)
        irreversible = recoverability < cfg.recoverability_threshold
        score = (
            imagined
            - cfg.effort_weight * effort
            - cfg.latent_norm_weight * latent_norm
            + cfg.recoverability_weight * recoverability
            - (cfg.irreversibility_penalty if irreversible else 0.0)
        )
        rows.append(
            RolloutAuditRow(
                sequence_name=name,
                horizon=len(seq),
                imagined_return=float(imagined),
                action_effort=float(effort),
                terminal_latent_norm=latent_norm,
                recoverability_proxy=float(recoverability),
                irreversible=bool(irreversible),
                final_score=float(score),
            )
        )

    if not rows:
        return rows
    best_name = max(rows, key=lambda r: r.final_score).sequence_name
    return [
        RolloutAuditRow(**{**r.to_dict(), "selected": r.sequence_name == best_name})
        for r in rows
    ]
