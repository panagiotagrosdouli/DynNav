from __future__ import annotations

from dynnav.experiments.causal_graph_benchmark import (
    run_causal_graph_recovery_benchmark,
)
from dynnav.experiments.dependence_shift_benchmark import (
    run_dependence_shift_benchmark,
)
from dynnav.experiments.history_compression_benchmark import (
    run_history_compression_scaling,
)
from dynnav.experiments.online_calibration_benchmark import (
    run_online_calibration_benchmark,
)


def test_g1_dependence_shift_has_expected_failure_ordering() -> None:
    rows = run_dependence_shift_benchmark(trials=1000, seed=12)
    by_key = {(row.dependence, row.planner): row for row in rows}

    independent = by_key[("independent", "independence_history")]
    common = by_key[("common_cause", "independence_history")]
    anti = by_key[("anti_correlated", "independence_history")]
    robust = by_key[("common_cause", "dependence_robust_history")]

    assert 0.15 < independent.failure_rate < 0.35
    assert 0.40 < common.failure_rate < 0.60
    assert anti.failure_rate == 0.0
    assert robust.failure_rate == 0.0
    assert robust.path_length > common.path_length


def test_g3_safe_probe_stops_before_unconstrained_probe() -> None:
    rows = run_online_calibration_benchmark(
        opportunities=500,
        true_closure_probability=0.7,
        minimum_return_probability=0.5,
        seed=5,
    )
    by_policy = {row.policy: row for row in rows}
    assert by_policy["always_probe"].exposures == 500
    assert by_policy["oracle_known_probability"].exposures == 0
    assert 0 < by_policy["safe_probe"].exposures < 500
    assert by_policy["safe_probe"].return_failures < by_policy["always_probe"].return_failures


def test_g4_randomized_graph_recovery_finds_injected_edges() -> None:
    summary = run_causal_graph_recovery_benchmark(
        trials_per_pair=1000,
        seed=9,
        minimum_effect=0.15,
    )
    assert summary.true_positives == 3
    assert summary.false_positives == 0
    assert summary.false_negatives == 0
    assert summary.precision == 1.0
    assert summary.recall == 1.0


def test_g5_quotient_search_preserves_solution_and_reduces_states() -> None:
    rows = run_history_compression_scaling(module_counts=(1, 2, 3))
    for row in rows:
        assert row.raw_final_return == row.compressed_final_return
        assert row.path_length > 0
        assert row.quotient_event_count < row.raw_hazard_count or row.modules == 1
    assert rows[-1].compressed_nodes_expanded <= rows[-1].raw_nodes_expanded
