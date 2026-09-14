from __future__ import annotations

from dynnav.experiments.safe_return_threshold_benchmark import (
    run_safe_return_threshold_benchmark,
    summarize_safe_return_threshold,
)


def test_threshold_controls_commitment_for_single_module() -> None:
    records = run_safe_return_threshold_benchmark(
        module_count=1,
        closure_probabilities=(0.8,),
        thresholds=(0.1, 0.9),
    )
    loose = next(row for row in records if row.threshold == 0.1)
    strict = next(row for row in records if row.threshold == 0.9)

    assert loose.success and strict.success
    assert loose.activated_closure_count == 1
    assert loose.geometric_length == 4
    assert strict.activated_closure_count == 0
    assert strict.geometric_length == 6
    assert strict.rejected_transitions > 0


def test_stricter_threshold_never_allows_more_active_commitments_in_controlled_family() -> None:
    records = run_safe_return_threshold_benchmark(
        module_count=2,
        closure_probabilities=(0.3, 0.8),
        thresholds=(0.1, 0.5, 0.9),
    )
    for probability in (0.3, 0.8):
        rows = sorted(
            (row for row in records if row.closure_probability == probability),
            key=lambda row: row.threshold,
        )
        active = [row.activated_closure_count for row in rows if row.success]
        assert active == sorted(active, reverse=True)


def test_threshold_summary_reports_each_setting() -> None:
    records = run_safe_return_threshold_benchmark(
        module_count=1,
        closure_probabilities=(0.2, 0.8),
        thresholds=(0.3, 0.9),
    )
    summary = summarize_safe_return_threshold(records)
    assert summary["trials"] == 4
    assert set(summary["per_threshold"]) == {"0.3", "0.9"}
