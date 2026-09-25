from __future__ import annotations

from dynnav.experiments.risk_budget_replication import run_risk_budget_replication


def test_risk_budget_replication_smoke() -> None:
    result = run_risk_budget_replication(
        opportunities=100,
        repetitions=2,
        seed=11,
    )
    assert result["metadata"]["repetitions"] == 2
    assert len(result["summary"]) == 4 * 3 * 6
    assert len(result["raw"]) == 4 * 3 * 2 * 6

    summaries = {
        (
            row["true_closure_probability"],
            row["minimum_return_probability"],
            row["policy"],
        ): row
        for row in result["summary"]
    }
    assert summaries[(0.3, 0.7, "credible_gate")]["exposures_mean"] == 0.0
    assert summaries[(0.3, 0.7, "risk_budget_20")]["exposures_mean"] > 0.0
