from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("paper_figures.py")
SPEC = importlib.util.spec_from_file_location("fragile_commitment_paper_figures", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _row(family: str, planner: str, success: str, recoverability: str) -> dict[str, str]:
    return {
        "family": family,
        "seed": "0",
        "planner": planner,
        "mission_success": success,
        "minimum_recoverability": recoverability,
        "cumulative_recoverability_loss": "0.2",
        "fragility_penalty": "0.3",
        "route_risk": "0.1",
        "path_length": "12.0",
    }


def test_aggregate_preserves_family_and_planner_groups() -> None:
    rows = [
        _row("bottleneck", "risk_only", "false", "0.2"),
        _row("bottleneck", "risk_only", "true", "0.4"),
        _row("bottleneck", "recoverability_aware", "true", "0.9"),
    ]

    summary = MODULE.aggregate(rows)

    assert summary["bottleneck"]["risk_only"]["mission_success"] == 0.5
    assert summary["bottleneck"]["risk_only"]["minimum_recoverability"] == 0.3
    assert summary["bottleneck"]["recoverability_aware"]["mission_success"] == 1.0


def test_planner_sequence_uses_canonical_order_then_unknown_names() -> None:
    planners = {"custom", "recoverability_aware", "shortest", "risk_only"}
    assert MODULE._planner_sequence(planners) == [
        "shortest",
        "risk_only",
        "recoverability_aware",
        "custom",
    ]
