"""Test real core-oracle integration for the interactive history demo."""
from __future__ import annotations

import pytest

from dynnav_dashboard.history_lab import (
    CLOSURE, ENDPOINT, RISKY_HISTORY, SAFE_HISTORY, TRIGGER,
    compare_histories, small_world,
)


@pytest.mark.parametrize("p", [0.0, 0.1, 0.5, 0.8, 1.0])
def test_same_endpoint_information_gap(p):
    assert SAFE_HISTORY[-1] == RISKY_HISTORY[-1] == ENDPOINT
    assert TRIGGER in tuple(zip(RISKY_HISTORY, RISKY_HISTORY[1:]))
    assert TRIGGER not in tuple(zip(SAFE_HISTORY, SAFE_HISTORY[1:]))
    result = compare_histories(p)
    assert result.safe_return_probability == pytest.approx(1.0)
    assert result.risky_return_probability == pytest.approx(1.0 - p)
    assert result.separation == pytest.approx(p)
    assert result.endpoint_only_minimax_error_bound == pytest.approx(p / 2)


def test_closure_is_the_only_return_bottleneck():
    grid = small_world()
    assert grid.passable(CLOSURE)
    assert grid.neighbors4((0, 2)) == [(1, 2)]
    assert grid.neighbors4((1, 2)) == [(2, 2)]


@pytest.mark.parametrize("p", [-0.01, 1.01])
def test_invalid_probability_is_rejected(p):
    with pytest.raises(ValueError, match="probability"):
        compare_histories(p)
