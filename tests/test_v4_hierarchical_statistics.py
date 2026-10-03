from __future__ import annotations

import pytest

from dynnav.experiments.statistics import hierarchical_paired_bootstrap_interval


def test_hierarchical_bootstrap_uses_equal_scenario_weighting() -> None:
    result = hierarchical_paired_bootstrap_interval(
        {
            "small": [-1.0, -1.0],
            "large": [1.0] * 20,
        },
        resamples=500,
        seed=7,
    )

    assert result.estimate == pytest.approx(0.0)
    assert result.sample_size == 2
    assert result.lower <= result.estimate <= result.upper


def test_hierarchical_bootstrap_is_reproducible() -> None:
    data = {
        "a": [-0.2, -0.1, 0.0, 0.1],
        "b": [-0.4, -0.3, -0.2, -0.1],
        "c": [0.0, 0.0, 0.1, 0.2],
    }

    first = hierarchical_paired_bootstrap_interval(data, resamples=500, seed=99)
    second = hierarchical_paired_bootstrap_interval(data, resamples=500, seed=99)

    assert first == second


def test_hierarchical_bootstrap_rejects_empty_scenarios() -> None:
    with pytest.raises(ValueError, match="at least one scenario"):
        hierarchical_paired_bootstrap_interval({}, resamples=500)

    with pytest.raises(ValueError, match="at least one observation"):
        hierarchical_paired_bootstrap_interval(
            {"empty": []},
            resamples=500,
        )
