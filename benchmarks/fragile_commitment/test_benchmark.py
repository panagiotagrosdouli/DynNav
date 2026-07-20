"""Regression tests for the controlled counterexample benchmark."""

from benchmark import choose_route, evaluate_route
from scenario import generate_scenario


def test_counterexample_separates_risk_from_recoverability() -> None:
    scenario = generate_scenario(seed=7)
    fragile = evaluate_route(scenario, "fragile", scenario.fragile_route)
    resilient = evaluate_route(scenario, "resilient", scenario.resilient_route)

    risk_gap = abs(float(fragile["route_risk"]) - float(resilient["route_risk"]))
    recoverability_gap = float(resilient["min_recoverability"]) - float(
        fragile["min_recoverability"]
    )

    assert risk_gap < 1.0
    assert recoverability_gap > 0.05
    assert fragile["event_blocks_route"] is True
    assert resilient["event_blocks_route"] is False


def test_recoverability_aware_policy_avoids_fragile_route() -> None:
    scenario = generate_scenario(seed=3)
    fragile = evaluate_route(scenario, "fragile", scenario.fragile_route)
    resilient = evaluate_route(scenario, "resilient", scenario.resilient_route)

    assert choose_route("shortest", fragile, resilient)["route"] == "fragile"
    assert choose_route("safe_return", fragile, resilient)["route"] == "fragile"
    assert choose_route("recoverability_aware", fragile, resilient)["route"] == "resilient"
