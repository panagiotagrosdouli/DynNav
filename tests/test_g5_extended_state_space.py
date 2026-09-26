from __future__ import annotations

from dynnav.experiments.history_compression_state_space import (
    run_reachable_state_space_scaling,
)


def test_g5_eight_module_full_state_compression_is_large() -> None:
    row = run_reachable_state_space_scaling(module_counts=(8,))[0]
    assert row.raw_hazard_count == 16
    assert row.quotient_event_count == 8
    assert row.raw_reachable_states == 398583
    assert row.compressed_reachable_states == 207
    assert row.compression_ratio > 1900.0
    assert row.reduction_fraction > 0.999
    assert row.raw_peak_frontier > row.compressed_peak_frontier
    assert row.raw_enumeration_ms > 0.0
    assert row.compressed_enumeration_ms > 0.0
