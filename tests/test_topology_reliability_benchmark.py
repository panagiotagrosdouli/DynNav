from __future__ import annotations

import json

import pytest

from dynnav.experiments.topology_reliability_benchmark import (
    run_topology_reliability_benchmark,
    summarize_topology_reliability,
    write_topology_reliability_artifacts,
)


def test_series_bridge_estimator_matches_exact_probability() -> None:
    records = run_topology_reliability_benchmark((0.2, 0.6))
    series = [record for record in records if record.topology == "series_bridge"]

    assert [row.exact_return_probability for row in series] == pytest.approx([0.8, 0.4])
    assert [row.most_reliable_path_probability for row in series] == pytest.approx([0.8, 0.4])
    assert [row.estimator_absolute_error for row in series] == pytest.approx([0.0, 0.0])


def test_parallel_topology_exposes_single_path_redundancy_gap() -> None:
    records = run_topology_reliability_benchmark((0.2, 0.6))
    parallel = [record for record in records if record.topology == "parallel_bridges"]

    assert [row.exact_return_probability for row in parallel] == pytest.approx([0.96, 0.64])
    assert [row.most_reliable_path_probability for row in parallel] == pytest.approx([0.8, 0.4])
    assert all(row.estimator_absolute_error > 0.0 for row in parallel)


def test_structural_score_is_constant_when_only_topology_belief_changes() -> None:
    records = run_topology_reliability_benchmark((0.1, 0.5, 0.9))
    summary = summarize_topology_reliability(records)

    assert summary["series_bridge"]["structural_score_range"] == pytest.approx(0.0)
    assert summary["parallel_bridges"]["structural_score_range"] == pytest.approx(0.0)
    assert summary["series_bridge"]["exact_probability_range"] > 0.0
    assert summary["parallel_bridges"]["exact_probability_range"] > 0.0


def test_benchmark_writes_traceable_raw_and_summary_artifacts(tmp_path) -> None:
    records = run_topology_reliability_benchmark((0.25, 0.75))
    write_topology_reliability_artifacts(records, tmp_path)

    assert (tmp_path / "trials.csv").exists()
    payload = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert payload["series_bridge"]["trials"] == 2
    assert payload["parallel_bridges"]["trials"] == 2
