from __future__ import annotations

from dynnav.experiments.causal_effect_sweep import (
    run_confounding_propensity_control,
    run_randomized_ipw_sweep,
)


def test_randomized_ipw_recovers_large_injected_effect() -> None:
    rows = run_randomized_ipw_sweep(
        sample_sizes=(4_000,),
        propensities=(0.5,),
        effects=(0.0, 0.4),
        repetitions=12,
        seed=17,
    )
    by_effect = {row.true_ate: row for row in rows}
    assert abs(by_effect[0.0].bias) < 0.05
    assert abs(by_effect[0.4].bias) < 0.05
    assert by_effect[0.4].positive_interval_rate > 0.9
    assert by_effect[0.0].positive_interval_rate < 0.25


def test_correct_record_propensity_removes_spurious_confounding_effect() -> None:
    corrected, misspecified = run_confounding_propensity_control(
        sample_size=8_000,
        repetitions=12,
        seed=23,
    )
    assert abs(corrected.mean_estimate) < 0.05
    assert abs(misspecified.mean_estimate) > 0.25
    assert corrected.rmse < misspecified.rmse
    assert misspecified.positive_interval_rate > 0.9
