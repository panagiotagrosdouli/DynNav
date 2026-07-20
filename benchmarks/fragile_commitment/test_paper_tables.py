from paper_tables import aggregate


def _row(family: str, planner: str, seed: int, success: bool, risk: float) -> dict[str, str]:
    return {
        "family": family,
        "planner": planner,
        "seed": str(seed),
        "mission_success": str(success),
        "path_length": "10",
        "route_risk": str(risk),
        "minimum_recoverability": "0.8",
        "cumulative_recoverability_loss": "0.2",
        "fragility_penalty": "0.3",
    }


def test_aggregate_preserves_planner_order_and_overall_rows() -> None:
    rows = [
        _row("open", "recoverability_aware", 0, True, 0.2),
        _row("open", "risk_only", 0, False, 0.1),
        _row("bottleneck", "recoverability_aware", 0, True, 0.3),
        _row("bottleneck", "risk_only", 0, True, 0.2),
    ]
    summary = aggregate(rows)
    overall = [row for row in summary if row["family"] == "overall"]
    assert [row["planner"] for row in overall] == ["risk_only", "recoverability_aware"]
    assert overall[0]["mission_success"] == "0.5000"
    assert overall[1]["mission_success"] == "1.0000"


def test_aggregate_reports_family_specific_means() -> None:
    rows = [
        _row("open", "risk_only", 0, True, 0.1),
        _row("open", "risk_only", 1, False, 0.3),
    ]
    summary = aggregate(rows)
    open_row = next(row for row in summary if row["family"] == "open")
    assert open_row["n"] == "2"
    assert open_row["route_risk"] == "0.2000"
    assert open_row["mission_success"] == "0.5000"
