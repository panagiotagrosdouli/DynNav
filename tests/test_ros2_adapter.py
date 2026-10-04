from types import SimpleNamespace

import pytest

from dynnav.core import Pose, Trajectory
from dynnav.ros2 import Ros2Adapter


def occupancy_message(width: int, height: int, resolution: float, data: list[int]):
    return SimpleNamespace(
        info=SimpleNamespace(width=width, height=height, resolution=resolution),
        data=data,
    )


def test_occupancy_from_message_preserves_row_major_probabilities_and_resolution():
    grid = Ros2Adapter().occupancy_from_message(
        occupancy_message(2, 2, 0.25, [0, 100, -1, 50])
    )

    assert grid.shape == (2, 2)
    assert grid.resolution == pytest.approx(0.25)
    assert grid.probability(Pose(0, 0)) == pytest.approx(0.0)
    assert grid.probability(Pose(1, 0)) == pytest.approx(1.0)
    assert grid.probability(Pose(0, 1)) == pytest.approx(0.5)
    assert grid.probability(Pose(1, 1)) == pytest.approx(0.5)


def test_occupancy_from_message_rejects_mismatched_data_length():
    with pytest.raises(ValueError, match="data length"):
        Ros2Adapter().occupancy_from_message(
            occupancy_message(2, 2, 1.0, [0, 100, -1])
        )


def test_occupancy_from_message_rejects_nonpositive_dimensions():
    with pytest.raises(ValueError, match="width and height"):
        Ros2Adapter().occupancy_from_message(
            occupancy_message(0, 2, 1.0, [])
        )


def test_command_from_trajectory_targets_next_pose():
    trajectory = Trajectory(
        poses=(Pose(1, 1), Pose(2, 1), Pose(3, 1)),
        cost=2.0,
        risk=0.0,
        recoverability=1.0,
    )

    command = Ros2Adapter().command_from_trajectory(trajectory, mode="history-aware")

    assert command.mode == "history-aware"
    assert command.target == Pose(2, 1)
