from statistical_analysis import mean_ci95, summarize


def _row(seed: int, planner: str, success: bool, offset: float) -> dict[str, str]:
    return {
        "seed": str(seed),
        "planner": planner,
        "mission_success": str(success),
        "path_length": str(10.0 + offset),
        "route_risk": str(1.0 + offset),
        "min_recoverability": str(0.8 - offset),
        "mean_recoverability": str(0.9 - offset),
        "commitment_loss": str(0.1 + offset),
        "bottleneck_exposure": str(0.2 + offset),
        "fragility_penalty": str(0.3 + offset),
    }


def test_mean_ci95_single_sample_is_degenerate() -> None:
    assert mean_ci95([0.5]) == (0.5, 0.5, 0.5)


def test_summarize_groups_planners_and_computes_success_rate() -> None:
    rows = [
        _row(0, "fragile", False, 0.0),
        _row(1, "fragile", True, 0.1),
        _row(0, "resilient", True, 0.0),
        _row(1, "resilient", True, 0.1),
    ]
    summary = {row["planner"]: row for row in summarize(rows)}

    assert summary["fragile"]["trials"] == 2
    assert summary["fragile"]["mission_success_rate"] == 0.5
    assert summary["resilient"]["mission_success_rate"] == 1.0
    assert summary["fragile"]["mean_path_length"] == 10.05
