"""Curriculum evaluation utilities for Contribution 22.

Curriculum learning should be evaluated by more than a final reward. This module
measures stage progression, sample-efficiency proxies, stability, and transfer to
held-out difficulty levels.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from curriculum_rl import CURRICULUM_STAGES, CurriculumScheduler, CurriculumStrategy, DifficultyLevel


@dataclass(frozen=True)
class CurriculumEvalResult:
    strategy: str
    n_episodes: int
    final_stage: str
    final_stage_idx: int
    n_stage_transitions: int
    episodes_to_hard: int
    mean_success_last_window: float
    success_trend: float
    stability_score: float
    heldout_transfer_success: float
    sample_efficiency_score: float

    def to_dict(self) -> dict[str, float | int | str]:
        return asdict(self)


def synthetic_success_probability(skill: float, difficulty: DifficultyLevel) -> float:
    difficulty_score = (
        0.08 * difficulty.n_obstacles
        + 0.05 * difficulty.map_size
        + 1.2 * difficulty.obstacle_speed
        + 1.5 * difficulty.sensor_noise
        + 0.04 * difficulty.goal_dist_range[1]
    )
    return float(1.0 / (1.0 + np.exp(-(skill - difficulty_score))))


def simulate_curriculum_strategy(
    strategy: CurriculumStrategy,
    n_episodes: int = 300,
    seed: int = 42,
    window_size: int = 25,
) -> tuple[list[dict], CurriculumScheduler, float]:
    rng = np.random.default_rng(seed)
    scheduler = CurriculumScheduler(strategy=strategy, window_size=window_size, advance_every=60)
    skill = 0.45
    log: list[dict] = []

    for ep in range(1, n_episodes + 1):
        current = scheduler.current
        p_success = synthetic_success_probability(skill, current)
        success = bool(rng.random() < p_success)
        advanced = scheduler.record_episode(success)
        # Learning progresses more when the task is challenging but possible.
        skill += 0.010 + 0.020 * (1.0 - p_success) * (0.5 + float(success))
        if advanced:
            skill += 0.02
        log.append(
            {
                "episode": ep,
                "strategy": strategy.value,
                "stage": scheduler.current.name,
                "stage_idx": scheduler.current_stage_idx,
                "success": int(success),
                "success_probability": p_success,
                "skill": skill,
                "advanced": int(advanced),
            }
        )

    heldout = DifficultyLevel(
        "heldout_cluttered_dynamic",
        n_obstacles=16,
        map_size=14.0,
        obstacle_speed=0.25,
        sensor_noise=0.18,
        goal_dist_range=(5.0, 11.0),
    )
    transfer_success = synthetic_success_probability(skill, heldout)
    return log, scheduler, float(transfer_success)


def evaluate_curriculum_strategy(
    strategy: CurriculumStrategy,
    n_episodes: int = 300,
    seed: int = 42,
) -> CurriculumEvalResult:
    log, scheduler, transfer_success = simulate_curriculum_strategy(strategy, n_episodes=n_episodes, seed=seed)
    successes = np.asarray([row["success"] for row in log], dtype=float)
    stages = [row["stage_idx"] for row in log]
    hard_idx = next((i + 1 for i, idx in enumerate(stages) if idx >= 2), -1)
    last = successes[-50:] if len(successes) >= 50 else successes
    first = successes[:50] if len(successes) >= 50 else successes
    success_trend = float(np.mean(last) - np.mean(first)) if len(successes) else 0.0
    transition_count = len(scheduler.stage_history)
    stage_changes = np.asarray([row["advanced"] for row in log], dtype=float)
    stability = float(1.0 - min(1.0, np.std(stage_changes) * 5.0))
    sample_eff = float((scheduler.current_stage_idx + 1) * max(0.0, np.mean(last)) / max(1.0, n_episodes / 100.0))

    return CurriculumEvalResult(
        strategy=strategy.value,
        n_episodes=n_episodes,
        final_stage=scheduler.current.name,
        final_stage_idx=scheduler.current_stage_idx,
        n_stage_transitions=transition_count,
        episodes_to_hard=int(hard_idx),
        mean_success_last_window=float(np.mean(last)),
        success_trend=success_trend,
        stability_score=stability,
        heldout_transfer_success=float(transfer_success),
        sample_efficiency_score=sample_eff,
    )
