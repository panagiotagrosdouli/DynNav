from __future__ import annotations

from dynnav.experiments.side_information_learning_benchmark import (
    run_side_information_learning_benchmark,
)


def _by_policy(rows):
    return {row.policy: row for row in rows}


def test_exact_shared_sentinel_breaks_target_only_lockout() -> None:
    rows = _by_policy(
        run_side_information_learning_benchmark(
            opportunities=1000,
            true_target_probability=0.1,
            true_sentinel_probability=0.1,
            minimum_return_probability=0.7,
            confidence=0.90,
            seed=11,
        )
    )

    assert rows["target_only_credible"].target_exposures == 0
    assert rows["shared_sentinel_transfer"].target_exposures > 0
    assert rows["shared_sentinel_transfer"].first_target_exposure_step is not None
    assert rows["shared_sentinel_transfer"].false_safe_exposures == 0
    assert rows["shared_sentinel_transfer"].absolute_error < 0.05


def test_optimistic_misspecified_sentinel_can_create_false_safe_exposure() -> None:
    rows = _by_policy(
        run_side_information_learning_benchmark(
            opportunities=1000,
            true_target_probability=0.7,
            true_sentinel_probability=0.1,
            minimum_return_probability=0.7,
            confidence=0.90,
            seed=17,
        )
    )

    transfer = rows["shared_sentinel_transfer"]
    assert transfer.target_exposures > 0
    assert transfer.false_safe_exposures == transfer.target_exposures
    assert transfer.target_failures > 0
    assert rows["oracle_gate"].target_exposures == 0


def test_pessimistic_misspecified_sentinel_can_preserve_lockout() -> None:
    rows = _by_policy(
        run_side_information_learning_benchmark(
            opportunities=1000,
            true_target_probability=0.1,
            true_sentinel_probability=0.7,
            minimum_return_probability=0.7,
            confidence=0.90,
            seed=23,
        )
    )

    transfer = rows["shared_sentinel_transfer"]
    assert transfer.target_exposures == 0
    assert rows["oracle_gate"].target_exposures == 1000
