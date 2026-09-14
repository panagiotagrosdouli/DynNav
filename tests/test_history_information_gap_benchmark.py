from __future__ import annotations

import pytest

from dynnav.experiments.history_information_gap_benchmark import (
    run_history_information_gap_benchmark,
    summarize_history_information_gap,
)


def test_state_only_model_cannot_distinguish_counterfactual_histories() -> None:
    records = run_history_information_gap_benchmark((0.2, 0.5, 0.8))
    for row in records:
        assert row.safe_history_return_probability == pytest.approx(1.0)
        assert row.risky_history_return_probability == pytest.approx(1.0 - row.closure_probability)
        assert row.state_only_return_probability == pytest.approx(row.risky_history_return_probability)
        assert row.history_separation == pytest.approx(row.closure_probability)
        assert row.safe_history_state_only_error == pytest.approx(-row.closure_probability)
        assert row.risky_history_state_only_error == pytest.approx(0.0)


def test_information_gap_summary_tracks_probability_sweep() -> None:
    summary = summarize_history_information_gap(
        run_history_information_gap_benchmark((0.1, 0.5, 0.9))
    )
    assert summary["trials"] == 3
    assert summary["mean_history_separation"] == pytest.approx(0.5)
    assert summary["max_history_separation"] == pytest.approx(0.9)
    assert summary["mean_safe_history_state_only_error"] == pytest.approx(-0.5)
    assert summary["max_absolute_risky_history_state_only_error"] == pytest.approx(0.0)
