"""Regression tests for paired benchmark statistics."""

from paired_tests import analyse, mcnemar_exact, wilcoxon_signed_rank


def test_wilcoxon_detects_consistent_positive_shift() -> None:
    statistic, p_value, effect, n = wilcoxon_signed_rank(
        [2, 3, 4, 5, 6, 7],
        [1, 1, 1, 1, 1, 1],
    )
    assert statistic == 0.0
    assert p_value <= 0.05
    assert effect == 1.0
    assert n == 6


def test_wilcoxon_all_ties_is_neutral() -> None:
    statistic, p_value, effect, n = wilcoxon_signed_rank([1, 2], [1, 2])
    assert statistic == 0.0
    assert p_value == 1.0
    assert effect == 0.0
    assert n == 0


def test_mcnemar_exact_detects_one_sided_discordance() -> None:
    statistic, p_value, effect, n = mcnemar_exact(
        [False] * 6,
        [True] * 6,
    )
    assert statistic == 0
    assert p_value <= 0.05
    assert effect == -1.0
    assert n == 6


def test_analysis_pairs_by_family_and_seed() -> None:
    rows = []
    for seed in range(6):
        rows.extend(
            [
                {
                    "family": "bottleneck",
                    "seed": str(seed),
                    "planner": "risk_only",
                    "path_length": "10",
                    "route_risk": "0.1",
                    "minimum_recoverability": "0.2",
                    "cumulative_recoverability_loss": "0.8",
                    "fragility_penalty": "0.9",
                    "mission_success": "false",
                },
                {
                    "family": "bottleneck",
                    "seed": str(seed),
                    "planner": "recoverability_aware",
                    "path_length": "12",
                    "route_risk": "0.11",
                    "minimum_recoverability": "0.8",
                    "cumulative_recoverability_loss": "0.2",
                    "fragility_penalty": "0.3",
                    "mission_success": "true",
                },
            ]
        )

    results = analyse(rows)
    by_metric = {result.metric: result for result in results}
    assert by_metric["mission_success"].p_value <= 0.05
    assert by_metric["minimum_recoverability"].effect_size == -1.0
    assert by_metric["fragility_penalty"].effect_size == 1.0
