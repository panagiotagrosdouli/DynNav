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
        ((72, 81), (73, 81)),
        ((92, 81), (93, 81)),
    )
    assert contract.blocker_cell_counts[0] > 100
    assert contract.blocker_cell_counts[1] > 100
