#!/usr/bin/env python3
"""Decode and audit a LILocBench ROS1 bag without starting a ROS graph."""

from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any

import numpy as np

DATASET_PAGE = "https://www.ipb.uni-bonn.de/html/projects/localization_benchmark/"


def summarize(values: list[float]) -> dict[str, float | int] | None:
    """Summarize finite numeric observations with reproducible quantiles."""
    if not values:
        return None
    finite = [value for value in values if math.isfinite(value)]
    if not finite:
        return None
    return {
        "count": len(finite),
        "min": min(finite),
        "median": median(finite),
        "p95": float(np.percentile(finite, 95)),
        "max": max(finite),
    }


def nearest_time_deltas_ms(reference: list[float], query: list[float]) -> list[float]:
    """Return each query's distance to the nearest reference timestamp."""
    if not reference:
        return []
    ordered = sorted(reference)
    deltas: list[float] = []
    for stamp in query:
        index = bisect.bisect_left(ordered, stamp)
        candidates = ordered[max(0, index - 1) : min(len(ordered), index + 1)]
        deltas.append(min(abs(stamp - candidate) for candidate in candidates) * 1000.0)
    return deltas


def fit_odom_to_ground_truth_diagnostic(
    odometry: list[dict[str, float]], ground_truth: np.ndarray
) -> dict[str, Any] | None:
    """Fit a diagnostic planar rigid transform on the first 70%, report held-out error.

    This transform is not a TF transform and is never used for map overlay. It is
    reported solely to check whether a single rigid alignment is adequate.
    """
    if len(odometry) < 10 or len(ground_truth) < 10:
        return None
    gt_times = ground_truth[:, 0]
    odom_times = np.array([item["stamp"] for item in odometry], dtype=np.float64)
    valid = (odom_times >= gt_times[0]) & (odom_times <= gt_times[-1])
    odom = np.array([[item["x"], item["y"]] for item in odometry], dtype=np.float64)[valid]
    times = odom_times[valid]
    if len(times) < 10:
        return None
    target = np.column_stack(
        [np.interp(times, gt_times, ground_truth[:, axis]) for axis in (1, 2)]
    )
    split = max(5, min(len(times) - 1, int(0.7 * len(times))))
    source_train = odom[:split]
    target_train = target[:split]
    source_center = source_train.mean(axis=0)
    target_center = target_train.mean(axis=0)
    u, _, vt = np.linalg.svd((source_train - source_center).T @ (target_train - target_center))
    row_rotation = u @ vt
    if np.linalg.det(row_rotation) < 0:
        u[:, -1] *= -1
        row_rotation = u @ vt
    column_rotation = row_rotation.T
    translation = target_center - column_rotation @ source_center
    predicted = (column_rotation @ odom.T).T + translation
    residual = np.linalg.norm(predicted - target, axis=1)

    def error_summary(values: np.ndarray) -> dict[str, float]:
        return {
            "rmse_m": float(np.sqrt(np.mean(values**2))),
            "median_m": float(np.median(values)),
            "p95_m": float(np.percentile(values, 95)),
            "max_m": float(np.max(values)),
        }

    return {
        "status": "diagnostic only; not an authoritative TF and not used for map overlay",
        "fit_fraction": split / len(times),
        "transform_odom_to_gt_xy": {
            "rotation_matrix": column_rotation.tolist(),
            "translation_m": translation.tolist(),
            "yaw_deg": math.degrees(math.atan2(column_rotation[1, 0], column_rotation[0, 0])),
        },
        "train_error": error_summary(residual[:split]),
        "held_out_error": error_summary(residual[split:]),
        "paired_messages": len(times),
    }


def analyze_bag(bag_path: Path, ground_truth_path: Path | None = None) -> dict[str, Any]:
    """Read every ROS1 message in bag-time order and audit timing, frames, and sensors."""
    try:
        from rosbags.rosbag1 import Reader
        from rosbags.typesys import Stores, get_types_from_msg, get_typestore
    except ImportError as exc:
        raise RuntimeError(
            "ROS1 bag support requires the optional dependency: "
            "python -m pip install -e '.[lilocbench]'"
        ) from exc

    bag_path = bag_path.expanduser().resolve()
    typestore = get_typestore(Stores.ROS1_NOETIC)
    topic_types: dict[str, set[str]] = defaultdict(set)
    topic_counts: Counter[str] = Counter()
    topic_record_times: dict[str, list[float]] = defaultdict(list)
    topic_header_times: dict[str, list[float]] = defaultdict(list)
    topic_lags_ms: dict[str, list[float]] = defaultdict(list)
    topic_frames: dict[str, Counter[str]] = defaultdict(Counter)
    topic_child_frames: dict[str, Counter[str]] = defaultdict(Counter)
    topic_connection_stamps: dict[tuple[int, str], list[float]] = defaultdict(list)
    scans: dict[str, list[dict[str, float]]] = defaultdict(list)
    odometry: list[dict[str, float]] = []
    tf_edges: Counter[tuple[str, str, str]] = Counter()
    tf_lags_ms: list[float] = []
    decoded_messages = 0

    with Reader(bag_path) as reader:
        for connection in reader.connections:
            topic_types[connection.topic].add(connection.msgtype)
            if connection.msgtype not in typestore.types:
                typestore.register(get_types_from_msg(connection.msgdef.data, connection.msgtype))

        for connection, record_ns, raw in reader.messages():
            message = typestore.deserialize_ros1(raw, connection.msgtype)
            decoded_messages += 1
            topic = connection.topic
            record_seconds = record_ns / 1_000_000_000.0
            topic_counts[topic] += 1
            topic_record_times[topic].append(record_seconds)
            topic_connection_stamps[(connection.id, topic)].append(record_seconds)

            if hasattr(message, "header"):
                header = message.header
                header_seconds = header.stamp.sec + header.stamp.nanosec / 1_000_000_000.0
                topic_header_times[topic].append(header_seconds)
                topic_lags_ms[topic].append((record_seconds - header_seconds) * 1000.0)
                topic_frames[topic][header.frame_id] += 1
            else:
                header_seconds = None

            if topic in ("/tf", "/tf_static"):
                for transform in message.transforms:
                    parent = transform.header.frame_id.lstrip("/")
                    child = transform.child_frame_id.lstrip("/")
                    tf_edges[(topic, parent, child)] += 1
                    stamp = transform.header.stamp.sec + transform.header.stamp.nanosec / 1_000_000_000.0
                    if topic == "/tf":
                        tf_lags_ms.append((record_seconds - stamp) * 1000.0)

            if topic == "/dingo_velocity_controller/odom":
                position = message.pose.pose.position
                orientation = message.pose.pose.orientation
                yaw = math.atan2(
                    2.0 * (orientation.w * orientation.z + orientation.x * orientation.y),
                    1.0 - 2.0 * (orientation.y**2 + orientation.z**2),
                )
                odometry.append(
                    {
                        "stamp": header_seconds,
                        "x": position.x,
                        "y": position.y,
                        "yaw": yaw,
                    }
                )
                topic_child_frames[topic][message.child_frame_id] += 1

            if topic in ("/laser_scan_front/scan", "/laser_scan_rear/scan"):
                ranges = np.asarray(message.ranges, dtype=np.float64)
                valid = np.isfinite(ranges) & (ranges >= message.range_min) & (ranges <= message.range_max)
                scans[topic].append(
                    {
                        "beam_count": float(len(ranges)),
                        "valid_beam_count": float(np.count_nonzero(valid)),
                        "valid_range_min_m": float(np.min(ranges[valid])) if np.any(valid) else math.nan,
                        "valid_range_max_m": float(np.max(ranges[valid])) if np.any(valid) else math.nan,
                        "scan_time_s": float(message.scan_time),
                    }
                )

        topic_summary: dict[str, Any] = {}
        for topic in sorted(topic_counts):
            record_times = topic_record_times[topic]
            headers = topic_header_times[topic]
            connection_monotonic = all(
                all(b >= a for a, b in zip(stamps, stamps[1:], strict=False))
                for (connection_id, name), stamps in topic_connection_stamps.items()
                if name == topic
            )
            topic_summary[topic] = {
                "message_count": topic_counts[topic],
                "message_types": sorted(topic_types[topic]),
                "record_time_s": {"first": min(record_times), "last": max(record_times)},
                "header_time_s": {"first": min(headers), "last": max(headers)} if headers else None,
                "header_record_lag_ms": summarize(topic_lags_ms[topic]),
                "frame_ids": dict(sorted(topic_frames[topic].items())),
                "child_frame_ids": dict(sorted(topic_child_frames[topic].items())),
                "record_order_monotonic_per_connection": connection_monotonic,
            }
            if topic in scans:
                for key in ("beam_count", "valid_beam_count", "valid_range_min_m", "valid_range_max_m", "scan_time_s"):
                    topic_summary[topic][key] = summarize([row[key] for row in scans[topic]])

        parents_by_child: dict[str, set[str]] = defaultdict(set)
        frame_names: set[str] = set()
        for (_, parent, child), _count in tf_edges.items():
            parents_by_child[child].add(parent)
            frame_names.update((parent, child))
        multiple_parents = {child: sorted(parents) for child, parents in parents_by_child.items() if len(parents) > 1}
        roots = sorted(frame for frame in frame_names if frame not in parents_by_child)
        tf_edge_summary = [
            {"topic": topic, "parent": parent, "child": child, "transform_messages": count}
            for (topic, parent, child), count in sorted(tf_edges.items())
        ]
        bag_metadata = {
            "path_name": bag_path.name,
            "sha256": hashlib.sha256(bag_path.read_bytes()).hexdigest(),
            "bytes": bag_path.stat().st_size,
            "record_start_ns": reader.start_time,
            "record_end_ns": reader.end_time,
            "record_duration_s": reader.duration / 1_000_000_000.0,
            "message_count": reader.message_count,
            "decoded_message_count": decoded_messages,
            "connection_count": len(reader.connections),
            "topic_count": len(topic_counts),
            "topics": topic_summary,
        }

    sync: dict[str, Any] = {}
    gt_times: list[float] = []
    gt_values: np.ndarray | None = None
    if ground_truth_path is not None:
        gt_values = np.loadtxt(ground_truth_path, dtype=np.float64)
        gt_times = gt_values[:, 0].tolist()
        sync["bag_topics_to_ground_truth_nearest_ms"] = {}
        for topic in sorted(topic_header_times):
            if not topic_header_times[topic]:
                continue
            deltas = nearest_time_deltas_ms(gt_times, topic_header_times[topic])
            sync["bag_topics_to_ground_truth_nearest_ms"][topic] = {
                **(summarize(deltas) or {}),
                "within_25ms_fraction": sum(delta <= 25.0 for delta in deltas) / len(deltas),
            }
        front = topic_header_times.get("/laser_scan_front/scan", [])
        rear = topic_header_times.get("/laser_scan_rear/scan", [])
        odom_times = topic_header_times.get("/dingo_velocity_controller/odom", [])
        sync["front_to_rear_scan_nearest_ms"] = summarize(nearest_time_deltas_ms(front, rear))
        sync["odom_to_ground_truth_nearest_ms"] = summarize(nearest_time_deltas_ms(gt_times, odom_times))

    tf_has_map = any(frame.lower() in ("map", "world") for frame in frame_names)
    odom_to_base = any(parent == "odom" and child == "base_link" for _, parent, child in tf_edges)
    result: dict[str, Any] = {
        "dataset": "LILocBench",
        "sequence": "dynamics_0",
        "evidence_status": "offline ROS1 bag decode and timestamp/TF audit; no ROS graph or sensor playback",
        "source_url": f"{DATASET_PAGE}data/bagfiles_no_cams/dynamics_0.bag",
        "bag": bag_metadata,
        "timestamp_synchronization": sync,
        "tf": {
            "frames": sorted(frame_names),
            "root_frames": roots,
            "unique_parent_per_child": not multiple_parents,
            "multiple_parent_frames": multiple_parents,
            "map_or_world_frame_present": tf_has_map,
            "odom_to_base_link_present": odom_to_base,
            "dynamic_transform_header_record_lag_ms": summarize(tf_lags_ms),
            "edges": tf_edge_summary,
            "interpretation": (
                "Bag includes odom->base_link but no map/world frame or map->odom transform; "
                "do not overlay bag odometry directly on the occupancy map."
            ),
        },
    }
    if ground_truth_path is not None and gt_values is not None:
        result["ground_truth"] = {
            "source_url": f"{DATASET_PAGE}data/gt_poses_public/dynamics_0/gt_poses.txt",
            "sha256": hashlib.sha256(ground_truth_path.read_bytes()).hexdigest(),
            "pose_count": int(len(gt_values)),
            "time_range_s": [float(gt_values[0, 0]), float(gt_values[-1, 0])],
        }
        result["odom_to_ground_truth_fit_diagnostic"] = fit_odom_to_ground_truth_diagnostic(odometry, gt_values)
    return result


def write_csv_artifacts(result: dict[str, Any], output_dir: Path) -> list[str]:
    """Write deterministic topic, TF-edge, and synchronization tables."""
    output_dir.mkdir(parents=True, exist_ok=True)

    def write(name: str, fields: tuple[str, ...], rows: list[dict[str, Any]]) -> str:
        path = output_dir / name
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        return name

    topic_rows = []
    for topic, summary in sorted(result["bag"]["topics"].items()):
        record_time = summary["record_time_s"]
        header_time = summary["header_time_s"] or {}
        lag = summary["header_record_lag_ms"] or {}
        topic_rows.append(
            {
                "topic": topic,
                "message_types": ";".join(summary["message_types"]),
                "message_count": summary["message_count"],
                "record_first_s": record_time["first"],
                "record_last_s": record_time["last"],
                "header_first_s": header_time.get("first"),
                "header_last_s": header_time.get("last"),
                "header_record_lag_median_ms": lag.get("median"),
                "header_record_lag_p95_ms": lag.get("p95"),
                "frame_ids": ";".join(summary["frame_ids"]),
                "child_frame_ids": ";".join(summary["child_frame_ids"]),
            }
        )
    topic_name = write(
        "lilocbench_dynamics_0_ros1_topics.csv",
        (
            "topic", "message_types", "message_count", "record_first_s", "record_last_s",
            "header_first_s", "header_last_s", "header_record_lag_median_ms",
            "header_record_lag_p95_ms", "frame_ids", "child_frame_ids",
        ),
        topic_rows,
    )

    tf_name = write(
        "lilocbench_dynamics_0_tf_edges.csv",
        ("topic", "parent_frame", "child_frame", "transform_messages"),
        [
            {
                "topic": edge["topic"],
                "parent_frame": edge["parent"],
                "child_frame": edge["child"],
                "transform_messages": edge["transform_messages"],
            }
            for edge in result["tf"]["edges"]
        ],
    )

    synchronization = result["timestamp_synchronization"]
    comparisons: dict[str, dict[str, Any]] = {}
    for topic, summary in synchronization.get("bag_topics_to_ground_truth_nearest_ms", {}).items():
        comparisons[f"{topic}_to_gt"] = summary
    for name in ("front_to_rear_scan_nearest_ms", "odom_to_ground_truth_nearest_ms"):
        if name in synchronization and synchronization[name] is not None:
            comparisons[name.removesuffix("_nearest_ms")] = synchronization[name]
    sync_name = write(
        "lilocbench_dynamics_0_sync_metrics.csv",
        ("comparison", "count", "min_ms", "median_ms", "p95_ms", "max_ms", "within_25ms_fraction"),
        [
            {
                "comparison": name,
                "count": summary.get("count"),
                "min_ms": summary.get("min"),
                "median_ms": summary.get("median"),
                "p95_ms": summary.get("p95"),
                "max_ms": summary.get("max"),
                "within_25ms_fraction": summary.get("within_25ms_fraction"),
            }
            for name, summary in sorted(comparisons.items())
        ],
    )
    return [topic_name, tf_name, sync_name]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bag", type=Path, help="LILocBench reduced ROS1 .bag file")
    parser.add_argument("--ground-truth", type=Path, help="optional matching TUM ground-truth pose file")
    parser.add_argument("--output", type=Path, help="write the audit JSON to this path")
    parser.add_argument("--artifact-dir", type=Path, help="write reproducible topic/TF/synchronization CSVs")
    args = parser.parse_args()
    result = analyze_bag(args.bag, args.ground_truth)
    if args.artifact_dir:
        result["csv_artifacts"] = write_csv_artifacts(result, args.artifact_dir.expanduser().resolve())
    encoded = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
