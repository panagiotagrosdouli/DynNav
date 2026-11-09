from __future__ import annotations

from pathlib import Path

import numpy as np
import yaml
from PIL import Image

from scripts.analyze_lilocbench_ros1_bag import (
    fit_odom_to_ground_truth_diagnostic,
    nearest_time_deltas_ms,
    summarize,
    write_csv_artifacts,
)
from scripts.generate_lilocbench_overlay import generate_overlay


def test_nearest_timestamps_and_summary() -> None:
    assert np.allclose(nearest_time_deltas_ms([0.0, 0.1, 0.2], [0.03, 0.16]), [30.0, 40.0])
    assert summarize([]) is None
    result = summarize([1.0, 2.0, 3.0])
    assert result is not None
    assert result["count"] == 3
    assert result["median"] == 2.0


def test_bag_csv_exports_are_lf_delimited(tmp_path: Path) -> None:
    result = {
        "bag": {
            "topics": {
                "/scan": {
                    "message_types": ["sensor_msgs/msg/LaserScan"],
                    "message_count": 1,
                    "record_time_s": {"first": 2.0, "last": 2.0},
                    "header_time_s": {"first": 1.99, "last": 1.99},
                    "header_record_lag_ms": {"median": 10.0, "p95": 10.0},
                    "frame_ids": {"laser": 1},
                    "child_frame_ids": {},
                }
            }
        },
        "tf": {"edges": [{"topic": "/tf", "parent": "odom", "child": "base_link", "transform_messages": 1}]},
        "timestamp_synchronization": {
            "bag_topics_to_ground_truth_nearest_ms": {"/scan": {"count": 1, "median": 5.0}},
            "front_to_rear_scan_nearest_ms": {"count": 1, "median": 7.0},
        },
    }

    names = write_csv_artifacts(result, tmp_path)

    assert len(names) == 3
    for name in names:
        assert b"\r\n" not in (tmp_path / name).read_bytes()
    assert "odom,base_link,1" in (tmp_path / "lilocbench_dynamics_0_tf_edges.csv").read_text()


def test_odom_alignment_diagnostic_reports_held_out_error() -> None:
    times = np.arange(0.0, 100.0, 0.5)
    ground_truth = np.column_stack(
        (times, np.cos(times / 9.0) + times / 15.0, np.sin(times / 11.0) + times / 45.0)
    )
    angle = 0.37
    rotation = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
    translation = np.array([3.0, -4.0])
    target = ground_truth[:, 1:3]
    source = (rotation.T @ (target - translation).T).T
    odometry = [
        {"stamp": float(stamp), "x": float(point[0]), "y": float(point[1]), "yaw": 0.0}
        for stamp, point in zip(times, source, strict=True)
    ]

    result = fit_odom_to_ground_truth_diagnostic(odometry, ground_truth)

    assert result is not None
    assert "not an authoritative TF" in result["status"]
    assert result["train_error"]["rmse_m"] < 1e-10
    assert result["held_out_error"]["rmse_m"] < 1e-10


def test_overlay_generator_fails_if_ground_truth_hits_blocked_cell(tmp_path: Path) -> None:
    image_path = tmp_path / "map.png"
    pixels = np.full((10, 10), 255, dtype=np.uint8)
    pixels[5, 5] = 0
    Image.fromarray(pixels).save(image_path)
    yaml_path = tmp_path / "map.yaml"
    yaml_path.write_text(
        yaml.safe_dump(
            {
                "image": image_path.name,
                "resolution": 1.0,
                "origin": [0.0, 0.0, 0.0],
                "occupied_thresh": 0.65,
                "free_thresh": 0.196,
                "negate": 0,
            }
        ),
        encoding="utf-8",
    )
    poses = tmp_path / "poses.txt"
    # Image row 5 maps to ROS cell y=4 after the required vertical flip.
    poses.write_text("0 5.5 4.5 0 0 0 0 1\n1 8.5 8.5 0 0 0 0 1\n", encoding="utf-8")

    try:
        generate_overlay(yaml_path, poses, tmp_path / "overlay.svg")
    except ValueError as exc:
        assert "refusing to create a verified overlay" in str(exc)
    else:
        raise AssertionError("overlay generation must reject a trajectory sample in an occupied cell")


def test_overlay_generator_creates_licensed_reproducible_svg(tmp_path: Path) -> None:
    image_path = tmp_path / "map.png"
    Image.fromarray(np.full((12, 12), 255, dtype=np.uint8)).save(image_path)
    yaml_path = tmp_path / "map.yaml"
    yaml_path.write_text(
        yaml.safe_dump(
            {
                "image": image_path.name,
                "resolution": 0.5,
                "origin": [0.0, 0.0, 0.0],
                "occupied_thresh": 0.65,
                "free_thresh": 0.196,
                "negate": 0,
            }
        ),
        encoding="utf-8",
    )
    poses = tmp_path / "poses.txt"
    poses.write_text("0 1 1 0 0 0 0 1\n1 5 5 0 0 0 0 1\n", encoding="utf-8")
    output = tmp_path / "overlay.svg"

    result = generate_overlay(yaml_path, poses, output)

    svg = output.read_text(encoding="utf-8")
    assert result["ground_truth_pose_count"] == 2
    assert result["ground_truth_known_free_cells"] == 2
    assert "CC BY-NC-SA 4.0" in svg
    assert "static A-star" in svg
    assert "not closed loop" in svg
