from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYZER = ROOT / "scripts" / "analyze_lilocbench_ground_truth.py"


def test_analyzer_reports_reproducible_xy_metrics_and_input_hash(tmp_path: Path) -> None:
    poses = tmp_path / "poses.txt"
    poses.write_text(
        "0.0 0 0 0 0 0 0 1\n"
        "0.5 3 4 0 0 0 0 1\n"
        "1.0 3 8 0 0 0 0 1\n",
        encoding="utf-8",
    )
    output = tmp_path / "summary.json"

    completed = subprocess.run(
        [sys.executable, str(ANALYZER), str(poses), "--output", str(output)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert completed.stdout == ""
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["samples"] == 3
    assert result["duration_s"] == 1.0
    assert result["sampling_hz_mean"] == 2.0
    assert result["xy_path_length_m"] == 9.0
    assert result["xy_speed_m_s"]["mean"] == 9.0
    assert result["source_sha256"] == hashlib.sha256(poses.read_bytes()).hexdigest()


def test_analyzer_rejects_non_monotonic_timestamps(tmp_path: Path) -> None:
    poses = tmp_path / "invalid.txt"
    poses.write_text(
        "1.0 0 0 0 0 0 0 1\n"
        "0.5 1 0 0 0 0 0 1\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [sys.executable, str(ANALYZER), str(poses)],
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "timestamps must increase strictly" in completed.stderr
