from __future__ import annotations

import pytest

from dynnav.dependence_connectivity_interaction import (
    ConnectivityTruthTable,
    connectivity_truth_table,
    dependence_sensitivity,
    expected_return_from_joint,
)
from dynnav.planners.grid_map import GridMap


def test_parallel_redundancy_has_negative_dependence_sensitivity() -> None:
    free = {
        (0, 0), (1, 0), (2, 0),
        (0, 2), (1, 2), (2, 2),
        (0, 1), (2, 1),
    }
    obstacles = {
        (x, y)
        for x in range(3)
        for y in range(3)
        if (x, y) not in free
    }
    grid = GridMap.from_obstacles(3, 3, obstacles=obstacles)
    table = connectivity_truth_table(
        grid,
        (2, 1),
        {(0, 1)},
        (1, 0),
        (1, 2),
    )
    assert table == ConnectivityTruthTable(1, 1, 1, 0)
    assert dependence_sensitivity(table) == -1
    assert expected_return_from_joint(
        table,
        p_first=0.5,
        p_second=0.5,
        joint_closure=0.25,
    ) == pytest.approx(0.75)
    assert expected_return_from_joint(
        table,
        p_first=0.5,
        p_second=0.5,
        joint_closure=0.5,
    ) == pytest.approx(0.5)


def test_serial_cut_has_positive_dependence_sensitivity() -> None:
    grid = GridMap.from_obstacles(4, 1)
    table = connectivity_truth_table(
        grid,
        (3, 0),
        {(0, 0)},
        (1, 0),
        (2, 0),
    )
    assert table == ConnectivityTruthTable(1, 0, 0, 0)
    assert dependence_sensitivity(table) == 1
    assert expected_return_from_joint(
        table,
        p_first=0.5,
        p_second=0.5,
        joint_closure=0.25,
    ) == pytest.approx(0.25)
    assert expected_return_from_joint(
        table,
        p_first=0.5,
        p_second=0.5,
        joint_closure=0.5,
    ) == pytest.approx(0.5)


def test_irrelevant_second_hazard_has_zero_dependence_sensitivity() -> None:
    table = ConnectivityTruthTable(1, 0, 1, 0)
    assert dependence_sensitivity(table) == 0
    independent = expected_return_from_joint(
        table,
        p_first=0.4,
        p_second=0.6,
        joint_closure=0.24,
    )
    positively_dependent = expected_return_from_joint(
        table,
        p_first=0.4,
        p_second=0.6,
        joint_closure=0.4,
    )
    assert independent == pytest.approx(positively_dependent)
