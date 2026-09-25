from __future__ import annotations

from dynnav.experiments.history_compression_state_space import (
    run_reachable_state_space_scaling,
)
from dynnav.experiments.safe_learning_lockout_benchmark import (
    run_safe_learning_lockout_benchmark,
)
from dynnav.online_hazard_learning import (
    BetaClosurePosterior,
    conservative_return_lower_bound,
)


def test_g3_credible_gate_exposes_learning_lockout() -> None:
    prior = BetaClosurePosterior(1.0, 3.0)
    assert conservative_return_lower_bound(prior, confidence=0.90) < 0.7

    rows = run_safe_learning_lockout_benchmark(
        opportunities=500,
        true_closure_probability=0.3,
        minimum_return_probability=0.7,
        confidence=0.90,
        seed=19,
    )
    by_policy = {row.policy: row for row in rows}

    assert by_policy["credible_lower_gate"].exposures == 0
    assert by_policy["oracle_gate"].exposures == 500
    assert 0 < by_policy["posterior_mean_gate"].exposures < 500


def test_g5_full_reachable_state_quotient_reduces_state_space() -> None:
    rows = run_reachable_state_space_scaling(module_counts=(1, 2, 3, 4))
    assert all(
        row.compressed_reachable_states <= row.raw_reachable_states
        for row in rows
    )
    assert rows[-1].compressed_reachable_states < rows[-1].raw_reachable_states
    assert rows[-1].compression_ratio > rows[0].compression_ratio
