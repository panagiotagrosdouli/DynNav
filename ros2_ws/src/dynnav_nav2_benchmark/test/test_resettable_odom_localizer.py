from __future__ import annotations

import math

import pytest

from dynnav_nav2_benchmark.resettable_odom_localizer import (
    PlanarPose,
    apply_planar_transform,
    map_to_odom_alignment,
)


def _angle_error(first: float, second: float) -> float:
    return math.atan2(math.sin(first - second), math.cos(first - second))


@pytest.mark.parametrize(
    ("desired", "odom"),
    (
        (PlanarPose(0.0, 0.0, 0.0), PlanarPose(0.0, 0.0, 0.0)),
        (PlanarPose(1.0, -2.0, 0.0), PlanarPose(3.0, 4.0, 0.0)),
        (
            PlanarPose(1.0, 2.0, math.pi / 2.0),
            PlanarPose(-3.0, 0.5, -math.pi / 4.0),
        ),
    ),
)
def test_map_to_odom_alignment_maps_current_odom_pose_to_frozen_start(
    desired: PlanarPose,
    odom: PlanarPose,
) -> None:
    transform = map_to_odom_alignment(
        desired_map_base=desired,
        current_odom_base=odom,
    )
    mapped = apply_planar_transform(transform, odom)

    assert mapped.x == pytest.approx(desired.x)
    assert mapped.y == pytest.approx(desired.y)
    assert _angle_error(mapped.yaw, desired.yaw) == pytest.approx(0.0)


def test_alignment_preserves_relative_odometry_motion() -> None:
    start = PlanarPose(0.0, 0.0, 0.0)
    reset_odom = PlanarPose(5.0, -2.0, 0.3)
    transform = map_to_odom_alignment(
        desired_map_base=start,
        current_odom_base=reset_odom,
    )

    later = PlanarPose(
        reset_odom.x + math.cos(reset_odom.yaw),
        reset_odom.y + math.sin(reset_odom.yaw),
        reset_odom.yaw,
    )
    mapped = apply_planar_transform(transform, later)

    assert mapped.x == pytest.approx(1.0)
    assert mapped.y == pytest.approx(0.0)
    assert _angle_error(mapped.yaw, 0.0) == pytest.approx(0.0)
