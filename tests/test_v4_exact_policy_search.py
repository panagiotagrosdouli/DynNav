from __future__ import annotations

from dynnav.experiments.v4_exact_policy_search import (
    run_exact_policy_search,
    summarize_exact_policy_search,
)


def test_exact_policy_search_produces_comparable_tiny_world_records() -> None:
    records = run_exact_policy_search(candidates=4, seed=2026100305)

    assert len(records) == 4
    for row in records:
        assert row.hazard_count in {1, 2}
        assert row.horizon >= row.shortest_distance
        assert row.exact_states_evaluated > 0
        if row.exact_success and row.receding_success:
            assert row.first_action_regret >= -1e-9


def test_exact_policy_search_is_reproducible() -> None:
    first = run_exact_policy_search(candidates=2, seed=17)
    second = run_exact_policy_search(candidates=2, seed=17)

    assert first == second


def test_exact_policy_search_summary_does_not_require_a_disagreement() -> None:
    records = run_exact_policy_search(candidates=3, seed=23)
    summary = summarize_exact_policy_search(records)

    assert summary["candidate_count"] == 3
    assert 0 <= summary["comparable_count"] <= 3
    assert 0 <= summary["action_disagreement_count"] <= summary["comparable_count"]
    assert (
        0
        <= summary["positive_first_action_regret_count"]
        <= summary["comparable_count"]
    )
