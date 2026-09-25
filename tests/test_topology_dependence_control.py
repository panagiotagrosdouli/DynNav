from __future__ import annotations

import pytest

from dynnav.experiments.topology_dependence_control import (
    run_topology_dependence_control,
)


def test_g1_dependence_effect_reverses_with_topology() -> None:
    rows = run_topology_dependence_control()
    by_key = {
        (row.topology, row.dependence): row.return_probability
        for row in rows
    }

    assert by_key[("parallel_redundant", "independent")] == pytest.approx(0.75)
    assert by_key[("parallel_redundant", "common_cause")] == pytest.approx(0.50)
    assert by_key[("parallel_redundant", "anti_correlated")] == pytest.approx(1.00)

    assert by_key[("serial_cut", "independent")] == pytest.approx(0.25)
    assert by_key[("serial_cut", "common_cause")] == pytest.approx(0.50)
    assert by_key[("serial_cut", "anti_correlated")] == pytest.approx(0.00)
