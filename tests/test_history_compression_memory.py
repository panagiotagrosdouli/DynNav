from __future__ import annotations

import pytest

from dynnav.experiments.history_compression_memory import (
    run_history_compression_memory_scaling,
)


def test_g5_memory_scaling_preserves_optimal_objective_and_return() -> None:
    rows = run_history_compression_memory_scaling(
        module_counts=(2, 3),
        recoverability_weight=2.0,
    )
    assert len(rows) == 2
    for row in rows:
        assert row.compressed_reachable_states <= row.raw_reachable_states
        assert row.raw_objective == pytest.approx(row.compressed_objective)
        assert row.raw_final_return == pytest.approx(row.compressed_final_return)
        assert row.raw_enumeration_peak_bytes > 0
        assert row.compressed_enumeration_peak_bytes > 0
        assert row.raw_planner_peak_bytes > 0
        assert row.compressed_planner_peak_bytes > 0


def test_g5_reachable_state_compression_grows_with_duplicate_modules() -> None:
    rows = run_history_compression_memory_scaling(
        module_counts=(2, 4, 6),
        recoverability_weight=0.0,
    )
    assert rows[-1].reachable_state_ratio > rows[0].reachable_state_ratio
    assert rows[-1].raw_hazard_count == 12
    assert rows[-1].quotient_event_count == 6
