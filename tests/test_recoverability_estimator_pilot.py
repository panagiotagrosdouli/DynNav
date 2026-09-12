from __future__ import annotations

import json

from dynnav.experiments.recoverability_estimator_pilot import (
    run_estimator_pilot,
    summarize_estimator_pilot,
    write_estimator_pilot_artifacts,
)


def test_pilot_is_deterministic_for_fixed_development_seeds() -> None:
    first = run_estimator_pilot((0, 1, 2), hazard_count=4)
    second = run_estimator_pilot((0, 1, 2), hazard_count=4)

    assert first == second


def test_estimators_remain_conservative_against_exact_oracle() -> None:
    records = run_estimator_pilot(tuple(range(10)), hazard_count=5)
    summary = summarize_estimator_pilot(records)

    assert summary["single_path_overestimate_count"] == 0
    assert summary["two_path_overestimate_count"] == 0


def test_two_path_estimator_is_never_worse_than_single_path_on_pilot_cases() -> None:
    records = run_estimator_pilot(tuple(range(10)), hazard_count=5)

    for row in records:
        assert row.two_path_absolute_error <= row.single_path_absolute_error + 1e-12


def test_pilot_writes_reproducible_raw_artifacts(tmp_path) -> None:
    records = run_estimator_pilot((0, 1, 2), hazard_count=4)
    write_estimator_pilot_artifacts(records, tmp_path)

    assert (tmp_path / "trials.csv").exists()
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["trials"] == 3
    assert "single_path_mae" in summary
    assert "two_path_mae" in summary
