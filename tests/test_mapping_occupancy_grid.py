from __future__ import annotations

import math

import numpy as np
import pytest

from dynnav.mapping import (
    InverseSensorModel,
    OccupancyBeliefGrid,
    OccupancyGridMetadata,
    PlanarLaserScan,
)


def make_grid() -> OccupancyBeliefGrid:
    return OccupancyBeliefGrid(
        OccupancyGridMetadata(
            width=10,
            height=8,
            resolution=1.0,
            origin_x=-2.0,
            origin_y=-1.0,
        )
    )


def make_scan(ranges: tuple[float, ...], *, timestamp: float = 1.0) -> PlanarLaserScan:
    return PlanarLaserScan(
        ranges=ranges,
        angle_min=0.0,
        angle_increment=math.pi / 2.0,
        range_min=0.1,
        range_max=6.0,
        timestamp=timestamp,
    )


def test_metadata_rejects_invalid_geometry() -> None:
    with pytest.raises(ValueError, match="width and height"):
        OccupancyGridMetadata(width=0, height=2, resolution=1.0)
    with pytest.raises(ValueError, match="resolution"):
        OccupancyGridMetadata(width=2, height=2, resolution=float("nan"))
    with pytest.raises(ValueError, match="frame_id"):
        OccupancyGridMetadata(width=2, height=2, resolution=1.0, frame_id="")


def test_inverse_sensor_model_validates_probability_ordering() -> None:
    with pytest.raises(ValueError, match="free_probability"):
        InverseSensorModel(free_probability=0.6)
    with pytest.raises(ValueError, match="occupied_probability"):
        InverseSensorModel(occupied_probability=0.4)
    with pytest.raises(ValueError, match="strictly inside"):
        InverseSensorModel(maximum_probability=1.0)


def test_world_grid_round_trip_returns_cell_center() -> None:
    grid = make_grid()
    assert grid.world_to_grid((-1.8, -0.8)) == (0, 0)
    assert grid.grid_to_world((0, 0)) == pytest.approx((-1.5, -0.5))
    assert grid.world_to_grid(grid.grid_to_world((7, 5))) == (7, 5)
    assert grid.world_to_grid((-2.01, 0.0)) is None
    with pytest.raises(IndexError):
        grid.grid_to_world((10, 0))


def test_single_hit_marks_traversed_cells_free_and_endpoint_occupied() -> None:
    grid = make_grid()
    stats = grid.update_scan(sensor_position=(0.5, 1.5), sensor_yaw=0.0, scan=make_scan((3.0,)))

    assert stats.processed_beams == 1
    assert stats.ignored_beams == 0
    assert stats.free_cell_updates == 2
    assert stats.occupied_cell_updates == 1
    assert grid.probability((3, 2)) < 0.5
    assert grid.probability((4, 2)) < 0.5
    assert grid.probability((5, 2)) > 0.5
    assert grid.probability((2, 2)) == pytest.approx(0.5)


def test_no_return_marks_ray_free_without_false_terminal_obstacle() -> None:
    grid = make_grid()
    stats = grid.update_scan(
        sensor_position=(0.5, 1.5),
        sensor_yaw=0.0,
        scan=make_scan((float("inf"),)),
    )

    assert stats.processed_beams == 1
    assert stats.occupied_cell_updates == 0
    assert stats.free_cell_updates > 0
    assert np.max(grid.probability_grid()) <= 0.5


def test_out_of_map_hit_is_clipped_and_never_marked_occupied() -> None:
    grid = make_grid()
    scan = PlanarLaserScan(
        ranges=(100.0,),
        angle_min=0.0,
        angle_increment=1.0,
        range_min=0.1,
        range_max=100.0,
        timestamp=2.0,
    )
    stats = grid.update_scan(sensor_position=(0.5, 1.5), sensor_yaw=0.0, scan=scan)

    assert stats.processed_beams == 1
    assert stats.occupied_cell_updates == 0
    assert grid.probability((9, 2)) < 0.5


def test_invalid_beams_are_ignored_without_mutating_grid() -> None:
    grid = make_grid()
    before = grid.log_odds.copy()
    scan = make_scan((float("nan"), 0.0, 0.05))
    stats = grid.update_scan(sensor_position=(0.5, 1.5), sensor_yaw=0.0, scan=scan)

    assert stats.processed_beams == 0
    assert stats.ignored_beams == 3
    np.testing.assert_array_equal(grid.log_odds, before)


def test_repeated_evidence_saturates_at_configured_bounds() -> None:
    model = InverseSensorModel(minimum_probability=0.1, maximum_probability=0.9)
    grid = OccupancyBeliefGrid(
        OccupancyGridMetadata(width=10, height=4, resolution=1.0),
        model,
    )
    scan = PlanarLaserScan(
        ranges=(3.0,),
        angle_min=0.0,
        angle_increment=1.0,
        range_min=0.1,
        range_max=8.0,
        timestamp=1.0,
    )

    for timestamp in range(1, 100):
        grid.update_scan((0.5, 0.5), 0.0, PlanarLaserScan(**{**scan.__dict__, "timestamp": float(timestamp)}))

    assert grid.probability((3, 0)) == pytest.approx(0.9)
    assert grid.probability((1, 0)) == pytest.approx(0.1)


def test_dynamic_decay_relaxes_stale_evidence_toward_prior() -> None:
    grid = make_grid()
    grid.update_scan((0.5, 1.5), 0.0, make_scan((3.0,), timestamp=1.0))
    occupied_before = grid.probability((5, 2))

    decayed = grid.decay_dynamic_evidence(current_time=11.0, half_life=10.0)

    assert decayed == 3
    assert 0.5 < grid.probability((5, 2)) < occupied_before
    assert grid.probability((5, 2)) == pytest.approx(0.6, abs=1.0e-12)


def test_decay_respects_stale_grace_period() -> None:
    grid = make_grid()
    grid.update_scan((0.5, 1.5), 0.0, make_scan((3.0,), timestamp=5.0))
    before = grid.log_odds.copy()

    assert grid.decay_dynamic_evidence(current_time=8.0, half_life=2.0, stale_after=5.0) == 0
    np.testing.assert_array_equal(grid.log_odds, before)


def test_ros_compatible_export_preserves_unknown_cells() -> None:
    grid = make_grid()
    values = grid.occupancy_values()
    assert values.dtype == np.int8
    assert np.all(values == -1)

    grid.update_scan((0.5, 1.5), 0.0, make_scan((3.0,)))
    values = grid.occupancy_values()
    assert values[2, 3] == 0
    assert values[2, 5] == 100
    assert values[0, 0] == -1


def test_public_arrays_are_read_only_views() -> None:
    grid = make_grid()
    with pytest.raises(ValueError):
        grid.log_odds[0, 0] = 2.0
    with pytest.raises(ValueError):
        grid.observed_mask[0, 0] = True


def test_sensor_origin_outside_map_is_rejected() -> None:
    grid = make_grid()
    with pytest.raises(ValueError, match="outside"):
        grid.update_scan((-100.0, -100.0), 0.0, make_scan((1.0,)))


def test_scan_validation_rejects_invalid_bounds_and_metadata() -> None:
    with pytest.raises(ValueError, match="ranges"):
        make_scan(())
    with pytest.raises(ValueError, match="range bounds"):
        PlanarLaserScan((1.0,), 0.0, 1.0, 2.0, 1.0, 0.0)
    with pytest.raises(ValueError, match="angle_increment"):
        PlanarLaserScan((1.0,), 0.0, 0.0, 0.1, 2.0, 0.0)
