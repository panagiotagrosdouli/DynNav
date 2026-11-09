"""C01 real ROS map evaluation contract tests (fixtures are synthetic only)."""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

FILE = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "eval_real_ros_map.py"
)
spec = importlib.util.spec_from_file_location("c01_real_map_eval", FILE)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_component_separation_and_deterministic_tasks():
    grid = np.zeros((7, 9), dtype=np.uint8)
    grid[:, 4] = 1
    components = module.free_components(grid)
    assert sorted(len(c) for c in components) == [28, 28]
    a = module.sample_tasks(components, count=6, min_distance=3, seed=123)
    b = module.sample_tasks(components, count=6, min_distance=3, seed=123)
    assert a == b
    for s, g in a:
        assert (s[0] < 4) == (g[0] < 4)


def test_start_goal_and_path_validation():
    grid = np.zeros((5, 5), dtype=np.uint8)
    grid[2, 2] = 1
    assert module.validate_path(grid, [(0, 0), (1, 0), (1, 1)], (0, 0), (1, 1))
    assert not module.validate_path(grid, [(0, 0), (2, 0)], (0, 0), (2, 0))
    assert not module.validate_path(grid, [(0, 0), (1, 0), (2, 2)], (0, 0), (2, 2))


def test_missing_model_does_not_fallback(tmp_path):
    yaml_path = write_map(tmp_path)
    with pytest.raises(FileNotFoundError, match="checkpoint"):
        module.evaluate(yaml_path, tmp_path / "out", tmp_path / "missing.pt", 3, 1, 2)


def write_map(folder):
    # White is free, black occupied; map loader flips the image's vertical axis.
    pixels = np.full((12, 12), 255, dtype=np.uint8)
    pixels[6, 5:7] = 0
    Image.fromarray(pixels).save(folder / "map.png")
    path = folder / "map.yaml"
    path.write_text(
        "image: map.png\nresolution: 0.1\norigin: [0.0, 0.0, 0.0]\n"
        "negate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.196\n",
        encoding="utf-8",
    )
    return path


def test_map_end_to_end_baseline(tmp_path):
    path = write_map(tmp_path)
    report = module.evaluate(path, tmp_path / "results", None, 4, 5, 3)
    assert report["evidence_type"] == "real_map_offline_generated_queries"
    assert report["neural_model_loaded"] is False
    assert report["number_tasks"] == 4
    assert set(report["methods"]) == {"astar_manhattan", "dijkstra_h0"}
    assert all(row["suboptimal_task_count"] == 0 for row in report["methods"].values())
    assert (tmp_path / "results" / "trials.csv").is_file()
    assert (tmp_path / "results" / "summary.json").is_file()
