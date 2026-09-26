from __future__ import annotations

from dynnav.experiments.side_information_replication import (
    run_side_information_replication,
)


def test_side_information_replication_smoke() -> None:
    result = run_side_information_replication(
        opportunities=100,
        repetitions=2,
        seed=31,
    )
    assert result["metadata"]["repetitions"] == 2
    assert len(result["summary"]) == 4 * 3 * 3 * 3
    assert len(result["raw"]) == 4 * 3 * 3 * 2 * 3

    exact_safe = [
        row
        for row in result["summary"]
        if row["true_target_probability"] == 0.1
        and row["minimum_return_probability"] == 0.7
        and row["sentinel_condition"] == "exact_shared"
        and row["policy"] == "shared_sentinel_transfer"
    ][0]
    target_only = [
        row
        for row in result["summary"]
        if row["true_target_probability"] == 0.1
        and row["minimum_return_probability"] == 0.7
        and row["sentinel_condition"] == "exact_shared"
        and row["policy"] == "target_only_credible"
    ][0]
    assert exact_safe["target_exposures_mean"] > 0.0
    assert target_only["target_exposures_mean"] == 0.0
