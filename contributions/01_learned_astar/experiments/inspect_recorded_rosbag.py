"""Audit *actual recorded* ROS 1/2 bag messages, without claiming C01 drove the robot.

Uses rosbags (pip install rosbags). Record sensor-topic inventories, per-topic
message counts and time bounds from actual original storage. Do not synthesize
ROS messages and label them recorded. ROS 1 input is not ROS 2 execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for part in iter(lambda: stream.read(1024*1024), b""):
            h.update(part)
    return h.hexdigest()


def inspect_rosbag(path: Path, *, max_messages: int = 0) -> dict:
    from rosbags.highlevel import AnyReader

    if not path.exists():
        raise FileNotFoundError(path)
    sources = [path] if path.is_file() else [path]
    with AnyReader(sources) as reader:
        connections = list(reader.connections)
        types = {c.topic: c.msgtype for c in connections}
        available = sorted(types)
        sensor = [c for c in connections if
                  "LaserScan" in c.msgtype or "Odometry" in c.msgtype or
                  c.topic.endswith("cmd_vel") or "TFMessage" in c.msgtype]
        counts = Counter()
        first = {}
        last = {}
        nan_lasers = Counter()
        samples = 0
        for conn, stamp, raw in reader.messages(connections=sensor):
            counts[conn.topic] += 1
            samples += 1
            timestamp = stamp * 1e-9
            first.setdefault(conn.topic, timestamp)
            last[conn.topic] = timestamp
            # Decode actual recorded message, not just index/header metadata.
            msg = reader.deserialize(raw, conn.msgtype)
            if "LaserScan" in conn.msgtype:
                nan_lasers[conn.topic] += sum(
                    1 for v in msg.ranges if v != v
                )
            if max_messages and samples >= max_messages:
                break
    if not sensor:
        raise ValueError("No LiDAR, odometry, cmd_vel or TF messages found")
    if not counts:
        raise ValueError("ROS bag has no readable recorded sensor messages")
    stats = [
        {
            "topic": topic,
            "type": types[topic],
            "decoded_message_count": counts[topic],
            "first_recorded_time_s": first[topic],
            "last_recorded_time_s": last[topic],
            "observed_duration_s": last[topic] - first[topic],
            "nan_lidar_ranges_observed": nan_lasers[topic],
        }
        for topic in sorted(counts)
    ]
    result = {
        "evidence_type": "previously_recorded_physical_robot_rosbag_offline_inspection",
        "bag_path": str(path),
        "bag_sha256": hash_file(path) if path.is_file() else None,
        "all_topics": available,
        "topic_statistics": stats,
        "decoded_message_count_total": samples,
        "truncated_by_max_messages": bool(max_messages and samples >= max_messages),
        "ros2_live_execution": False,
        "c01_algorithm_executed_on_recording": False,
        "c01_controlled_source_robot": False,
        "physical_robot_validation": False,
        "limitations": [
            "Recorded physical-world sensor data do not show the C01 algorithm controlling the source robot.",
            "The source dynamics_0 bag is ROS 1 .bag; reading it offline is not ROS 2 playback.",
            "The bag alone does not establish world-to-map alignment or independently measured obstacle avoidance.",
        ],
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bag", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-messages", type=int, default=0)
    args = parser.parse_args()
    if args.max_messages < 0:
        parser.error("--max-messages must be non-negative")
    result = inspect_rosbag(args.bag.resolve(), max_messages=args.max_messages)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
