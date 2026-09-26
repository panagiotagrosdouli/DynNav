# ruff: noqa: I001

from pathlib import Path

from dynnav_nav2_benchmark.canonical_g1_contract import evaluate_canonical_g1_topology


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def test_canonical_g1_assets_realize_parallel_redundant_truth_table() -> None:
    contract = evaluate_canonical_g1_topology(
        map_yaml=PACKAGE_ROOT / "maps" / "g1_parallel_corridor.yaml",
        scenario_yaml=PACKAGE_ROOT / "config" / "sandbox_correlated_history_events.yaml",
    )
    assert (contract.f00, contract.f10, contract.f01, contract.f11) == (1, 1, 1, 0)
    assert contract.interaction == -1
    assert contract.trigger_cells == (
        ((72, 104), (73, 104)),
        ((92, 104), (93, 104)),
    )
    assert contract.trigger_gate_edge_counts == (41, 41)
    assert contract.trigger_gate_full_corridor_cuts == (True, True)
    assert contract.independence_route.steps == 108
    assert contract.independence_route.total_cost == 204.0
    assert contract.independence_route.final_active_mask == 3
    assert contract.independence_route.trigger_crossings == (True, True)
    assert contract.robust_route.steps == 230
    assert contract.robust_route.total_cost == 230.0
    assert contract.robust_route.final_active_mask == 0
    assert contract.robust_route.trigger_crossings == (False, False)
    assert contract.blocker_cell_counts[0] > 300
    assert contract.blocker_cell_counts[1] > 300
